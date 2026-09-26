# Estado de implementación — migración de escritorio de OpenRED

> Informe de ejecución del `PLAN_MIGRACION_ESCRITORIO.md`. Fecha: 2026-09-25.
> Base legacy: `c2250d0` (ahora en `legacy/`). Todo lo marcado como verificado se ha
> ejecutado en esta máquina (Windows 11, Rust 1.98, Node 24, CPython 3.12.12 vía uv).

## 1. Resumen ejecutivo

| Área | Estado | Evidencia |
|---|---|---|
| Motores de cálculo T0–T4 (sidecar Python) | **Implementado y con paridad verificada** | `engine/tests` 83 tests · `tools/parity/run_parity.py --full` **9/9 PASS** |
| Contratos IPC + esquemas + fixtures dorados | **Congelado y validado** | `contracts/` · `validate_schemas.py` 90 checks |
| Shell Tauri 2 (supervisor, router, diálogos, logs) | **Implementado y probado** | `cargo test` 20/20 · arranque real del `.exe` con sidecar `ready` |
| UI React (8 módulos, design system) | **Implementado** | `tsc` limpio · `vitest` 47/47 · `vite build` OK |
| CI/CD, Python portable, empaquetado | **Instaladores NSIS + MSI y portable ZIP construidos y verificados** | `OpenRED_0.1.0_x64-setup.exe` (69,7 MB) · `OpenRED_0.1.0_x64_en-US.msi` (120,7 MB) · `artifacts/OpenRED-portable-x64.zip` (121,5 MB) · smoke clean-machine PASS sobre la instalación real y sobre el MSI extraído |
| Hardware real (ESP32), macOS/Linux, firma | **Pendiente por entorno** | ver §5 |

El clon reproduce el legacy en los cuatro módulos de cálculo, incluidos los **archivos
exportados byte a byte** (engine JSON, nozzle JSON, 3 CSV CAD y CSV del banco de pruebas).

## 2. Qué se implementó

### 2.1 Repositorio
- Estructura objetivo del plan §5.1: `legacy/`, `contracts/`, `engine/`, `apps/desktop/`,
  `tools/`, `tests/`, `.github/workflows/`.
- `legacy/` conserva el código original completo (app, módulos, venv, instalador, working
  directory de ejemplo) como referencia de paridad.

### 2.2 Motor headless (`engine/openred_engine`)
- **RPC JSONL sobre stdio** (`rpc.py`): peticiones, respuestas, errores de dominio, eventos,
  cancelación por id, apagado ordenado.
- **Servicios**: `workspace`, `db`, `adiabatic`, `engine`, `nozzle`, `cad`, `testbed`, `plugins`
  (~45 métodos).
- **Núcleo portado literalmente** desde `legacy/`: `back_0` (termodinámica NASA), `back_1`
  (Level-Set + `fsolve`), `back_2` (CAD), `GrainLibrary`, `NozzleLibrary` — sin tkinter, sin CWD
  relativo, sin `messagebox`.
- **Persistencia**: SQLite con el mismo esquema en `%APPDATA%\OpenRED\database.db` (D6/D10),
  DAO con reasignación de IDs y backup, escrituras atómicas.
- **Figuras**: matplotlib(Agg) → PNG base64. **Serial**: pyserial + `Transport` + `MockTransport`.
- Correcciones de integración documentadas en `tests/defects/` (DEF-0001..DEF-0005), incluido
  el bug de export del legacy (que el clon implementa bien, R10) y el deadlock de scipy.

### 2.3 Shell de escritorio (`apps/desktop/src-tauri`)
- Supervisor del sidecar (spawn dev/release, `ready` con timeout, 1 reinicio, kill al salir),
  router JSON-RPC con ids/eventos, logs rotados a `%APPDATA%\OpenRED\logs`, single-instance,
  updater configurado, diálogos nativos y comandos de app.
