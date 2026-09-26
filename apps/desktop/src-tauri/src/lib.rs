//! Shell Tauri 2 de OpenRED: ventana, plugins, supervisor del sidecar Python y
//! router JSON-RPC (ver `PLAN_MIGRACION_ESCRITORIO.md` §2.2).

mod commands;
mod ipc;
mod logging;
mod paths;
mod sidecar;

use tauri::{Manager, RunEvent};
use tauri_plugin_single_instance::init as single_instance;

use sidecar::Sidecar;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // El plugin single-instance debe registrarse antes que el resto.
        .plugin(single_instance(|app, _argv, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            commands::engine_request,
            commands::engine_status,
            commands::engine_restart,
            commands::pick_workdir,
            commands::pick_file,
            commands::pick_save_file,
            commands::open_logs_folder,
            commands::app_info,
            commands::save_workdir,
        ])
        .setup(|app| {
            let data_dir = paths::ensure_dirs(app.handle())?;
            match logging::init(&data_dir) {
                Ok(guard) => {
                    app.manage(guard);
                }
                Err(err) => eprintln!("No se pudo inicializar el logging en fichero: {err}"),
            }
            app.manage(Sidecar::new(app.handle()));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::ExitRequested { .. } = event {
                let sidecar = app.state::<Sidecar>().inner().clone();
                tauri::async_runtime::block_on(sidecar.shutdown(sidecar::SHUTDOWN_TIMEOUT));
            }
        });
}
