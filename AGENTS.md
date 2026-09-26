# AGENTS.md — cómo operar en este repo

Guía práctica para agentes y personas que **añaden o modifican funcionalidad** en OpenRED.
Complementa a `README.md` (visión general), `contracts/README.md` (contrato IPC),
`docs/IMPLEMENTATION_STATUS.md` (estado y verificación) y `PLAN_MIGRACION_ESCRITORIO.md` (plan
histórico de la migración; no es fuente de verdad del código actual).

## 1. Arquitectura en 30 segundos

```
React UI (apps/desktop/src)
   │  request<T>("ns.metodo", params)        ← src/api/engine.ts
   ▼
Tauri/Rust (apps/desktop/src-tauri/src)     ← comando engine_request (commands.rs → ipc.rs → sidecar.rs)
   │  JSON-RPC por stdio, una línea JSON por mensaje
   ▼
Motor Python (engine/openred_engine)        ← servicios en services/*.py, dispatcher en rpc.py
   │
   ├─ ficheros: <workdir>/{Engines,Nozzles,Sketches,Tests,config.json,checklist.json}
   ├─ SQLite:   <data>/database.db      (%APPDATA%\OpenRED)
   └─ serial:   banco de ensayos (pyserial, transporte simulado en tests)
```

`legacy/` es la **referencia ejecutable** de la app original (Python/Tk). Los números, ficheros
exportados y líneas de consola del clon deben ser idénticos.

| Directorio | Qué hay / cuándo tocarlo |
|---|---|
| `legacy/` | App original **congelada**. No se modifica (solo lectura; shim documentado si es imprescindible). |
| `engine/openred_engine/` | Motor headless: servicios RPC, cálculo, BD, plugins. |
| `engine/tests/` | Tests del motor (pytest, marcadores `golden`, `serial`, `slow`). |
| `contracts/` | Contrato IPC congelado (`methods.md`), esquemas JSON y fixtures dorados. |
| `apps/desktop/src/` | UI React: `api/` (cliente tipado + mock), `app/` (shell), `ui/` (módulos), `test/` (vitest). |
| `apps/desktop/src-tauri/` | Shell Rust: sidecar, comandos nativos, empaquetado (`tauri.conf.json`). |
| `tools/parity/` | Harness de paridad (`run_parity.py`, `gen_fixtures.py`, `validate_schemas.py`). |
| `tools/python-portable/`, `tools/packaging/` | Runtime Python portable y bundle/instaladores. |
| `tools/migration/` | Verificación de datos legacy migrados. |
| `tests/defects/` | Divergencias y bugs del legacy (`DEF-*.md`, `TEMPLATE.md`). |
| `docs/` | Estado de implementación y guía de migración de datos. |

## 2. Reglas de oro

1. **`legacy/` no se toca.** Si un comportamiento difiere a propósito, se documenta en
   `tests/defects/DEF-XXXX.md` con la decisión que lo ampara (p. ej. DEF-0001, export de toberas).
2. **El contrato está congelado.** Cualquier método/evento/campo nuevo —aunque sea aditivo— pasa
   por un RFC en `contracts/RFC-XXXX-*.md` (plantilla en `contracts/README.md`) antes de tocar
   `contracts/`, y en el mismo cambio se actualizan `methods.md`, esquemas, fixtures y consumidores.
3. **Paridad numérica y de ficheros.** Tolerancia de referencia `numpy.allclose(rtol=1e-9, atol=0)`;
   JSON/CSV byte-compatibles salvo las normalizaciones documentadas (`DP. Thrust (kg)1`,
   `Sketch,Plane`, CRLF). La consola conserva formato y orden exactos.
4. **Los datos mutables viven fuera del motor**: `<data>` (`%APPDATA%\OpenRED`: `database.db`,
   `config/app.json`, `logs/`, `mpl-data/`) y el directorio de trabajo del usuario. El motor
   **nunca** escribe en su directorio de instalación (`OPENRED_RESOURCE_DIR`). Usa `paths.py`.
5. **El motor no importa tkinter** y stdout es **solo** protocolo JSON-RPC; los diagnósticos van a
   stderr (`logging_setup`). matplotlib siempre con backend `Agg`.
