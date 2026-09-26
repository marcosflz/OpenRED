# Shell Tauri de OpenRED (`apps/desktop/src-tauri`)

Shell nativo del escritorio (Tauri 2 + Rust). Se encarga de:

- **Ventana/webview** (1280×800, mínimo 1024×700), icono, instancia única y updater.
- **Supervisor del sidecar Python** `openred_engine`: arranque, reinicio con backoff, parada ordenada.
- **Router JSON-RPC** por stdio (JSONL) según `contracts/methods.md` (§1): peticiones a Python y
  eventos Python → webview.
- **Logging** `tracing` a `<datos>/logs/openred.log` (rotación diaria) + stderr en debug.
- **Comandos** de diálogos, rutas, info de la app y persistencia de `workdir`.

El frontend React vive en `apps/desktop/src` y **no** forma parte de este crate.

## Estructura

| Fichero | Contenido |
|---|---|
| `src/lib.rs` | Builder Tauri, plugins, comandos, `RunEvent::ExitRequested` → `app.shutdown` |
| `src/main.rs` | Entry point (`openred_desktop_lib::run()`) |
| `src/sidecar.rs` | Spawn/lectura/escritura del proceso Python, parser JSONL, reintentos |
| `src/ipc.rs` | `RpcError`, framing de respuestas y punto de entrada del router |
| `src/commands.rs` | `#[tauri::command]` expuestos al webview |
| `src/logging.rs` | `tracing-subscriber` + `tracing-appender` (rolling daily) |
| `src/paths.rs` | `<datos>`, `<recursos>/engine`, `config/app.json` |
| `capabilities/default.json` | Permisos del webview (event/window/dialog/updater/opener/app) |

## Modo desarrollo

El shell arranca el motor desde el checkout del repositorio si define estas variables:

- `OPENRED_ENGINE_PYTHON`: ruta al intérprete (p. ej. `engine\.venv\Scripts\python.exe`).
- `OPENRED_ENGINE_DIR`: directorio que contiene el paquete `openred_engine` (p. ej. `engine`).
  Se usa como `cwd` y se añade a `PYTHONPATH`.

En PowerShell, desde `apps/desktop`:

```powershell
$env:OPENRED_ENGINE_PYTHON = "..\..\engine\.venv\Scripts\python.exe"
$env:OPENRED_ENGINE_DIR    = "..\..\engine"
npm run tauri dev
```

Si falta cualquiera de las dos variables se usa el layout de release (intérprete embebido), que
no existe en el checkout: define ambas para trabajar en local. El motor se lanza con
`python -s -X utf8 -m openred_engine`, así que el paquete `openred_engine` debe exponer
`__main__.py` (a cargo del workstream del motor).

Variables que el shell inyecta siempre al sidecar: `PYTHONNOUSERSITE=1`, `PYTHONUTF8=1`,
`PYTHONDONTWRITEBYTECODE=1`, `MPLBACKEND=Agg`, `MPLCONFIGDIR=<datos>/mpl-data`,
`OPENRED_DATA_DIR=<datos>`, `OPENRED_RESOURCE_DIR=<motor>`, `PYTHONPATH=<motor>` (más
`<motor>/python/site-packages` si existe, para bundles antiguos) y `OPENRED_WORKDIR=<workdir>`
si `config/app.json` guarda uno. En release las wheels viven dentro del propio runtime
(`<motor>/python/Lib/site-packages`), así que no se necesita `PYTHONPATH` para las dependencias.

## Layout del bundle de release (plan §3.2)

```text
<install_dir>/OpenRED/
├── OpenRED.exe                  # binario Tauri (mainBinaryName = "OpenRED")
├── engine/                      # recursos Python empaquetados (solo lectura)
│   ├── python/
│   │   ├── python.exe           # CPython 3.12 embebido (python-build-standalone)
│   │   └── site-packages/       # numpy, scipy, matplotlib, pyserial
│   ├── openred_engine/          # paquete del sidecar (incluye `__main__.py`)
│   │   └── plugins/{GrainLibrary,NozzleLibrary}/
│   └── engine.lock              # hashes SHA-256 (integridad)
└── resources/                   # iconos, assets, LICENSES/
```

