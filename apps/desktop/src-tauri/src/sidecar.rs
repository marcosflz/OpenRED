//! Supervisor del sidecar Python `openred_engine`.
//!
//! - Arranque del proceso (`tokio::process`) en modo dev o release (plan §3.2/§3.3).
//! - Lectura JSONL de stdout: respuestas -> `oneshot` pendientes; eventos -> `engine-event`.
//! - stderr -> `tracing` + evento `engine-log`.
//! - `event ready` con timeout de 10 s y 1 reintento automático con backoff de 1 s.
//! - Al salir: `app.shutdown` (3 s) y kill si no responde.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::Duration;

use serde::Serialize;
use serde_json::{json, Value};
use tauri::{AppHandle, Emitter};
use tokio::io::{AsyncBufReadExt, AsyncRead, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::{mpsc, oneshot, watch};
use tokio::time::{sleep, sleep_until, Instant};

use crate::ipc::{RpcError, ERR_INTERNAL, ERR_NOT_RUNNING};
use crate::paths;

/// Evento con el payload crudo de las notificaciones del motor.
pub const EVENT_ENGINE: &str = "engine-event";
/// Evento de log reenviado desde stderr del motor: `{level, line}`.
pub const EVENT_LOG: &str = "engine-log";
/// Evento de estado del sidecar: `{running, pid, version, error}`.
pub const EVENT_STATUS: &str = "engine-status";
/// Evento por cada petición despachada: `{id, method, phase}` (permite cancelar por `id`).
pub const EVENT_REQUEST: &str = "engine-request";

/// Timeout para recibir `event ready` tras arrancar el proceso.
/// El motor hace warm-up de numpy/scipy/matplotlib antes de anunciar `ready`
/// (evita un deadlock de imports concurrentes), por lo que el primer arranque
/// puede tardar varios segundos.
pub const READY_TIMEOUT: Duration = Duration::from_secs(30);
/// Timeout de las peticiones normales al motor.
pub const REQUEST_TIMEOUT: Duration = Duration::from_secs(300);
/// Gracia para `app.shutdown` antes de matar el proceso.
pub const SHUTDOWN_TIMEOUT: Duration = Duration::from_secs(3);

const RESTART_BACKOFF: Duration = Duration::from_secs(1);
const PROCESS_POLL: Duration = Duration::from_millis(200);
const KILL_WAIT: Duration = Duration::from_secs(2);
const RESTART_READY_TIMEOUT: Duration = Duration::from_secs(30);
/// Uptime mínimo para considerar el proceso "sano" y renovar el presupuesto de reinicio.
const STABLE_UPTIME: Duration = Duration::from_secs(30);

const ENGINE_ARGS: [&str; 5] = ["-s", "-X", "utf8", "-m", "openred_engine"];
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

fn lock<T>(mutex: &Mutex<T>) -> MutexGuard<'_, T> {
    mutex
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

fn truncate(value: &str, max_chars: usize) -> String {
    if value.chars().count() <= max_chars {
        value.to_string()
    } else {
        value.chars().take(max_chars).collect::<String>() + "…"
    }
}

// ---------------------------------------------------------------------------
// Parser JSONL
// ---------------------------------------------------------------------------

/// Mensaje entrante del sidecar por stdout.
#[derive(Debug, Clone, PartialEq)]
pub enum Incoming {
    /// Respuesta a una petición (`{"id":..,"result":..}` o `{"id":..,"error":{..}}`).
    Response {
        id: u64,
        result: Option<Value>,
        error: Option<Value>,
    },
    /// Notificación del motor (`{"method":"event","params":{..}}`).
    Event { params: Value },
}

/// Parser puro de una línea JSONL del sidecar. `None` para líneas vacías,
/// JSON inválido o mensajes que no cumplen el contrato.
pub fn parse_line(line: &str) -> Option<Incoming> {
    let trimmed = line.trim();
    if trimmed.is_empty() {
        return None;
    }
    let value: Value = serde_json::from_str(trimmed).ok()?;
    let object = value.as_object()?;

    if let Some(method) = object.get("method").and_then(Value::as_str) {
        if method == "event" || method.starts_with("event/") {
            let params = object.get("params").cloned().unwrap_or_else(|| json!({}));
            return Some(Incoming::Event { params });
        }
        return None;
    }

    if let Some(id) = object.get("id").and_then(Value::as_u64) {
        if object.contains_key("result") || object.contains_key("error") {
            return Some(Incoming::Response {
                id,
                result: object.get("result").cloned(),
                error: object.get("error").cloned(),
            });
        }
    }

    None
}

/// Convierte el framing de una respuesta en `Result` (error JSON-RPC -> `RpcError`).
pub fn response_result(result: Option<Value>, error: Option<Value>) -> Result<Value, RpcError> {
    if let Some(error) = error {
        return Err(RpcError::from_engine_error(&error));
    }
    match result {
        Some(value) => Ok(value),
        None => Err(RpcError::new(
            ERR_INTERNAL,
            "Respuesta del motor sin 'result' ni 'error'",
        )),
    }
}

/// Nivel aproximado para una línea de stderr del motor (logging de Python o traza suelta).
pub fn detect_log_level(line: &str) -> &'static str {
    let trimmed = line.trim_start();
    if trimmed.starts_with("ERROR")
        || trimmed.starts_with("CRITICAL")
        || trimmed.starts_with("Traceback")
    {
        "error"
    } else if trimmed.starts_with("WARNING") {
        "warn"
    } else if trimmed.starts_with("DEBUG") {
        "debug"
    } else {
        "info"
    }
}