- `tauri.conf.json`: OpenRED, 1280×800, MSI+NSIS, iconos generados desde `legacy/icon.ico`.

### 2.4 UI (`apps/desktop/src`)
- Shell: menú File/Preferences/Database/Help, sidebar de 8 módulos, temas `red`/`orange` ×
  dark/light con los colores de `legacy/themes/*.json`, estado de workspace y config.json.
- Design system propio (40+ componentes) + cliente RPC tipado + backend mock para dev/tests.
- Módulos: **Adiabatic Temp** (+ ventanas CRUD de componentes/propelentes y curva de quemado),
  **Engine Design** (geometría, consola en vivo, Level-Set, DATA/GRAPHS, export),
  **Nozzle Design** (carga, sliders, cálculo cancelable, off-design, tablas, export),
  **CAD Design** (25 campos, 6 vistas, 3 exports con confirmación), **Testing Bed**
  (checklist, puertos, WiFi, consola, gauges/plots, replay), y los 3 placeholders "Soon".

## 3. Verificación ejecutada (comandos reales)

```powershell
# Motor
cd engine; uv run ruff check openred_engine tests     # All checks passed
uv run pytest -o addopts="" -q                       # 83 passed

# Paridad clon ↔ legacy (fixtures dorados generados con --full)
python tools/parity/validate_schemas.py              # OK: 90 checks
python tools/parity/run_parity.py --full             # 9 passed, 0 failed
#   t0_adiabatic, t0_error, t1_engine_smoke (294), t1_engine_full (585),
#   t2_load_engine, t2_nozzle (21 resultados), t2_op_points (8 puntos, regímenes idénticos),
#   t3_cad (3 CSV byte-iguales), t4_replay (729 registros, CSV byte-igual)

# UI
cd apps\desktop; npx tsc --noEmit                    # sin errores
npx vitest run                                       # 47 passed
npx vite build                                       # OK

# Shell
cd apps\desktop\src-tauri; cargo test                # 20 passed
cargo build                                          # OK

# E2E del binario con el sidecar real (env de desarrollo)
#   openred-desktop.exe + OPENRED_ENGINE_PYTHON/OPENRED_ENGINE_DIR
#   -> "sidecar listo" en ~0,7 s, sin procesos huérfanos al cerrar

# Empaquetado (motor portable + instaladores)
pwsh tools/python-portable/fetch_python.ps1          # CPython 3.12.14 + wheels con uv
pwsh tools/packaging/build_engine_bundle.ps1         # artifacts/engine-bundle (350 MB, engine.lock)
npx tauri build --bundles nsis                       # (desde apps/desktop)
#   -> ...\target\release\bundle\nsis\OpenRED_0.1.0_x64-setup.exe  (69,7 MB)
npx tauri build --bundles msi
#   -> ...\target\release\bundle\msi\OpenRED_0.1.0_x64_en-US.msi   (120,7 MB)

# Verificación de la instalación real (ya ejecutada)
#   1) setup.exe /S /D=<dir>            -> layout <dir>\{OpenRED.exe, engine\}
#   2) tests/clean-machine/smoke.ps1 -InstallDir <dir>   -> PASS (engine.lock 6458 ficheros,
#      app.ping + workspace + T0 + T1 reducido con 294 líneas idénticas al fixture)
#   3) <dir>\OpenRED.exe SIN variables de entorno -> arranca <dir>\engine\python\python.exe,
#      "sidecar listo" en ~1,3 s, 0 huérfanos al cerrar
#   4) MSI: msiexec /a ... TARGETDIR=<dir> -> payload idéntico; smoke PASS
#   5) portable: artifacts/OpenRED-portable-x64.zip extraído en otra ruta -> funciona igual

# Migración de datos reales del legacy (BD + working directory) — ver docs/MIGRACION_DATOS.md
#   legacy/database.db            -> %APPDATA%\OpenRED\database.db        (1 propelente KNSU, 13 componentes)
#   legacy/workingDirectory\*     -> %USERPROFILE%\Documents\OpenRED      (Engines/Nozzles/Sketches/Tests)
#   verificación por JSON-RPC sobre el motor empaquetado: 37/37 PASS
#     (listados idénticos, valores de BD exactos, T2 nozzle.calculate 21 valores,
#      T3 3 CSV idénticos escritos en el workdir migrado, workdir persistido en app.json)
#   y arranque real del portable con los datos: barra de estado C:/Users/marco/Documents/OpenRED,
#     propelente KNSU (1) y config.json/Tubular-Grain restaurados
```