El shell resuelve el motor como `<resource_dir>/engine` (`tauri::path::resource_dir()`); en
Windows `resource_dir()` es el directorio del `.exe`, en macOS `Contents/Resources`. El empaquetado
de `engine/` en el instalador (recursos de `tauri.conf.json`) queda pendiente del workstream de
distribución (§3.1/§3.4).

Datos mutables (nunca en la carpeta de instalación):

- Windows: `%APPDATA%\OpenRED\{config,logs,mpl-data}`.
- macOS: `~/Library/Application Support/OpenRED/…`; Linux: `~/.local/share/OpenRED/…`.

`config/app.json` guarda `{ "workdir": "<ruta>" }` (lo escribe el comando `save_workdir` y lo lee
el supervisor para exportar `OPENRED_WORKDIR` al arrancar/reiniciar el motor).

## Comandos Tauri

| Comando | Descripción |
|---|---|
| `engine_request(method, params?)` | Reenvía una petición JSON-RPC al sidecar (timeout 300 s) |
| `engine_status()` | `{running, pid, lastError, version}` |
| `engine_restart()` | Relanza el sidecar y espera `ready` (15 s) |
| `pick_workdir()` | Diálogo de carpeta → ruta o `null` |
| `pick_file(filters?)` | Diálogo de fichero (`filters`: extensiones) |
| `pick_save_file(defaultName?)` | Diálogo "Guardar como" |
| `open_logs_folder()` | Abre `<datos>/logs` en el explorador |
| `app_info()` | `{version, dataDir, resourceDir, platform}` |
| `save_workdir(path)` | Persiste `workdir` en `config/app.json` |

Los argumentos llegan desde JS en camelCase (p. ej. `defaultName`, `invoke('engine_request', { method, params })`).

### Eventos emitidos al webview

| Evento | Payload |
|---|---|
| `engine-event` | Notificación cruda del motor (`{"name":...}`), p. ej. `ready`, `progress`, `console`, `job_done` |
| `engine-status` | `{running, pid, version, error}` (arranque listo, caída, parada) |
| `engine-log` | `{level, line}` por cada línea de stderr del motor |
| `engine-request` | `{id, method, phase:"start"}` al despachar una petición |

`engine-request` permite conocer el `id` de una petición en vuelo para cancelarla con
`engine_request("request.cancel", { id })` sin bloquear otras peticiones.

### Ciclo de vida del sidecar

1. Arranque al iniciar la app; se espera `event ready` con timeout de 10 s.
2. Si no llega `ready` o el proceso muere: **1 reintento automático** con backoff de 1 s y evento
   `engine-status {running:false, error}`. El presupuesto de reinicio solo se renueva cuando el
   proceso ha estado listo ≥ 30 s (evita bucles de reinicio con un motor inestable).
3. `engine_restart` fuerza un relanzamiento manual y resetea el presupuesto.
4. Al cerrar la app (`RunEvent::ExitRequested`): se envía `app.shutdown` con 3 s de gracia y, si no
   responde, se mata el proceso.

## Logging

`RUST_LOG` controla el filtro (por defecto `info`). Fichero rotado a diario en
`<datos>/logs/openred.log.YYYY-MM-DD`; en builds `debug` también se escribe a stderr. Las líneas de
stderr del motor se reenvían además como evento `engine-log`.

## Updater (placeholder)

`tauri.conf.json` → `plugins.updater` apunta al manifiesto de releases:
`https://github.com/marcosflz/OpenRED-desktop/releases/latest/latest.json`.

> **Pendiente de release:** `pubkey` está vacío a propósito. Antes de publicar hay que generar el
> par minisign (`tauri signer generate`), poner la clave pública en `plugins.updater.pubkey` y
> firmar los artefactos con `TAURI_SIGNING_PRIVATE_KEY`. Con `pubkey` vacío, `check()` fallará.

## Verificación

```powershell
cargo check          # sin errores
cargo test           # tests del parser JSONL, framing de respuestas y specs de arranque
npm run build        # desde apps/desktop (frontend)
```

Iconos regenerados con `npx tauri icon ../../legacy/icon.ico` desde `apps/desktop`
(`src-tauri/icons/**`).