// ---------------------------------------------------------------------------
// Espectro de arranque (testeable)
// ---------------------------------------------------------------------------

/// Programa + argumentos + entorno con el que se lanza el sidecar.
#[derive(Debug, Clone, PartialEq)]
pub struct SpawnSpec {
    pub program: PathBuf,
    pub args: Vec<String>,
    pub cwd: PathBuf,
    pub envs: Vec<(String, String)>,
}

/// Construye el comando de arranque.
///
/// - **Dev**: `dev_python` + `dev_dir` (env `OPENRED_ENGINE_PYTHON`/`OPENRED_ENGINE_DIR`).
/// - **Release**: `<engine_resource_dir>/python/python.exe` con cwd `<engine_resource_dir>`.
pub fn build_spawn_spec(
    data_dir: &Path,
    engine_resource_dir: &Path,
    dev_python: Option<&str>,
    dev_dir: Option<&str>,
    workdir: Option<&str>,
) -> SpawnSpec {
    let (program, cwd, engine_dir) = match (dev_python, dev_dir) {
        (Some(python), Some(dir)) => {
            let dir = PathBuf::from(dir);
            (PathBuf::from(python), dir.clone(), dir)
        }
        _ => {
            let program = if cfg!(windows) {
                engine_resource_dir.join("python").join("python.exe")
            } else {
                engine_resource_dir
                    .join("python")
                    .join("bin")
                    .join("python3")
            };
            (
                program,
                engine_resource_dir.to_path_buf(),
                engine_resource_dir.to_path_buf(),
            )
        }
    };

    let engine_dir_text = engine_dir.to_string_lossy().into_owned();
    let data_dir_text = data_dir.to_string_lossy().into_owned();
    let mpl_dir = data_dir.join("mpl-data").to_string_lossy().into_owned();

    // Release layout: <engine>/python is the runtime and pip installed the wheels into
    // <engine>/python/site-packages (`fetch_python.ps1`), so both must be importable.
    let mut python_paths = vec![engine_dir_text.clone()];
    let site_packages = engine_dir.join("python").join("site-packages");
    if site_packages.is_dir() {
        python_paths.push(site_packages.to_string_lossy().into_owned());
    }
    let python_path = std::env::join_paths(python_paths.iter())
        .map(|value| value.to_string_lossy().into_owned())
        .unwrap_or_else(|_| engine_dir_text.clone());

    let mut envs = vec![
        ("PYTHONNOUSERSITE".to_string(), "1".to_string()),
        ("PYTHONUTF8".to_string(), "1".to_string()),
        ("PYTHONDONTWRITEBYTECODE".to_string(), "1".to_string()),
        ("MPLBACKEND".to_string(), "Agg".to_string()),
        ("MPLCONFIGDIR".to_string(), mpl_dir),
        ("OPENRED_DATA_DIR".to_string(), data_dir_text),
        ("OPENRED_RESOURCE_DIR".to_string(), engine_dir_text),
        ("PYTHONPATH".to_string(), python_path),
    ];
    if let Some(workdir) = workdir.filter(|value| !value.trim().is_empty()) {
        envs.push(("OPENRED_WORKDIR".to_string(), workdir.to_string()));
    }

    SpawnSpec {
        program,
        args: ENGINE_ARGS.iter().map(|arg| arg.to_string()).collect(),
        cwd,
        envs,
    }
}

