//! Logging del shell: fichero rotado diariamente en `<data>/logs/openred.log`
//! (no bloqueante) + stderr en builds de debug. Respeta `RUST_LOG`.

use std::path::Path;

use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

/// Mantiene vivo el hilo del writer no bloqueante de `tracing-appender`.
/// Debe conservarse durante toda la vida de la app (se registra como estado gestionado).
pub struct LogGuard(#[allow(dead_code)] std::sync::Mutex<Option<WorkerGuard>>);

impl LogGuard {
    pub fn new(guard: WorkerGuard) -> Self {
        Self(std::sync::Mutex::new(Some(guard)))
    }
}

/// Inicializa el subscriber global. Devuelve el guard que mantiene el fichero abierto.
pub fn init(data_dir: &Path) -> std::io::Result<LogGuard> {
    let logs = data_dir.join("logs");
    std::fs::create_dir_all(&logs)?;

    let file_appender = tracing_appender::rolling::daily(&logs, "openred.log");
    let (file_writer, guard) = tracing_appender::non_blocking(file_appender);

    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    let file_layer = fmt::layer()
        .with_writer(file_writer)
        .with_ansi(false)
        .with_target(true)
        .with_level(true);

    let registry = tracing_subscriber::registry().with(filter).with(file_layer);

    #[cfg(debug_assertions)]
    let registry = registry.with(fmt::layer().with_writer(std::io::stderr).with_target(true));

    registry.init();

    Ok(LogGuard::new(guard))
}