6. **La UI no calcula**: orquesta y pinta. Todo cálculo/persistencia va por un método RPC del motor.
7. **Sin permisos implícitos de escritura fuera** de `<workdir>` y `<data>`; nada de rutas absolutas
   de la máquina en código, tests o fixtures.
8. **No hagas `git commit`/`git push`** salvo que se te pida expresamente.

## 3. Entorno de desarrollo

Requisitos: Python 3.12 (gestionado con **uv**), Node 20+, Rust estable + prerequisitos de Tauri 2.
En Windows, el `python` del PATH de esta máquina puede estar roto: usa siempre `uv` o el venv.

```powershell
# Dependencias del motor (una vez)
cd engine; uv sync --extra dev

# Motor: tests y lint
cd engine
uv run pytest                                  # suite completa
uv run pytest -m "not slow"                    # lo que corre en CI
uv run pytest -m golden                        # paridad con fixtures dorados
uv run ruff check

# UI + shell (apps/desktop)
npm ci
npx tsc --noEmit
npx vitest run
cd src-tauri; cargo test

# Desarrollo con el motor del checkout (el binario de release usa su propio Python)
$env:OPENRED_ENGINE_PYTHON = "..\..\engine\.venv\Scripts\python.exe"
$env:OPENRED_ENGINE_DIR    = "..\..\engine"
npm run tauri dev
```

Datos de desarrollo: `%APPDATA%\OpenRED` (BD, `config/app.json`, logs) y `~/Documents/OpenRED`
(workdir por defecto). Para partir de cero, **haz copia** de `database.db` y borra esa carpeta.
Los logs del shell están en `%APPDATA%\OpenRED\logs\openred.log.<fecha>`.

## 4. Flujo para añadir una feature

0. **Decide si toca el contrato** (nuevo método/evento/parámetro/campo de resultado): si sí, empieza
   por el RFC (regla de oro 2). Si es solo UI sobre métodos existentes, salta al paso 3.
1. **Contrato**: RFC aceptado → `contracts/methods.md` (§3.x) + esquema del namespace
   (`contracts/schemas/<ns>.schema.json`: `oneOf` + `$defs`, `additionalProperties: false` por
   defecto) + fixtures que reflejen el caso.
2. **Fixtures**: si hay referencia legacy, genera el dorado ejecutándolo con
   `tools/parity/gen_fixtures.py` (nunca a mano); si es una feature nueva sin legacy, crea el
   fixture con `id`, `tag`, `provenance` y añade ese `id` a `FIXTURE_SCHEMA` de
   `tools/parity/validate_schemas.py`.
3. **Motor**: implementa el handler en `engine/openred_engine/services/<ns>.py` y regístralo en
   `METHODS`. Si el namespace es perezoso (`engine`, `nozzle`, `cad`, `testbed`) añádelo también a
   `_KNOWN_METHODS` en `services/__init__.py`. Errores con `RpcError(code, message, detail)` usando
   los códigos de `rpc.py`. Nada de I/O en el import del dispatcher.
4. **Tests del motor**: `engine/tests/test_*.py`. Los numéricos van marcados `golden` contra el
   legacy; los de serial usan `testbed.mock` (marcador `serial`).
5. **Puente TS**: añade los tipos a `apps/desktop/src/api/types.ts` y **el caso en
   `apps/desktop/src/api/mock.ts`** (obligatorio: sin él, `vitest` y el modo navegador fallan con
   `-32601`). Los atajos de `engine.ts` solo para comandos de app; los módulos llaman
   `request<T>("ns.metodo", params)`.
6. **UI**: componente en `apps/desktop/src/ui/<modulo>/index.tsx` (o dentro del módulo existente),
   pestaña en `apps/desktop/src/app/tabs.tsx` si es un módulo nuevo, estados vacíos/cargando/error y
   textos en español como la app original. Test en `apps/desktop/src/test/ui-*.test.tsx` usando el
   mock.
7. **Verificación completa** (§6) y, si aplica, actualiza `docs/` (`IMPLEMENTATION_STATUS.md`,
   `MIGRACION_DATOS.md`…). Si el cambio afecta al empaquetado, reconstruye el bundle (§7).

## 5. Recetas

### 5.1 Añadir un método RPC