// ---------------------------------------------------------------------------
// Estado compartido
// ---------------------------------------------------------------------------

/// Estado del sidecar que consumen `engine_status` y los eventos.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct EngineStatus {
    pub running: bool,
    pub pid: Option<u32>,
    pub last_error: Option<String>,
    pub version: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct StatusEvent {
    running: bool,
    pid: Option<u32>,
    version: Option<String>,
    error: Option<String>,
}

#[derive(Debug)]
enum Control {
    Restart,
    Shutdown,
}

#[derive(Debug)]
enum RunEnd {
    Shutdown,
    Restart,
    Died {
        error: Option<String>,
        was_ready: bool,
        uptime: Duration,
    },
}

struct Status {
    running: bool,
    pid: Option<u32>,
    version: Option<String>,
    last_error: Option<String>,
    stdin: Option<mpsc::UnboundedSender<String>>,
}

struct Inner {
    app: AppHandle,
    data_dir: PathBuf,
    engine_resource_dir: PathBuf,
    pending: Mutex<HashMap<u64, oneshot::Sender<Result<Value, RpcError>>>>,
    status: Mutex<Status>,
    next_id: AtomicU64,
    ctl: mpsc::UnboundedSender<Control>,
    ready_tx: watch::Sender<bool>,
    ready_rx: watch::Receiver<bool>,
    shutting_down: AtomicBool,
}

/// Handle clonable al supervisor del sidecar (estado gestionado por Tauri).
#[derive(Clone)]
pub struct Sidecar {
    inner: Arc<Inner>,
}

impl Sidecar {
    /// Construye el estado y lanza el supervisor (que arranca el proceso de inmediato).
    pub fn new(app: &AppHandle) -> Self {
        let data_dir = paths::data_dir(app);
        let engine_resource_dir = paths::engine_resource_dir(app);
        let (ctl_tx, ctl_rx) = mpsc::unbounded_channel();
        let (ready_tx, ready_rx) = watch::channel(false);

        let inner = Arc::new(Inner {
            app: app.clone(),
            data_dir,
            engine_resource_dir,
            pending: Mutex::new(HashMap::new()),
            status: Mutex::new(Status {
                running: false,
                pid: None,
                version: None,
                last_error: None,
                stdin: None,
            }),
            next_id: AtomicU64::new(0),
            ctl: ctl_tx,
            ready_tx,
            ready_rx,
            shutting_down: AtomicBool::new(false),
        });

        tauri::async_runtime::spawn(supervisor(inner.clone(), ctl_rx));

        Self { inner }
    }

    /// Envía una petición y espera la respuesta (timeout de `REQUEST_TIMEOUT`).
    ///
    /// No retiene ningún lock mientras espera, por lo que `request.cancel` puede
    /// despacharse con otra petición en vuelo.
    pub async fn request(&self, method: String, params: Value) -> Result<Value, RpcError> {
        let id = self.inner.next_id.fetch_add(1, Ordering::SeqCst) + 1;

        {
            let status = lock(&self.inner.status);
            if !status.running || status.stdin.is_none() {
                return Err(RpcError::not_running(status.last_error.clone()));
            }
        }

        let line = serde_json::to_string(&json!({
            "id": id,
            "method": method.clone(),
            "params": params,
        }))
        .map_err(|err| RpcError::internal(format!("No se pudo codificar la petición: {err}")))?;

        let (tx, rx) = oneshot::channel();
        lock(&self.inner.pending).insert(id, tx);

        let _ = self.inner.app.emit(
            EVENT_REQUEST,
            json!({ "id": id, "method": method, "phase": "start" }),
        );

        if let Err(err) = self.inner.send_line(line) {
            lock(&self.inner.pending).remove(&id);
            return Err(err);
        }

        match tokio::time::timeout(REQUEST_TIMEOUT, rx).await {
            Ok(Ok(result)) => result,
            Ok(Err(_)) => Err(RpcError::not_running(self.inner.last_error())),
            Err(_) => {
                lock(&self.inner.pending).remove(&id);
                Err(RpcError::timeout(&method))
            }
        }
    }

