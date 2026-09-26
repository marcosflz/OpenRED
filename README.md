# OpenRED — Rocket Engine Designer

OpenRED es una aplicación de escritorio de código abierto para el diseño de motores cohete de
propelente sólido (equipos universitarios). Cubre el flujo completo: definición química del
propelente, cálculo de la temperatura adiabática de llama, diseño del grano por Level-Set,
diseño de tobera, generación de croquis CAD para Fusion360 y banco de pruebas con ESP32.

Este repositorio contiene el **clon nativo de escritorio** (Tauri 2 + React + motor Python
headless). El código original en Python/CustomTkinter se conserva en `legacy/` como referencia
de paridad.

> **¿Vas a añadir o modificar funcionalidad?** Lee `AGENTS.md`: flujo de trabajo, reglas de
> contrato y paridad, comandos de verificación y trampas conocidas.

## Arquitectura

```
apps/desktop/src-tauri   Shell Rust/Tauri 2: ventana, supervisor del sidecar, router JSON-RPC,
                         diálogos, logs, single-instance, updater
apps/desktop/src         UI React 19 + TypeScript + Vite: 8 módulos, design system, ECharts, KaTeX
engine/openred_engine    Sidecar Python 3.12 headless (JSON-RPC por stdio):
                         • modules/back_0|1|2 (termodinámica, Level-Set, CAD) — puerto literal de legacy/
                         • plugins/GrainLibrary, plugins/NozzleLibrary (contrato nozzle_type)
                         • services/* (workspace, db, adiabatic, engine, nozzle, cad, testbed)
                         • matplotlib(Agg)→PNG, pyserial + Transport mock
contracts/               Contrato IPC congelado (methods.md), JSON Schemas y fixtures dorados
tools/                   Paridad legacy↔clon, Python portable, empaquetado
tests/                   Defectos y pruebas clean-machine
legacy/                  Snapshot de la app original (referencia de paridad, no se despliega)
```

- **Sin Tcl/Tk**: el runtime Python excluye `tkinter`/`customtkinter`; las figuras se renderizan
  con matplotlib (backend `Agg`) y viajan como PNG base64.
- **Datos mutables fuera de la instalación**: `%APPDATA%\OpenRED` (o XDG) para `database.db`,
  logs y caché. El "working directory" del usuario se elige desde la app y contiene
  `Engines/ Nozzles/ Sketches/ Tests/ config.json`.
- **Paridad**: mismos algoritmos, mismas semillas de `fsolve`, mismos formatos de fichero
  (engine JSON, nozzle JSON, CSV CAD, CSV de tests) y la misma consola del cálculo LSM.

## Desarrollo

Requisitos: Rust ≥1.85, Node ≥20, [uv](https://docs.astral.sh/uv/).

```powershell
# 1) Motor (tests + ejecución)
cd engine
uv sync --extra dev
uv run pytest -q
uv run python -m openred_engine   # arranca el sidecar (JSON-RPC por stdin/stdout)

# 2) UI (dev en navegador con backend simulado)
cd apps\desktop
npm ci
npx vite                # http://localhost:5173 (mock, sin Rust)

# 3) App completa (Tauri + motor real)
$env:OPENRED_ENGINE_PYTHON = "$PWD\..\engine\.venv\Scripts\python.exe"
$env:OPENRED_ENGINE_DIR    = (Resolve-Path "$PWD\..\engine")
npm run tauri dev
```

En release el shell usa el runtime empaquetado en `<install>\engine\python\python.exe` (con las
dependencias dentro del propio runtime); en desarrollo se apuntan `OPENRED_ENGINE_PYTHON` y
`OPENRED_ENGINE_DIR` al checkout (ver `apps/desktop/src-tauri/README.md`).

## Tests y paridad

```powershell
# Motor
cd engine; uv run pytest -q                       # unitarios + golden vs legacy
# UI
cd apps\desktop; npx vitest run; npx tsc --noEmit
# Shell Rust
cd apps\desktop\src-tauri; cargo test
# Paridad completa clon ↔ legacy (fixtures dorados)
python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures --full
python tools/parity/run_parity.py --full
```

Los fixtures (`contracts/fixtures/`) se generan ejecutando el código de `legacy/` y son la
referencia de las matrices T0–T4 del plan de migración. Toda divergencia debe documentarse en
`tests/defects/`.

## Empaquetado

- `tools/python-portable/fetch_python.ps1` descarga python-build-standalone (tag y SHA-256
  fijados en `tools/python-portable/python.lock`) e instala `engine/requirements-core.lock` con
  **uv** dentro del propio runtime (fallback: pip).
- `tools/packaging/build_engine_bundle.ps1` arma `artifacts/engine-bundle/` (runtime + motor + `engine.lock`).
- `tools/packaging/build_installer.ps1` produce MSI/NSIS con `tauri build` (el bundle va como
  `bundle.resources` de Tauri, copiado a `<install>/engine`).
- Actualizaciones: `tauri-plugin-updater` con manifest firmado (`latest.json`); la clave pública
  debe generarse en cada release.

## Migrar datos del legacy

- `docs/MIGRACION_DATOS.md`: pasa `database.db` y el directorio de trabajo del legacy al clon
  (`%APPDATA%\OpenRED\database.db` y `Documents\OpenRED`). Las tablas son idénticas, se copian
  tal cual.
- `tools/migration/verify_migration.py`: comprueba la migración contra el motor empaquetado
  (41 comprobaciones: listados, BD, cálculo T2, CAD T3 y persistencia del workdir).

## Estado

Implementado y verificado en este repositorio: motor completo (T0–T4) con paridad numérica y de
ficheros frente a `legacy/`, shell Tauri 2, UI de los 8 módulos, empaquetado del motor portable,
e **instalador NSIS + portable ZIP construidos y probados sobre la instalación real**
(`target/release/bundle/nsis/OpenRED_0.1.0_x64-setup.exe`, `artifacts/OpenRED-portable-x64.zip`).

Pendiente de verificación física/hardware: protocolo del banco ESP32 real (probado con transporte
simulado y replay de CSV), firma Authenticode/Developer ID, y pruebas clean-machine canónicas en
VM (ver `tests/clean-machine/` y `docs/IMPLEMENTATION_STATUS.md`).

## Licencia

GPL-3.0 (heredada del proyecto original). Las dependencias mantienen sus licencias (PSF, BSD-3,
HPND, DejaVu); ver `resources/LICENSES/` al empaquetar.