1. RFC + `methods.md` + `contracts/schemas/<ns>.schema.json`.
2. `services/<ns>.py`: handler `def mi_metodo(params, ctx) -> dict` y entrada en `METHODS`.
3. `services/__init__.py`: entrada en `_KNOWN_METHODS` si es namespace perezoso.
4. `engine/tests/`: test unitario/integración (`test_rpc_integration.py` para el sobre RPC).
5. `api/types.ts` + `api/mock.ts` + UI.
6. `uv run --project engine python tools/parity/validate_schemas.py` (valida `methods.md` ↔
   esquemas ↔ fixtures; un método documentado sin esquema, o un fixture que invoca un método no
   declarado, falla).

### 5.2 Cambiar lógica numérica (mantener paridad)

- Copia el algoritmo de `legacy/back_modules/**` **literalmente** (mismas tolerancias, semillas de
  `fsolve`, orden de operaciones). Referencia: `engine/openred_engine/modules/back_*.py`.
- Si hay que divergir: `tests/defects/DEF-XXXX.md` (usa `TEMPLATE.md`) + justificación en el RFC si
  toca el contrato.
- Añade/actualiza un test `@pytest.mark.golden` y el fixture; después:
  `uv run --project engine python tools/parity/run_parity.py --full`.
- Si cambia una salida exportable (JSON/CSV/consola), el fixture debe volver a generarse
  **ejecutando el legacy** y el diff debe ser explicable línea a línea.

### 5.3 Añadir un plugin (GrainLibrary / NozzleLibrary)

- Fichero en `engine/openred_engine/plugins/<Library>/*.py` con una clase que exponga
  `nozzle_type` y el contrato de etiquetas heredado (`plugins.list` → `{labels: {label: clave}}`).
- No registres módulos sin clase plugin (p. ej. `SQUARE.py` se conserva pero no se registra).
- Test en `engine/tests/test_plugins.py` / `test_nozzle_library.py` y, si define UI, un caso en el
  mock de TS.

### 5.4 Añadir un módulo de UI

- `apps/desktop/src/ui/<modulo>/index.tsx` con `TabModuleProps`; pestaña en `app/tabs.tsx`
  (`TabId`, `TABS`) y el icono/etiqueta en el sidebar si aplica.
- Reutiliza `WorkspaceProvider` (`useWorkspace`) para workdir/config y `Toast` para avisos.
- Test de componente con `mockRequest`; nada de lógica de cálculo en el componente.

### 5.5 Añadir un comando nativo de Tauri

- `apps/desktop/src-tauri/src/commands.rs` (`#[tauri::command]`) + registro en
  `lib.rs::invoke_handler` + permiso en `src-tauri/capabilities/default.json` si toca.
- Envoltorio tipado en `api/engine.ts` (`invokeCommand<T>`), caso en `api/mock.ts` y test de UI.
- Comandos actuales: `engine_request`, `engine_status`, `engine_restart`, `pick_workdir`,
  `pick_file`, `pick_save_file`, `open_logs_folder`, `app_info`, `save_workdir`.

### 5.6 Añadir o actualizar un fixture dorado

```powershell
uv run --project engine python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures --full
uv run --project engine python tools/parity/validate_schemas.py
uv run --project engine python tools/parity/run_parity.py --full --report parity-report.json
```

Reglas: sin rutas absolutas ni timestamps, con `provenance` (commit + comando), id nuevo declarado
en `FIXTURE_SCHEMA` (validate_schemas) y `rpc.method` presente en el esquema del namespace.

### 5.7 BD y almacenamiento

- La BD es **idéntica al legacy** (`propelente`, `termoquimica`); no cambies el esquema sin RFC y
  plan de migración (ver `docs/MIGRACION_DATOS.md`). El acceso está centralizado en `store.py`
  (escritura con snapshot `database.db.bak` vía `backup_once`).
- Ficheros JSON del usuario: escritura atómica (`write_json_atomic`, tmp + `os.replace`), nunca
  escrituras parciales, y respeta los nombres exactos del legacy.

## 6. Verificación (puerta completa)