    /// Snapshot del estado para el comando `engine_status`.
    pub fn status(&self) -> EngineStatus {
        self.inner.status_snapshot()
    }

    /// Reinicia el proceso y espera a `ready` (timeout 15 s).
    pub async fn restart(&self) -> Result<(), RpcError> {
        self.inner.ready_tx.send(false).ok();
        self.inner
            .ctl
            .send(Control::Restart)
            .map_err(|_| RpcError::internal("El supervisor del motor no está activo"))?;

        let mut ready_rx = self.inner.ready_rx.clone();
        let wait = async {
            loop {
                if *ready_rx.borrow_and_update() {
                    return true;
                }
                if ready_rx.changed().await.is_err() {
                    return false;
                }
            }
        };

        match tokio::time::timeout(RESTART_READY_TIMEOUT, wait).await {
            Ok(true) => Ok(()),
            Ok(false) => Err(RpcError::not_running(self.inner.last_error())),
            Err(_) => Err(RpcError::internal(format!(
                "El motor no respondió 'ready' en {} s tras reiniciar",
                RESTART_READY_TIMEOUT.as_secs()
            ))),
        }
    }

    /// Apagado ordenado: `app.shutdown` (gracia) y kill si no responde.
    pub async fn shutdown(&self, grace: Duration) {
        if self.inner.shutting_down.swap(true, Ordering::SeqCst) {
            return;
        }
        if self.inner.is_running() {
            let _ =
                tokio::time::timeout(grace, self.request("app.shutdown".into(), json!({}))).await;
        }
        let _ = self.inner.ctl.send(Control::Shutdown);

        let deadline = Instant::now() + KILL_WAIT;
        while self.inner.is_running() && Instant::now() < deadline {
            sleep(Duration::from_millis(50)).await;
        }
    }
}

impl Inner {
    fn is_running(&self) -> bool {
        lock(&self.status).running
    }

    fn last_error(&self) -> Option<String> {
        lock(&self.status).last_error.clone()
    }

    fn status_snapshot(&self) -> EngineStatus {
        let status = lock(&self.status);
        EngineStatus {
            running: status.running,
            pid: status.pid,
            last_error: status.last_error.clone(),
            version: status.version.clone(),
        }
    }

    fn emit_status(&self) {
        let event = {
            let status = lock(&self.status);
            StatusEvent {
                running: status.running,
                pid: status.pid,
                version: status.version.clone(),
                error: status.last_error.clone(),
            }
        };
        let _ = self.app.emit(EVENT_STATUS, event);
    }

    fn mark_spawned(&self, pid: u32, stdin: mpsc::UnboundedSender<String>) {
        {
            let mut status = lock(&self.status);
            status.running = true;
            status.pid = Some(pid);
            status.version = None;
            status.last_error = None;
            status.stdin = Some(stdin);
        }
        self.emit_status();
    }

    fn mark_stopped(&self, error: Option<String>) {
        {
            let mut status = lock(&self.status);
            status.running = false;
            status.pid = None;
            status.stdin = None;
            if error.is_some() {
                status.last_error = error;
            }
        }
        self.ready_tx.send(false).ok();
        let last_error = self.last_error();
        self.fail_pending(RpcError::not_running(last_error));
        self.emit_status();
    }

    fn fail_pending(&self, error: RpcError) {
        let pending: Vec<_> = {
            let mut map = lock(&self.pending);
            map.drain().collect()
        };
        for (_, sender) in pending {
            let _ = sender.send(Err(error.clone()));
        }
    }

    fn send_line(&self, line: String) -> Result<(), RpcError> {
        let status = lock(&self.status);
        match status.stdin.as_ref() {
            Some(sender) => sender
                .send(line)
                .map_err(|_| RpcError::not_running(status.last_error.clone())),
            None => Err(RpcError::not_running(status.last_error.clone())),
        }
    }

