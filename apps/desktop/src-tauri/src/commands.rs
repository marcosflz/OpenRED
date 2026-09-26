//! Comandos Tauri expuestos al webview.

use serde_json::{json, Value};
use tauri::{AppHandle, Manager};
use tauri_plugin_dialog::{DialogExt, FilePath};
use tauri_plugin_opener::OpenerExt;

use crate::ipc::{self, RpcError};
use crate::paths;
use crate::sidecar::{EngineStatus, Sidecar};

/// Reenvía una petición al sidecar `openred_engine`.
#[tauri::command]
pub async fn engine_request(
    app: AppHandle,
    method: String,
    params: Option<Value>,
) -> Result<Value, RpcError> {
    ipc::request(&app, method, params.unwrap_or_else(|| json!({}))).await
}

/// Estado actual del sidecar.
#[tauri::command]
pub async fn engine_status(app: AppHandle) -> EngineStatus {
    app.state::<Sidecar>().inner().status()
}

/// Reinicia el sidecar y espera a que vuelva a estar listo.
#[tauri::command]
pub async fn engine_restart(app: AppHandle) -> Result<(), RpcError> {
    app.state::<Sidecar>().inner().restart().await
}

/// Diálogo de selección de carpeta de trabajo.
#[tauri::command]
pub async fn pick_workdir(app: AppHandle) -> Option<String> {
    let (sender, receiver) = tokio::sync::oneshot::channel();
    app.dialog()
        .file()
        .set_title("Selecciona el directorio de trabajo")
        .pick_folder(move |path| {
            let _ = sender.send(path);
        });
    receiver.await.ok().flatten().map(file_path_to_string)
}

/// Filtro de fichero enviado desde la UI: o una extensión suelta (`"json"`) o el
/// objeto `{name, extensions}` de `src/api/types.ts` (`FileFilter`).
#[derive(serde::Deserialize)]
#[serde(untagged)]
pub enum FileFilterArg {
    Extension(String),
    Filter {
        #[serde(rename = "name", default)]
        _name: Option<String>,
        #[serde(default)]
        extensions: Vec<String>,
    },
}

impl FileFilterArg {
    fn into_extensions(self) -> Vec<String> {
        match self {
            FileFilterArg::Extension(extension) => vec![extension],
            FileFilterArg::Filter { extensions, .. } => extensions,
        }
    }
}

/// Diálogo de selección de fichero. `filters` son extensiones (p. ej. `["json"]`)
/// o filtros `{name, extensions}`.
#[tauri::command]
pub async fn pick_file(app: AppHandle, filters: Option<Vec<FileFilterArg>>) -> Option<String> {
    let (sender, receiver) = tokio::sync::oneshot::channel();
    let mut dialog = app.dialog().file().set_title("Selecciona un fichero");
    let extensions: Vec<String> = filters
        .unwrap_or_default()
        .into_iter()
        .flat_map(FileFilterArg::into_extensions)
        .collect();
    if !extensions.is_empty() {
        let refs: Vec<&str> = extensions.iter().map(String::as_str).collect();
        dialog = dialog.add_filter("Archivos", &refs);
    }
    dialog.pick_file(move |path| {
        let _ = sender.send(path);
    });
    receiver.await.ok().flatten().map(file_path_to_string)
}

/// Diálogo "guardar como", con nombre por defecto opcional.
#[tauri::command]
pub async fn pick_save_file(app: AppHandle, default_name: Option<String>) -> Option<String> {
    let (sender, receiver) = tokio::sync::oneshot::channel();
    let mut dialog = app.dialog().file().set_title("Guardar como");
    if let Some(name) = default_name.filter(|value| !value.is_empty()) {
        dialog = dialog.set_file_name(name);
    }
    dialog.save_file(move |path| {
        let _ = sender.send(path);
    });
    receiver.await.ok().flatten().map(file_path_to_string)
}

/// Abre la carpeta de logs (`<data>/logs`) en el explorador del sistema.
#[tauri::command]
pub async fn open_logs_folder(app: AppHandle) -> Result<(), String> {
    let logs = paths::data_dir(&app).join("logs");
    std::fs::create_dir_all(&logs).map_err(|err| err.to_string())?;
    app.opener()
        .open_path(logs.to_string_lossy().into_owned(), None::<&str>)
        .map_err(|err| err.to_string())
}

/// Información de la app para diagnóstico.
#[tauri::command]
pub fn app_info(app: AppHandle) -> Value {
    let data_dir = paths::data_dir(&app);
    let resource_dir = app
        .path()
        .resource_dir()
        .unwrap_or_else(|_| std::path::PathBuf::new());
    json!({
        "version": app.package_info().version.to_string(),
        "dataDir": data_dir.to_string_lossy(),
        "resourceDir": resource_dir.to_string_lossy(),
        "platform": std::env::consts::OS,
    })
}

/// Persiste el directorio de trabajo elegido en `<data>/config/app.json`.
#[tauri::command]
pub async fn save_workdir(app: AppHandle, path: String) -> Result<(), String> {
    let mut config = paths::read_app_config(&app);
    if !config.is_object() {
        config = json!({});
    }
    config["workdir"] = json!(path);
    paths::write_app_config(&app, &config).map_err(|err| err.to_string())
}

fn file_path_to_string(path: FilePath) -> String {
    path.to_string()
}
