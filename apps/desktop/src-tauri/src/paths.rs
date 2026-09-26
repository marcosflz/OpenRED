//! Rutas compartidas del shell: datos mutables del usuario, recursos del motor y
//! configuración de la aplicación (`config/app.json`).
//!
//! Los datos mutables viven fuera de la carpeta de instalación (plan §2.1 D10):
//! `%APPDATA%\OpenRED` en Windows, `~/Library/Application Support/OpenRED` en macOS y
//! `~/.local/share/OpenRED` en Linux.

use std::fs;
use std::io;
use std::path::PathBuf;

use serde_json::{json, Value};
use tauri::{AppHandle, Manager};

/// Directorio de datos mutables de la aplicación (`<base>/OpenRED`).
pub fn data_dir(app: &AppHandle) -> PathBuf {
    let base = app
        .path()
        .data_dir()
        .or_else(|_| app.path().app_data_dir())
        .unwrap_or_else(|_| std::env::temp_dir());
    base.join("OpenRED")
}

/// Raíz de recursos Python del bundle (`<resource_dir>/engine`, ver plan §3.2).
pub fn engine_resource_dir(app: &AppHandle) -> PathBuf {
    app.path()
        .resource_dir()
        .map(|dir| dir.join("engine"))
        .unwrap_or_else(|_| PathBuf::from("engine"))
}

/// Ruta del fichero de configuración del shell (`<data>/config/app.json`).
pub fn app_config_path(app: &AppHandle) -> PathBuf {
    data_dir(app).join("config").join("app.json")
}

/// Crea la estructura de directorios de datos (datos, config, logs, mpl-data).
pub fn ensure_dirs(app: &AppHandle) -> io::Result<PathBuf> {
    let data = data_dir(app);
    fs::create_dir_all(data.join("config"))?;
    fs::create_dir_all(data.join("logs"))?;
    fs::create_dir_all(data.join("mpl-data"))?;
    Ok(data)
}

/// Lee `config/app.json`. Devuelve `{}` si no existe o está corrupto.
pub fn read_app_config(app: &AppHandle) -> Value {
    let path = app_config_path(app);
    match fs::read_to_string(&path) {
        Ok(text) => serde_json::from_str(&text).unwrap_or_else(|err| {
            tracing::warn!(target: "shell", path = %path.display(), "config/app.json inválido: {err}");
            json!({})
        }),
        Err(_) => json!({}),
    }
}

/// Escritura atómica (tmp + rename) de `config/app.json`.
pub fn write_app_config(app: &AppHandle, value: &Value) -> io::Result<()> {
    let path = app_config_path(app);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let tmp = path.with_extension("json.tmp");
    fs::write(&tmp, serde_json::to_vec_pretty(value)?)?;
    // `fs::rename` en Windows falla si el destino existe: se elimina antes.
    if path.exists() {
        fs::remove_file(&path)?;
    }
    fs::rename(&tmp, &path)
}

/// `workdir` guardado en `config/app.json`, si lo hay.
pub fn saved_workdir(app: &AppHandle) -> Option<String> {
    read_app_config(app)
        .get("workdir")
        .and_then(Value::as_str)
        .map(str::to_string)
        .filter(|value| !value.trim().is_empty())
}