    fn handle_line(&self, line: &str) {
        match parse_line(line) {
            Some(Incoming::Response { id, result, error }) => {
                let response = response_result(result, error);
                match lock(&self.pending).remove(&id) {
                    Some(sender) => {
                        let _ = sender.send(response);
                    }
                    None => {
                        tracing::debug!(target: "engine", id, "respuesta sin petición pendiente")
                    }
                }
            }
            Some(Incoming::Event { params }) => self.handle_event(params),
            None => {
                let line = truncate(line, 500);
                tracing::warn!(target: "engine", %line, "línea no parseable del sidecar");
            }
        }
    }

    fn handle_event(&self, params: Value) {
        let name = params
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();

        match name.as_str() {
            "ready" => {
                let version = params
                    .get("version")
                    .and_then(Value::as_str)
                    .map(str::to_string);
                let pid = params
                    .get("pid")
                    .and_then(Value::as_u64)
                    .map(|value| value as u32);
                {
                    let mut status = lock(&self.status);
                    status.running = true;
                    if pid.is_some() {
                        status.pid = pid;
                    }
                    status.version = version;
                    status.last_error = None;
                }
                self.ready_tx.send(true).ok();
                self.emit_status();
                tracing::info!(target: "engine", pid = ?pid, "sidecar listo");
            }
            "exiting" => {
                self.ready_tx.send(false).ok();
            }
            _ => {}
        }

        // Requisito de contrato: toda notificación se reenvía al webview tal cual.
        let _ = self.app.emit(EVENT_ENGINE, params);
    }

    fn handle_stderr_line(&self, line: &str) {
        let level = detect_log_level(line);
        match level {
            "error" => tracing::error!(target: "engine", "{line}"),
            "warn" => tracing::warn!(target: "engine", "{line}"),
            "debug" => tracing::debug!(target: "engine", "{line}"),
            _ => tracing::info!(target: "engine", "{line}"),
        }
        let _ = self
            .app
            .emit(EVENT_LOG, json!({ "level": level, "line": line }));
    }
}

// ---------------------------------------------------------------------------
// Proceso y tareas de E/S
// ---------------------------------------------------------------------------

fn spawn_child(spec: &SpawnSpec) -> std::io::Result<Child> {
    let mut command = Command::new(&spec.program);
    command
        .args(&spec.args)
        .current_dir(&spec.cwd)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);
    for (key, value) in &spec.envs {
        command.env(key, value);
    }
    #[cfg(windows)]
    command.creation_flags(CREATE_NO_WINDOW);
    command.spawn()
}

fn spawn_writer(inner: Arc<Inner>, mut stdin: ChildStdin, mut rx: mpsc::UnboundedReceiver<String>) {
    tauri::async_runtime::spawn(async move {
        while let Some(line) = rx.recv().await {
            let mut bytes = line.into_bytes();
            bytes.push(b'\n');
            if let Err(err) = stdin.write_all(&bytes).await {
                tracing::error!(target: "engine", "escritura a stdin del motor falló: {err}");
                inner.fail_pending(RpcError::new(
                    ERR_NOT_RUNNING,
                    "No se pudo escribir en el stdin del motor",
                ));
                break;
            }
            if let Err(err) = stdin.flush().await {
                tracing::error!(target: "engine", "flush de stdin del motor falló: {err}");
                break;
            }
        }
        let _ = stdin.shutdown().await;
    });
}

