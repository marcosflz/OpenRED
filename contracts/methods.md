# OpenRED Engine — Contrato IPC v1 (CONGELADO en M0)

> Fuente de verdad de métodos y eventos entre el shell Tauri (Rust) y el sidecar Python.
> Cambios posteriores requieren RFC en `contracts/RFC-*.md` (ver reglas de coordinación del plan).
> Esquemas formales: `contracts/schemas/*.schema.json`. Fixtures dorados: `contracts/fixtures/`.

## 1. Transporte

- Proceso: `python.exe -s -X utf8 -m openred_engine` con env:
  `PYTHONNOUSERSITE=1`, `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, `MPLBACKEND=Agg`,
  `MPLCONFIGDIR=<data>/mpl-data`, `OPENRED_DATA_DIR=<data>`, `OPENRED_RESOURCE_DIR=<install>/engine`,
  `OPENRED_WORKDIR=<dir de trabajo>` (opcional al arrancar).
- Una línea JSON por mensaje, UTF-8, terminada en `\n`. Nada más se escribe en stdout.
  Los diagnósticos van a stderr.
- Petición: `{"id": <int|str>, "method": "namespace.method", "params": {...}}`
- Respuesta OK: `{"id": <int|str>, "result": {...}}`
- Respuesta error: `{"id": <int|str>, "error": {"code": <int>, "message": <str>, "detail": <any|null>}}`
- Notificación (sin `id`): `{"method": "event", "params": {"name": "<evento>", ...}}`
- Al arrancar el sidecar envía `{"method":"event","params":{"name":"ready","version":"...","pid":N}}`.

## 2. Códigos de error

| code | significado |
|---|---|
| -32700 | JSON inválido |
| -32601 | método desconocido |
| -32602 | params inválidos (validación de esquema) |
| 1001 | no hay directorio de trabajo seleccionado |
| 1002 | fichero no encontrado / ilegible |
| 1003 | JSON de entrada inválido ("Invalid file.") |
| 1004 | ya existe `config.json` en la carpeta elegida |
| 1005 | cancelado por el usuario (`request.cancel`) |
| 1006 | cálculo divergente / sin convergencia |
| 1007 | operación no soportada (p. ej. tobera AS-Nozzle en CAD) |
| 1008 | sin conexión serial |
| 2000 | error interno (`detail` con traza resumida) |

## 3. Métodos y eventos

### 3.1 app

| Método | Params | Result |
|---|---|---|
| `app.ping` | `{}` | `{version, pid, python, dataDir, resourceDir, workdir}` |
| `app.info` | `{}` | `{version, dataDir, resourceDir, workdir, workdirSelected}` |
| `app.shutdown` | `{}` | `{ok:true}` (el proceso termina tras responder) |
| `request.cancel` | `{id: <id de la petición en curso>}` | `{cancelled: bool}` |

### 3.2 workspace

| Método | Params | Result |
|---|---|---|
| `workspace.get` | `{}` | `{workdir, workdirSelected}` |
| `workspace.set_dir` | `{path}` | `{workdir, created:[...], hasConfig, config}` — crea `Engines/ Nozzles/ Sketches/ Tests/`; carga `config.json` si existe (`config: null` si no) |
| `workspace.load_config` | `{}` | `{config, hasConfig}` |
| `workspace.save_config` | `{config, force?:bool}` | `{path}` — error 1004 si existe y `force!=true`; escritura atómica (tmp+rename) |
| `workspace.list` | `{kind:"Engines"\|"Nozzles"\|"Sketches"\|"Tests"}` | `{files:[{name, size, mtime}]}` |
| `workspace.ensure_workdir` | `{}` | `{workdir}` — crea el directorio por defecto `<Documents>/OpenRED` si no hay ninguno |

`config.json`: estructura exacta de la app original (claves `tabs.tab_0..tab_3`, valores numéricos como cadenas).
El motor NO interpreta el contenido: lo guarda/carga tal cual (paridad G3).

### 3.3 db

Tabla `termoquimica`: `id, Component, MolWeight, Hf0, minColdTemp, maxColdTemp, minHotTemp, maxHotTemp, a1..a5_cold, a1..a5_hot`.
Tabla `propelente`: `id, Propelente, T_ad, MolWeight, Cp, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n`.

| Método | Params | Result |
|---|---|---|
| `db.components.list` | `{}` | `{items:[{...columnas, latex}]}` — `latex` = `convert_to_latex(Component)` |
| `db.components.add` | `{values:{...sin id}}` | `{items:[...]}` — reasigna IDs secuenciales 1..N y las devuelve |
| `db.components.edit` | `{id, values}` | `{items:[...]}` — reasigna IDs tras la operación |
| `db.components.delete` | `{id}` | `{items:[...]}` — reasigna IDs tras la operación |
| `db.propellants.list` | `{}` | `{items:[{...columnas}]}` |
| `db.propellants.add` | `{values:{...sin id}}` | `{items:[...]}` |
| `db.propellants.edit` | `{id, values}` | `{items:[...]}` |
| `db.propellants.delete` | `{id}` | `{items:[...]}` |
| `db.propellants.burning_rate` | `{name, n_points?:1000}` | `{P:[...], r:[...], a, n, P1_min, P1_max}` — `r = a·P^n` sobre `[P1_min, P1_max]` |
| `db.clean_name` | `{name}` | `{clean}` — aplica `re.sub(r'\s*\(\d+\)\s*$','',name)` |

Comportamiento de paridad DB:
- Nombres duplicados permitidos (como el original).
- `reassign_ids` tras cada add/edit/delete.
- Validación científica (`validate_scientific_notation`) y reemplazo coma→punto se hacen en la UI; el motor valida y devuelve error `-32602` si un campo numérico no es parseable.
- Snapshot de `database.db` a `database.db.bak` antes de operaciones de escritura (retención: 1).

### 3.4 adiabatic (T0)

| Método | Params | Result |
|---|---|---|
| `adiabatic.calculate` | `{reac:[{moles:float, component:str}], prod:[...], t0:float, tGuess:float, hStep:float}` | `{tSol, molWeight, cp, cv, R, gamma, cChar}` |
| `adiabatic.component_info` | `{component}` | `{MolWeight, Hf0, minColdTemp, maxColdTemp, minHotTemp, maxHotTemp}` |
| `adiabatic.save_propellant` | `{values:{Propelente,T_ad,MolWeight,Cp,Cv,R,gamma,cChar,Density,P1_min,P1_max,a,n}}` | igual que `db.propellants.add` |

Errores: `hStep<=0` → `-32602` con `message="Invalid integration step value."`; componente inexistente → `-32602`
con `message="No data found for component: <x>"`. Moles no numéricos los sanea la UI a 0 (paridad T0-4).

### 3.5 plugins

| Método | Params | Result |
|---|---|---|
| `plugins.list` | `{library:"GrainLibrary"\|"NozzleLibrary"}` | `{plugins:{<nozzle_type>:{labels:{<label>:"<clave>"}}}}` |
| `plugins.reload` | `{}` | `{grain:[...], nozzle:[...]}` |

Escaneo de `OPENRED_RESOURCE_DIR/openred_engine/plugins/<library>/*.py`; se registran clases con atributo
`nozzle_type` (contrato heredado, R3). `SQUARE.py` se conserva pero no se registra (no tiene clase plugin).

### 3.6 engine (T1, diseño de motor)

| Método | Params | Result |
|---|---|---|
| `engine.geometry` | `{grain, spec:{<claves de labels>, rOut, dh}}` | `{png_b64, cad:{center:[x,y], x:[...], y:[...]}}` |
| `engine.calculate` | `{propellant, grain, spec:{P0,Rt,R2,Lc,dt,dh,It,<claves de labels>}, propellantData:{a,n,R,T1,cChar,rho_b,P1_min,P1_max}}` | ver abajo |
| `engine.save` | `{name, payload}` | `{path}` — escribe `Engines/<name>.json` (añade `.json` si falta) |
| `engine.load` | `{path}` | `{payload, arrays:{time,pressure,massFlow,mass}}` |
| `engine.list` | `{}` | `{files:[...]}` |

`engine.calculate` devuelve:
```
{
  "payload": { "inputs": {...exacto al export original...},
               "results": {meanPressure,maxPressure,minPressure,meanMassFlow,maxMassFlow,minMassFlow,
                           totalTime,totalMass,"tree_data":{"Time (s)","Pressure (Pa)","Mass Flow (kg/s)","Mass (kg)"}} },
  "arrays":  {"time":[...], "pressure":[...], "massFlow":[...], "mass":[...], "phi_samples":[<png? no>]},
  "figures": {"regression": b64, "pressure": b64, "massFlow": b64, "massBurn": b64}
}
```
- `inputs` incluye `Propellant, GrainGeo, CADx, CADy, CAD0` y todas las claves de `spec`/`propellantData`
  con los mismos nombres del original (`It` incluido). Los datos de `tree_data` excluyen la fila inicial
  (paridad exacta con `export_results`; el fichero de referencia es `legacy/workingDirectory/Engines/KNSU-32-RT65.json`).
- `figures.regression` equivale a `result_figure()`; `figures.pressure/massFlow/massBurn` a los 3 plots.
- Eventos durante el cálculo (mismo orden que la consola original, R13):
  - `event/console` `{job, line}` con `Iter: n\tt(s): ...\tP1 (Pa): ...\tG (kg/s): ...\tMp (kg): ...`
  - `event/progress` `{job, value, label}` (0..1).
  - `event/job_done` `{job, status:"ok"|"cancelled"|"error"}`.
- Parada: masa < 0.1 %, P1 fuera de `[P1_min,P1_max]`, divergencia `|ΔP1|>1e6` (mensajes finales idénticos).
- Cancelación: `request.cancel {id}` → responde error 1005 y emite `job_done status=cancelled`.

### 3.7 nozzle (T2)

| Método | Params | Result |
|---|---|---|
| `nozzle.load_engine` | `{path}` | `{inputs, n_samples, p1_min, p1_max, p_curve:{t:[...],P:[...]}, nozzleConfig}` |
| `nozzle.calculate` | `{engine, nozzleType, p1, n, spec:{<claves de labels>}}` | ver abajo |
| `nozzle.op_point` | `{engine, nozzleType, p1, p1t, p0, n, dt, defCheck, spec}` | `{F, Pe, PR, ratios:{PR0,PR1,PR2,PR3,p0_p1,pe_p1,pe_p0}, regime, nozzleType, curves:{x,mach,pr}}` — `p1` es la presión de diseño con la que se construye la tobera (igual que `front_nozDes`); `p1t`/`p0` son el punto de operación (R8) |
| `nozzle.save` | `{name, payload}` | `{path}` — `Nozzles/<name>.json`, claves de `BN1.json`, typo `"DP. Thrust (kg)1"` **normalizado** (R10/T2-9) |
| `nozzle.load` | `{path}` | `{payload}` |

`nozzle.calculate` devuelve:
```
{
  "calculatedResults": {<17 etiquetas idénticas a calculated_results>, "PR_Crit0..3": ...},
  "geometry_data": {"X (m)":[...], "Y (m)":[...], "AR (m)":[...]},
  "timeResults_data": {"Time (s)":[...], "Thrust (kg)":[...], "CF":[...]},
  "figures": {"geometry":b64,"mach":b64,"pres":b64,"thrust":b64,"cf":b64},
  "payload": { "Inputs": {NozzleConfig, DefaultCheck, P1, n, EngineConfig, specInputs}, ... }
}
```
- Eventos `event/progress {job, value}` (paso i/n), `event/job_done`.
- Cancelable (T2-5). Divergencias de `fsolve` → error 1006 con etiqueta que las identifique.
- `nozzle.load_engine` con JSON ilegible → error 1003 `"Invalid file."`.

### 3.8 cad (T3)

| Método | Params | Result |
|---|---|---|
| `cad.load_nozzle` | `{path}` o `{config}` (payload) | `{config, architecture:"conventional"\|"as-nozzle", fields:[{key,label,type,options?,default}], checks:[...], suggested:{...}, message?}` |
| `cad.views` | `{config, settings:{...12 entries/12 checks...}, type:"Fitted"\|"Bulk"}` | `{views:{engine,coverFront,nozzleFront,tools,toolMould,toolMouldFix}}` (b64) |
| `cad.export` | `{kind:"engine"\|"cover"\|"tools", config, settings, overwrite?:bool}` | `{path, written:[...]}` — error 1004 si existe y `overwrite!=true` |

`cad.export` reproduce la cabecera `Sketch,Plane,x,y,z`, planos `XY`/`YZ`, escala ×100 y redondeos del original.

### 3.9 testbed (T4)

| Método | Params | Result |
|---|---|---|
| `testbed.list_ports` | `{}` | `{ports:[{device,description}]}` |
| `testbed.monitor_ports` | `{enabled}` | `{ok}` + `event/ports` cada 1 s mientras esté activo |
| `testbed.run` | `{nozzleFile}` | `{testFile, nozzle, engine, maxThrust, maxTemp}` — crea `Tests/<nozzle>-<HH.MM.SS-DD.MM.yy>.csv` con cabecera `t(s),F(kg),T(K)` |
| `testbed.connect_com` | `{port}` | `{connected:true}` (115200, timeout 1 s; envía `RESET`) |
| `testbed.disconnect` | `{}` | `{connected:false}` |
| `testbed.connect_wifi` | `{ssid, password}` | `{sent:true}` — comando `CONNECT <ssid> <password>` |
| `testbed.abort` | `{}` | `{ok}` — `ABORT` + `RESET` |
| `testbed.checklist.load` | `{}` | `{title, items:[{text,done}]}` — lee `<workdir>/checklist.json` |
| `testbed.checklist.toggle` | `{index}` | `{items, complete}` — al completar envía `SWITCH START-RECORDING-LED` |
| `testbed.state` | `{}` | `{connected, wifiReady, recording, checklistComplete, leds:{serial,wifi}}` |
| `testbed.mock` | `{enabled:bool, script?:[str], demo?:bool}` | `{ok}` — transporte simulado para tests/CI (R6). Sin `demo`, las líneas de datos se guardan en búfer y `testbed.run` las reproduce de forma determinista (eventos `record` y CSV); con `demo:true` se emiten en vivo para la demo interactiva |

Eventos: `event/serial_line {line}`, `event/record {t,F,T}`, `event/state {...}`, `event/ports {ports}`,
`event/job_done {job:"testbed"}`, `event/log {level, message}`.

Máquina de estados (idéntica a `front_test.read_serial_data`):
- `SERIAL STARTED` → limpia monitor, LED serial verde.
- `TEST-BENCH CONNECTED` → habilita checklist y LED wifi verde.
- `RESET` → habilita opciones WiFi.
- `ABORT` → aborta el test.
- Línea `t(s): x F(kg): y T(K): z` → dedupe (no repetir consecutivos idénticos) + append CSV + gauge.

### 3.10 Eventos transversales

| Evento | Payload |
|---|---|
| `ready` | `{version, pid}` |
| `console` | `{job, line}` |
| `progress` | `{job, value, label?}` |
| `job_done` | `{job, status, error?}` |
| `log` | `{level, message}` |
| `serial_line` | `{line}` |
| `record` | `{t, F, T}` |
| `state` | `{...}` |
| `ports` | `{ports}` |
| `exiting` | `{}` |

## 4. Reglas de paridad

1. Los códigos numéricos se migran literalmente desde `legacy/back_modules` (mismo algoritmo, mismas
   semillas de `fsolve`, mismas tolerancias). Toda divergencia debe justificarse en `tests/defects/DEF-*.md`.
2. Los ficheros exportados (`Engines/*.json`, `Nozzles/*.json`, CSV CAD, CSV Tests) son **byte-compatibles**
   salvo las normalizaciones documentadas (typo `DP. Thrust (kg)1`, `Sketch,Plane`).
3. La consola del T1 muestra las mismas líneas que el original (formato `:.{decimals}f`, `:10.3e`).
4. `front_*` no se porta: la lógica de UI se reimplementa en React; la lógica de orquestación se mueve a
   `engine/openred_engine/services/*`.