| Comando | Qué cubre | CI |
|---|---|---|
| `cd engine; uv run ruff check` | estilo motor | engine-ci |
| `cd engine; uv run pytest -m "not slow"` | unitarios + integración | engine-ci |
| `uv run --project engine python tools/parity/validate_schemas.py` | contrato ↔ esquemas ↔ fixtures | engine-ci / parity |
| `uv run --project engine python tools/parity/run_parity.py --full` | paridad T0–T4 (9 checks) | parity |
| `cd apps/desktop; npx tsc --noEmit && npx vitest run` | UI | desktop-ci |
| `cd apps/desktop/src-tauri; cargo test` | shell Rust | desktop-ci |
| `pwsh tests/clean-machine/smoke.ps1 -InstallDir <dir>` | bundle instalado autosuficiente | clean-machine |
| `python tools/migration/verify_migration.py` | datos legacy migrados (opcional) | — |

Empaquetado (solo si tocas motor/runtime/configuración del bundle):

```powershell
pwsh tools/python-portable/fetch_python.ps1        # runtime portable (uv instala las wheels dentro)
pwsh tools/packaging/build_engine_bundle.ps1       # artifacts/engine-bundle + engine.lock
cd apps/desktop; npx tauri build --bundles nsis,msi
```

> El bundle **copia** el motor: si cambias `engine/openred_engine`, reconstruye el bundle antes de
> probar el instalador o el smoke. En desarrollo normal usa el venv del checkout (§3).

## 7. Diagnóstico

- **Logs**: `%APPDATA%\OpenRED\logs\openred.log.<fecha>` (shell/sidecar) y `engine.log` (motor).
  `File → Open logs folder` en la app.
- **`parity-report.json`**: detalle de cada fallo de paridad (raíz del repo).
- **Contrato**: `validate_schemas.py` dice exactamente qué método/fixture no cuadra.
- **Trampas conocidas**:
  - `python` del PATH roto → `uv run …` o `engine\.venv\Scripts\python.exe`.
  - Deadlock de scipy/OpenMP al arrancar: existe un warm-up (`warmup.py`); no lo elimines ni muevas
    imports pesados al dispatcher (los servicios pesados se cargan de forma perezosa).
  - El plugin de instancia única cierra la segunda instancia: mata la app antes de relanzarla en
    pruebas automatizadas.
  - Los CSV se comparan normalizando CRLF; al escribirlos, usa `newline=""` como el original.
  - `engine/python/` y `artifacts/` están en `.gitignore`: no los commitees y no los uses como
    fuente del motor en desarrollo.
  - Un DEF del legacy no siempre se corrige en `legacy/`: el clon puede implementarlo bien con la
    decisión documentada (ver DEF-0001..DEF-0005).

## 8. Convenciones

- **Idioma**: documentos y UI en español; identificadores, código y mensajes de log del motor en
  inglés (los mensajes de error visibles pueden ser los del legacy, literales).
- **Nombres**: métodos `namespace.snake_case`; eventos `snake_case`; campos del contrato con el
  nombre exacto del legacy (`Propelente`, `T_ad`, `workdirSelected`…). No renombres campos.
- **Python**: ruff (`E,F,W,I,UP,B`, línea 120), type hints, servicios que devuelven `dict`, errores
  como `RpcError`. Nada de estado global salvo el `paths`/config del motor.
- **TS**: strict; componentes funcionales; tipos del contrato en `api/types.ts`; sin `any`.
- **Rust**: `cargo fmt`/`clippy` cuando toques `src-tauri`; mantén los comandos finos (la lógica
  vive en `sidecar.rs`/`ipc.rs`).
- **Tests**: nombres descriptivos; los numéricos marcados `golden`; los de serial, `serial`; los
  lentos, `slow` (excluidos de CI por defecto).

## 9. Definición de hecho

- [ ] RFC si toca el contrato (y `methods.md`/esquemas/fixtures actualizados en el mismo cambio).
- [ ] Motor + registro (`METHODS`, `_KNOWN_METHODS` si aplica) y tests.
- [ ] Tipos TS + caso en `api/mock.ts` + test de UI.
- [ ] `ruff`, `pytest -m "not slow"`, `validate_schemas.py`, `run_parity.py --full`, `tsc`,
      `vitest`, `cargo test` en verde.
- [ ] Sin rutas absolutas de la máquina en código/fixtures; sin escrituras fuera de `<data>`/`<workdir>`.
- [ ] Divergencias de paridad documentadas en `tests/defects/DEF-*.md`.
- [ ] Documentación actualizada (`docs/`, `README.md`, `contracts/`) si cambia el comportamiento o
      el flujo de trabajo.