fn spawn_reader<R>(inner: Arc<Inner>, stream: R, is_stderr: bool)
where
    R: AsyncRead + Unpin + Send + 'static,
{
    tauri::async_runtime::spawn(async move {
        let mut lines = BufReader::new(stream).lines();
        loop {
            match lines.next_line().await {
                Ok(Some(line)) => {
                    if is_stderr {
                        inner.handle_stderr_line(&line);
                    } else {
                        inner.handle_line(&line);
                    }
                }
                Ok(None) => break,
                Err(err) => {
                    tracing::warn!(target: "engine", "lectura de stdout/stderr falló: {err}");
                    break;
                }
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Supervisor
// ---------------------------------------------------------------------------

async fn run_once(inner: &Arc<Inner>, ctl: &mut mpsc::UnboundedReceiver<Control>) -> RunEnd {
    let dev_python = std::env::var("OPENRED_ENGINE_PYTHON").ok();
    let dev_dir = std::env::var("OPENRED_ENGINE_DIR").ok();
    let workdir = paths::saved_workdir(&inner.app);
    let spec = build_spawn_spec(
        &inner.data_dir,
        &inner.engine_resource_dir,
        dev_python.as_deref(),
        dev_dir.as_deref(),
        workdir.as_deref(),
    );

    inner.ready_tx.send(false).ok();
    tracing::info!(
        target: "engine",
        program = %spec.program.display(),
        cwd = %spec.cwd.display(),
        "arrancando sidecar"
    );

    let mut child = match spawn_child(&spec) {
        Ok(child) => child,
        Err(err) => {
            return RunEnd::Died {
                error: Some(format!(
                    "No se pudo arrancar el motor ({}): {err}",
                    spec.program.display()
                )),
                was_ready: false,
                uptime: Duration::ZERO,
            };
        }
    };

    let pid = child.id().unwrap_or_default();
    let stdin = child.stdin.take();
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    let (stdin_tx, stdin_rx) = mpsc::unbounded_channel();
    inner.mark_spawned(pid, stdin_tx);

    if let Some(stdin) = stdin {
        spawn_writer(inner.clone(), stdin, stdin_rx);
    }
    if let Some(stdout) = stdout {
        spawn_reader(inner.clone(), stdout, false);
    }
    if let Some(stderr) = stderr {
        spawn_reader(inner.clone(), stderr, true);
    }

    // 1) Esperar `event ready` (timeout 10 s).
    let mut ready_rx = inner.ready_rx.clone();
    let mut was_ready = false;
    let deadline = Instant::now() + READY_TIMEOUT;
    loop {
        if *ready_rx.borrow() {
            was_ready = true;
            break;
        }
        tokio::select! {
            _ = sleep_until(deadline) => break,
            changed = ready_rx.changed() => {
                if changed.is_err() {
                    break;
                }
            }
            control = ctl.recv() => {
                let _ = child.kill().await;
                return match control {
                    Some(Control::Restart) => RunEnd::Restart,
                    Some(Control::Shutdown) | None => RunEnd::Shutdown,
                };
            }
            _ = sleep(PROCESS_POLL) => {
                if let Ok(Some(status)) = child.try_wait() {
                    return RunEnd::Died {
                        error: Some(format!("El motor terminó durante el arranque ({status})")),
                        was_ready: false,
                        uptime: Duration::ZERO,
                    };
                }
            }
        }
    }

    if !was_ready {
        let _ = child.kill().await;
        return RunEnd::Died {
            error: Some(format!(
                "El motor no envió 'ready' en {} s",
                READY_TIMEOUT.as_secs()
            )),
            was_ready: false,
            uptime: Duration::ZERO,
        };
    }

    // 2) Proceso en marcha: esperar fin del proceso o comandos de control.
    let ready_at = Instant::now();
    loop {
        tokio::select! {
            control = ctl.recv() => {
                let _ = child.kill().await;
                return match control {
                    Some(Control::Restart) => RunEnd::Restart,
                    Some(Control::Shutdown) | None => RunEnd::Shutdown,
                };
            }
            _ = sleep(PROCESS_POLL) => {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        return RunEnd::Died {
                            error: Some(format!("El proceso del motor terminó ({status})")),
                            was_ready: true,
                            uptime: ready_at.elapsed(),
                        };
                    }
                    Ok(None) => {}
                    Err(err) => {
                        return RunEnd::Died {
                            error: Some(format!("No se pudo consultar el proceso del motor: {err}")),
                            was_ready: true,
                            uptime: ready_at.elapsed(),
                        };
                    }
                }
            }
        }
    }
}

/// Bucle de vida del sidecar: arranque, 1 reintento automático con backoff y parada.
async fn supervisor(inner: Arc<Inner>, mut ctl: mpsc::UnboundedReceiver<Control>) {
    // Presupuesto de reinicios automáticos: 1 por "vida" del proceso.
    let mut budget: u32 = 1;

    loop {
        match run_once(&inner, &mut ctl).await {
            RunEnd::Shutdown => {
                inner.mark_stopped(None);
                tracing::info!(target: "engine", "sidecar detenido");
                return;
            }
            RunEnd::Restart => {
                inner.mark_stopped(None);
                budget = 1;
            }
            RunEnd::Died {
                error,
                was_ready,
                uptime,
            } => {
                tracing::warn!(
                    target: "engine",
                    "sidecar caído: {}",
                    error.as_deref().unwrap_or("sin detalle")
                );
                inner.mark_stopped(error);
                if was_ready && uptime >= STABLE_UPTIME {
                    // El proceso estuvo sano: se renueva un reinicio automático.
                    budget = 1;
                }

                if budget == 0 {
                    // Sin presupuesto: esperar un `engine_restart` manual (o la salida).
                    match ctl.recv().await {
                        Some(Control::Restart) => budget = 1,
                        _ => return,
                    }
                } else {
                    budget -= 1;
                    tokio::select! {
                        _ = sleep(RESTART_BACKOFF) => {}
                        control = ctl.recv() => match control {
                            Some(Control::Restart) => budget = 1,
                            _ => return,
                        },
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn dev_spec() -> SpawnSpec {
        build_spawn_spec(
            Path::new("C:/data/OpenRED"),
            Path::new("C:/install/engine"),
            Some("C:/dev/python.exe"),
            Some("C:/repo/engine"),
            Some("C:/work"),
        )
    }

    #[test]
    fn parse_line_ignores_empty_and_invalid() {
        assert_eq!(parse_line(""), None);
        assert_eq!(parse_line("   "), None);
        assert_eq!(parse_line("\t\n"), None);
        assert_eq!(parse_line("no soy json"), None);
        assert_eq!(parse_line("{incompleto"), None);
        assert_eq!(parse_line("[1,2,3]"), None);
        assert_eq!(parse_line("42"), None);
        assert_eq!(parse_line(r#"{"foo":"bar"}"#), None);
        assert_eq!(parse_line(r#"{"id":1}"#), None);
        assert_eq!(parse_line(r#"{"method":"desconocido","params":{}}"#), None);
    }

    #[test]
    fn parse_line_response_ok() {
        let parsed = parse_line(r#"{"id":12,"result":{"ok":true,"total":3}}"#).unwrap();
        match parsed {
            Incoming::Response { id, result, error } => {
                assert_eq!(id, 12);
                assert_eq!(result.unwrap()["total"], 3);
                assert_eq!(error, None);
            }
            other => panic!("esperaba Response, llegó {other:?}"),
        }
    }

    #[test]
    fn parse_line_response_error() {
        let line = r#"{"id":3,"error":{"code":1004,"message":"Ya existe","detail":null}}"#;
        match parse_line(line).unwrap() {
            Incoming::Response { id, result, error } => {
                assert_eq!(id, 3);
                assert_eq!(result, None);
                assert_eq!(error.unwrap()["code"], 1004);
            }
            other => panic!("esperaba Response, llegó {other:?}"),
        }
    }

    #[test]
    fn parse_line_result_null_is_valid() {
        match parse_line(r#"{"id":9,"result":null}"#).unwrap() {
            Incoming::Response { result, .. } => assert_eq!(result, Some(Value::Null)),
            other => panic!("esperaba Response, llegó {other:?}"),
        }
    }

    #[test]
    fn parse_line_event() {
        let parsed = parse_line(
            r#"{"method":"event","params":{"name":"ready","version":"0.2.0","pid":42}}"#,
        )
        .unwrap();
        match parsed {
            Incoming::Event { params } => {
                assert_eq!(params["name"], "ready");
                assert_eq!(params["pid"], 42);
            }
            other => panic!("esperaba Event, llegó {other:?}"),
        }
    }

    #[test]
    fn parse_line_event_slash_form() {
        let parsed =
            parse_line(r#"{"method":"event/progress","params":{"job":"engine","value":0.5}}"#)
                .unwrap();
        match parsed {
            Incoming::Event { params } => assert_eq!(params["value"], 0.5),
            other => panic!("esperaba Event, llegó {other:?}"),
        }
    }

    #[test]
    fn response_result_maps_error() {
        let err = response_result(
            None,
            Some(json!({"code": 1005, "message": "cancelado", "detail": {"x": 1}})),
        )
        .unwrap_err();
        assert_eq!(err.code, 1005);
        assert_eq!(err.message, "cancelado");
        assert_eq!(err.detail.unwrap()["x"], 1);
    }

    #[test]
    fn response_result_maps_missing_frames() {
        let err = response_result(None, None).unwrap_err();
        assert_eq!(err.code, ERR_INTERNAL);
        let value = response_result(Some(json!({"ok": true})), None).unwrap();
        assert_eq!(value["ok"], true);
    }

    #[test]
    fn detect_log_level_prefixes() {
        assert_eq!(detect_log_level("ERROR:root:falló"), "error");
        assert_eq!(
            detect_log_level("Traceback (most recent call last):"),
            "error"
        );
        assert_eq!(detect_log_level("WARNING:matplotlib:aviso"), "warn");
        assert_eq!(detect_log_level("DEBUG:x:detalle"), "debug");
        assert_eq!(detect_log_level("INFO:engine:listo"), "info");
        assert_eq!(detect_log_level("línea suelta"), "info");
    }

    #[test]
    fn spawn_spec_dev_uses_env_python_and_dir() {
        let spec = dev_spec();
        assert_eq!(spec.program, PathBuf::from("C:/dev/python.exe"));
        assert_eq!(spec.cwd, PathBuf::from("C:/repo/engine"));
        assert_eq!(spec.args, vec!["-s", "-X", "utf8", "-m", "openred_engine"]);
        let envs: HashMap<_, _> = spec.envs.iter().cloned().collect();
        assert_eq!(envs["PYTHONPATH"], "C:/repo/engine");
        assert_eq!(envs["OPENRED_RESOURCE_DIR"], "C:/repo/engine");
        assert_eq!(envs["OPENRED_DATA_DIR"], "C:/data/OpenRED");
        assert_eq!(envs["OPENRED_WORKDIR"], "C:/work");
        assert_eq!(envs["PYTHONNOUSERSITE"], "1");
        assert_eq!(envs["PYTHONUTF8"], "1");
        assert_eq!(envs["PYTHONDONTWRITEBYTECODE"], "1");
        assert_eq!(envs["MPLBACKEND"], "Agg");
        assert!(envs["MPLCONFIGDIR"].ends_with("mpl-data"));
    }

    #[test]
    fn spawn_spec_release_uses_bundled_python() {
        let spec = build_spawn_spec(
            Path::new("C:/data/OpenRED"),
            Path::new("C:/install/engine"),
            None,
            None,
            None,
        );
        let expected_python = if cfg!(windows) {
            PathBuf::from("C:/install/engine/python/python.exe")
        } else {
            PathBuf::from("C:/install/engine/python/bin/python3")
        };
        assert_eq!(spec.program, expected_python);
        assert_eq!(spec.cwd, PathBuf::from("C:/install/engine"));
        let envs: HashMap<_, _> = spec.envs.iter().cloned().collect();
        assert_eq!(envs["PYTHONPATH"], "C:/install/engine");
        assert!(!envs.contains_key("OPENRED_WORKDIR"));
    }

    #[test]
    fn spawn_spec_ignores_incomplete_dev_env() {
        let spec = build_spawn_spec(
            Path::new("C:/data/OpenRED"),
            Path::new("C:/install/engine"),
            Some("C:/dev/python.exe"),
            None,
            None,
        );
        assert_eq!(
            spec.program,
            if cfg!(windows) {
                PathBuf::from("C:/install/engine/python/python.exe")
            } else {
                PathBuf::from("C:/install/engine/python/bin/python3")
            }
        );
    }

    #[test]
    fn spawn_spec_workdir_blank_is_ignored() {
        let spec = build_spawn_spec(
            Path::new("C:/data"),
            Path::new("C:/engine"),
            Some("py"),
            Some("dir"),
            Some("   "),
        );
        let envs: HashMap<_, _> = spec.envs.iter().cloned().collect();
        assert!(!envs.contains_key("OPENRED_WORKDIR"));
    }
}