## 4. Matriz de paridad §4.2 — cobertura

| Bloque | Cobertura | Notas |
|---|---|---|
| **G1–G12** (shell, config, temas, temp_dir) | Implementado; G3 verificado por esquema/estructura y golden de config | `temp_dir.txt` sustituido por estado persistente (G11, decisión documentada) |
| **T0-1–T0-6** | Implementado; T0-3/T0-4 golden numérico `rtol=1e-12`; T0-5/D-1..D-4 CRUD | |
| **T1-1–T1-8** | Implementado; T1-3 (consola idéntica), T1-6 (payload completo `rtol=1e-12`) y T1-8 (round-trip a tobera/CAD) verificados | |
| **T2-1–T2-10** | Implementado; T2-6 y T2-7 (8 puntos off-design, regímenes idénticos), T2-9 corregido y exportado; T2-5 cancelación probada | |
| **T3-1–T3-5** | Implementado; T3-3 golden CSV byte a byte; T3-5 AS-Nozzle con aviso | |
| **T4-1–T4-8** | Implementado; T4-7 replay con CSV byte a byte (729 registros) | |
| **T4-9 hardware real** | **Pendiente** (no hay banco ESP32 en este entorno) | Mock + replay cubiertos; plan de campo en §5 |

## 5. Pendiente / no verificable aquí

1. **Hardware del banco (T4-9)**: probar con el ESP32 real (mapeo COM, LEDs, `CONNECT`,
   grabación). El protocolo se replica desde `front_test.py` y está cubierto con mock/replay.
2. **Firma de código**: el instalador no está firmado (SmartScreen mostrará aviso). Requiere
   certificado OV/Azure Trusted Signing; después, generar el par minisign y rellenar
   `plugins.updater.pubkey`.
3. **MSI**: el instalador NSIS está construido y verificado; el MSI se genera con
   `npx tauri build --bundles msi` (WiX se descarga en el primer build).
4. **macOS (DMG) y Linux (AppImage/deb)**: scripts y `python.lock` preparados (flavors arm64/x64),
   pero no se han construido en esta máquina Windows.
5. **E2E con `tauri-driver`** y capturas visuales: requieren un entorno gráfico con WebDriver;
   la UI se ha validado con type-check, tests de componentes y arranque real del binario.
6. **Máquina limpia canónica**: `tests/clean-machine/smoke.ps1` (ya en verde sobre la instalación
   real) es el proxy de CI; la validación canónica en Windows Sandbox/VM sin Python queda para
   el workflow `clean-machine`.
7. **Rendimiento R8**: el debounce de 100 ms y el cálculo en sidecar están implementados; la
   medición `<200 ms` por actualización off-design debe medirse en hardware objetivo.

## 6. Cómo trabajar con el repo

```powershell
cd engine; uv sync --extra dev; uv run pytest -q     # motor + paridad
cd apps\desktop; npm ci; npx vite                    # UI con backend simulado
$env:OPENRED_ENGINE_PYTHON="$PWD\..\..\engine\.venv\Scripts\python.exe"
$env:OPENRED_ENGINE_DIR=(Resolve-Path "..\..\engine")
npm run tauri dev                                    # app completa
```

Los contratos viven en `contracts/methods.md` (fuente de verdad) y los cambios requieren RFC
(`contracts/README.md`). Los defectos se registran en `tests/defects/DEF-*.md`.
