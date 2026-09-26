# PLAN_MIGRACION_ESCRITORIO.md — OpenRED: clon nativo de escritorio (Rust + Python portable)

> Estado de la auditoría: **inspección directa del repositorio completada**. Este documento se basa en la lectura del código fuente real de `C:\Users\marco\Documents\.dev\OpenRED` (HEAD `c2250d0`, origen `https://github.com/marcosflz/OpenRED.git`).
>
> **Limitación declarada:** en este entorno la ejecución de Python no está disponible (el `venv\pyvenv.cfg` apunta a `C:\Users\marco\AppData\Local\Programs\Python\Python312\python.exe`, que no existe; `python --version` falla). Por tanto **no se ha podido ejecutar la aplicación ni producir resultados de ejecución**. Todo lo marcado ✅ está verificado leyendo código, configuración y ficheros de datos; lo marcado ⚠️ está inferido y necesita verificación durante la ejecución del plan. No se ha ejecutado ninguna prueba; no se afirma que nada del clon esté implementado.

---

## 1. Auditoría del proyecto actual

### 1.1 Qué es el proyecto

OpenRED es una aplicación de escritorio **Python 3.12.4 + CustomTkinter/Tkinter** para el diseño de motores cohete de propelente sólido (equipos universitarios). GPL‑v3 (`LICENSE`, 35 KB). Windows‑only en la práctica (rutas con `\`, `icon.ico`, COM, Inno Setup).

Distribución actual: PyInstaller onefile (`app.spec` → `dist\app.exe`, 72 MB) + instalador Inno Setup (`inno\setup.iss`, `setup.exe` 73,5 MB). El README documenta un defecto conocido: `database.db` se escribe junto al ejecutable y falla bajo `C:\Program Files` por permisos.

### 1.2 Inventario de ficheros verificados ✅

```
app.py                    27,8 KB   Arranque, menús, gestión de ventanas, save/load de config.json
functions.py              27,4 KB   Utilidades compartidas + matemáticas + DB + loader de plugins
imports.py                 1,1 KB   Barril de imports (numpy, scipy, tkinter, ctk, PIL, serial, mpl…)
requirements.txt             61 B   tk, customtkinter, Pillow, matplotlib, scipy, numpy, pyserial
app.spec                          PyInstaller: entry app.py; datas: icon.ico, functions.py, imports.py
inno/setup.iss                    AppId {909DBF9A-CFC1-4731-8551-A202262F8B46}, v0.1, {autopf}\OpenRED
database.db               16,4 KB   SQLite (2 tablas); contenido inspeccionado por strings binarios
temp_dir.txt                     Ruta del último directorio de trabajo (se borra al salir)
themes/red.json, orange.json      Temas CTk (por defecto red.json, cargado en app.py:489)
workingDirectory/                 Ejemplo real de directorio de trabajo del usuario
back_modules/  front_modules/     Código principal (ver §1.3–1.4)
build/ dist/                      Artefactos PyInstaller previos
inno/setup.exe                    Instalador generado previo
venv/                             venv roto en esta máquina (dependencias sí registradas)
```

Versiones fijadas en `venv\Lib\site-packages` ✅: numpy 2.1.2, scipy 1.14.1, matplotlib 3.9.2, customtkinter 5.2.2, Pillow 10.4.0, pyserial 3.5, PyInstaller 6.10.0. El requisito `tk` de `requirements.txt` corresponde al paquete dummy `tk 0.1.0`.

### 1.3 Arquitectura actual

- **Shell** (`app.py`): `main()` crea `ctk.CTk` 1920×1080 con menú nativo Tk (`File / Preferences / Database`, `app.py:478-523`) y panel izquierdo de botones que conmuta 8 pestañas (`change_tab`, `app.py:581-588`). Instancia módulos como singletons globales (`*_module_instance`).
- **Front** (`front_modules/`): 10 módulos; cada uno es una clase que construye su UI dentro de un `CTkFrame` recibido. Mezclan UI, control de flujo, hilos y acceso a datos.
- **Back** (`back_modules/`): cálculo puro pero acoplado a la GUI vía `messagebox`, `CTkTextbox` y `temp_dir.txt`/`database.db` relativos al CWD.
- **Plugins por importación dinámica** (`functions.py: importLibraries`, línea 687): escanea `back_modules/GrainLibrary` y `back_modules/NozzleLibrary`, importa cada `.py` y registra las clases que tengan atributo de clase `nozzle_type`. Es el mecanismo de extensión real del proyecto (README: "users can make their own grain geometry module / nozzle solvers").

### 1.4 Módulos y funcionalidades (verificado en código ✅)

| Módulo / clase | Fichero | Funcionalidad |
|---|---|---|
| `AdiabaticTempModule` | `front_modules/front_adTemp.py` (554 lín.) | Temperatura adiabática de llama: filas dinámicas reactivos/productos (moles + combobox desde DB), render de la reacción como figura matplotlib con LaTeX y auto‑ajuste de fuente (`update_reaction_label`, l.404), cálculo (`calculate`→`adiabaticTemp_calc`), 7 campos de resultado, guardado de propelente en DB (`save_propellant`, l.273), tabla `propelente`, reasignación de IDs (`reassign_ids`) |
| `PolynomialCp`, `adiabaticTemp_calc` | `back_modules/back_0.py` | Cp NASA (rango frío/caliente) desde `termoquimica`; balance de calor integrado trapecio + Newton‑Raphson (`functions.newtonRaph`); devuelve T_ad, M, cp, cv, R, gamma, c* |
| `PropellantDesignModule` | `front_modules/front_propDes.py` (677 lín.) | Diseño de motor: selector de propelente (refresco en hover), selector de geometría de grano (plugins), inputs dinámicos por grano, 7 inputs comunes (P0, Rt, Rc, Lc, dt, dh, ItMax); sub‑pestañas GEOMETRY (plot vivo), CONSOLE (consola + calcular + exportar), REGRESSION (figura de contornos); simulación en hilo (`calculate_n_show` l.472, `run_simulation` l.485, polling `check_simulation_thread` l.508); salida DATA (8 métricas + tabla) y GRAPHS (3 plots); `export_results` escribe JSON de motor |
| `PropellantRegresionLSM` | `back_modules/back_1.py` (335 lín.) | Regresión de quemado por Level‑Set: presión implícita con `scipy.fsolve` (`update_p`), avance de frente (`update_front`), longitud de frente por BFS sobre máscara (`get_area_vol`), condiciones de parada (masa<0.1%, presión fuera de rango, divergencia) con escritura directa en `CTkTextbox` desde el hilo de cálculo (`run(textbox)`, l.217) |
| Plugins de grano | `back_modules/GrainLibrary/TUBULAR.py` (`Tubular`, `nozzle_type="Tubular-Grain"`), `SQUARE.py` | `getPhi()` nivel‑set inicial, `plotGeometry()`, `sketchCAD()`. **Nota:** `SQUARE.py` define solo una función (`initialize_level_set_square`) y **no** clase con `nozzle_type` → no aparece en la UI (código muerto hoy) |
| `NozzleDesignModule` | `front_modules/front_nozDes.py` (1217 lín.) | Diseño de tobera: carga de motor JSON (`get_engine_data` l.748), switch+slider de P1 (valor medio / punto de diseño con validación min‑max), nº de puntos, paso temporal de normalización, menú de tipos de tobera con inputs dinámicos; plot de perfil de presión con punto seleccionado; CALCULATE con **ventana de progreso cancelable** (`create_progress_window` l.436, bucle por pasos con `after(1, …)` l.367); resultados numéricos dinámicos (17 etiquetas), ratios críticos y clasificación de régimen (`updateMapPlots` l.522: Subsonic / Normal Shock Inside / Normal Shock Exit / Over‑Expanded / Design‑Point / Under‑Expanded); sliders off‑design P1t/P0 que recalculan mapas de presión y Mach en vivo; tablas TIME RESULTS y GEOMETRY; `export_results` JSON |
| `ConeNozzle` (`CONE-LN`) | `back_modules/NozzleLibrary/LAVAL_CONE.py` (572 lín.) | Tobera cónica: garganta arc (`f_throat`), cono (`f_Cone`), relaciones A/M (`f_AR` resuelta con `fsolve`), curvas de presión sub/sup, choque normal interno/salida (`inShockOperation` con búsqueda iterativa de x del choque), `run_step` por instante, `calculated_results` (17 valores), plots (geom, mach, pres, thrust, CF). **Etiqueta con typo verificado:** `"DP. Thrust (kg)1"` (línea 18) |
| `BellNozzle` (`TOPN-BN`) | `back_modules/NozzleLibrary/TOPBN.py` (466 lín. aprox., misma estructura) | Bell (Rao simplificado): misma API; `f_bell`, parámetros extra `theta_e`, `% L. Cono` |
| `EngineCADModule` | `front_modules/front_cad.py` (393 lín.) | CAD para Fusion360: carga tobera JSON, construye dinámicamente 12 entries + 12 checkboxes + 1 menú `type` (Fitted/Bulk) según `entriesLabelsDic` (l.199‑225); 6 vistas matplotlib (Engine, CoverFront, NozzleFront, Tools, ToolMould, ToolMouldFix); export CSV Engine/Cover/Tools a `Sketches/` con confirmación de sobrescritura y escala ×100 |
| `EngineCADBuilder_ConventionalNozzle` | `back_modules/back_2.py` (721 lín.) | Generación de geometría 2D del conjunto motor (cartucho, pared, tornillos, cubierta, moldes, tuerca) a partir de engine+nozzle JSON; `export_engine/cover/tools` escriben CSV multi‑sketch (columnas `Sketch,Plane,x,y,z`, planos XY/YZ) |
| `TestingBedModule` | `front_modules/front_test.py` (824 lín.) | Banco de pruebas: Run (elige nozzle JSON en `Nozzles/`, lee engine asociado, maxThrust/maxTemp, crea `Tests/<nozzle>-<HH.MM.SS-DD.MM.yy>.csv` con cabecera `t(s),F(kg),T(K)`), puertos COM (listado + hilo monitor 1 s, `monitor_ports` l.511), conexión serial 115200 (`connect_com` l.532) con comando `RESET`, monitor serial en textbox (`read_serial_data` l.684) con detección de `"SERIAL STARTED"`, `"TEST-BENCH CONNECTED"`, `"RESET"`, `"ABORT"`; WiFi: envío `CONNECT <ssid> <password>` (l.769); checklist dinámica desde `checklist.json` (`create_checklist` l.345) que al completarse envía `SWITCH START-RECORDING-LED`; parseo de líneas con regex (`functions.getSerialValues` l.664), dedupe, appendo a CSV y plots/gauges en vivo (`gaugePlot` l.575: THRUST, TEMPERATURE, BATTERY, WATER — batería y agua fijas a 1/1); Abort (`ABORT`+`RESET`); comandos LED `SERIAL_GREEN/BLUE`, `WIFI_GREEN/BLUE`; cierre azul+RESET |
| `TermoquimicaWindow` | `front_modules/front_chemWin.py` (296 lín.) | Ventana CRUD de `termoquimica` (17 columnas): combobox por ID, relleno de campos, validación científica con reemplazo coma→punto y aviso, Add/Edit/Delete, reasignación de IDs, singleton por clase (`instance`) |
| `PropellantWindow` | `front_modules/front_propWin.py` (479 lín.) | Ventana CRUD de `propelente` (13 columnas) + curva de velocidad de quemado `r=a·P^n` (ventana emergente con PNG de matplotlib vía `PIL`) |
| Placeholders | `front_doc.py`, `front_cfd.py`, `front_post.py` | Pestañas **Documentation**, **OpenFOAM Maker**, **Post-Processing**: solo un label "Soon" |

### 1.5 Utilidades compartidas (`functions.py`) ✅

`get_data(type,file)` (lee `temp_dir.txt` para componer `<dir>\<type>\<file>`), `get_entry_value` (vacío→"0"), `validate_scientific_notation` (regex), `get_database_components`, `get_propellant_value(column, name)` (SQL con f‑string de columna — inyección controlada por lista cerrada), `convert_to_latex`, `save_dir_path/get_dir_path/clear_dir_path` (ciclo de vida de `temp_dir.txt`), `newtonRaph` (derivada numérica; **lanza `messagebox`**), `integration` (trapecio), `discreteIntegration`, `initialize_database` (DDL), `insert_fig` (empotrable de Figure en frame con modos Manual/Auto), `TempSchemes.Euler/Heun/RK4`, `numerical_derivative`, `solve_ode_system` (con `messagebox`), `getSerialValues` (regex `t\(s\):\s*… F\(kg\)… T\(K\)…`), `importLibraries`, `get_circle_points`.

### 1.6 Persistencia y formatos ✅

- **`database.db` (SQLite, relativo al CWD):** tablas `termoquimica` (`id, Component, MolWeight, Hf0, minColdTemp, maxColdTemp, minHotTemp, maxHotTemp, a1..a5_cold, a1..a5_hot`) y `propelente` (`id, Propelente, T_ad, MolWeight, Cp, Cv, R, gamma, cChar, Density, P1_min, P1_max, a, n`). DDL en `functions.initialize_database`. Datos de ejemplo verificados por strings binarios: `C12H22O11 (Solid/Liquid)`, `KNO3 (S)`, `KOH (L/G/S)`, `K2CO3 (S/L)`, `O2`, `CO2`, `CO`, `H2O`, `H2`, `N2`; propelentes `KNSU`, `KNSU2`, `KNSL`. Reasignación de IDs secuenciales tras cada operación (quirk a conservar).
- **Directorio de trabajo** (elegido por el usuario con `filedialog.askdirectory`; `temp_dir.txt` guarda la ruta y se **borra al salir**): `Engines/*.json`, `Nozzles/*.json`, `Sketches/*.csv`, `Tests/*.csv`, `checklist.json` (`{"Checklist": [...]}`), `config.json`.
- **`config.json`** (estructura exacta verificada en `workingDirectory/config.json`): `{"tabs": {"tab_0": {reactivos[[mole,name]…], productos[…], initial_temp, temp_Int_step, temp_guess}, "tab_1": {propellant, geoConfig, P0, Rt, Rc, Lc, dt, dh, ItMax, `<grain>_<entry>`…}, "tab_2": {engine_config, SwitchState, P1, n_res, nozzle_type, `<nozzle>_<entry>`…}, "tab_3": {NozzleConfig, type, n_conv, …, on_*}}}`. **Todos los valores numéricos se guardan como cadenas.** `open_on_saving_directory` rechaza carpetas que ya tengan `config.json`.
- **Engine JSON** (`front_propDes.export_results`): `{"inputs": {Propellant, GrainGeo, CADx[], CADy[], CAD0[], + specInputs (P0, Rt, R2, Lc, dt, dh, It, a, n, R, T1, cChar, rho_b, P1_min, P1_max, …)}, "results": {meanPressure, maxPressure, minPressure, meanMassFlow, maxMassFlow, minMassFlow, totalTime, totalMass, "tree_data": {"Time (s)", "Pressure (Pa)", "Mass Flow (kg/s)", "Mass (kg)"}}}`. Ejemplo real: `workingDirectory/Engines/KNSU-32-RT65.json` (59 KB).
- **Nozzle JSON** (`front_nozDes.export_results`): `{"Inputs": {NozzleConfig, DefaultCheck, P1, n, EngineConfig, specInputs}, "geometry_data": {"X (m)", "Y (m)", "AR (m)"}, "timeResults_data": {"Time (s)", "Thrust (kg)", "CF"}, "calculatedResults": {<17 etiquetas> + PR_Crit0..3}}`. Ejemplo real: `workingDirectory/Nozzles/BN1.json` (27,9 KB).
- **CAD CSV:** cabecera `Sketch,Plane,x,y,z`, planos `XY`/`YZ`, coordenadas ×100 (metros→cm). ⚠️ El ejemplo real `Sketches/BN1_ENGINE_CAD.csv` tiene cabecera `Sketch,Type,x,y,z` (build antiguo) — el código actual escribe `Plane`.
- **Tests CSV:** cabecera `t(s),F(kg),T(K)` + filas `0.025,0.049,301.4` (ejemplos reales en `Tests/`).

### 1.7 Integraciones externas y red ✅

- **Serial (pyserial):** listado de puertos (`serial.tools.list_ports`), 115200 baudios, timeout 1 s. Protocolo ESP32 (comandos `\n`-terminados): `RESET`, `ABORT`, `SERIAL_GREEN`, `SERIAL_BLUE`, `WIFI_GREEN`, `WIFI_BLUE`, `SWITCH START-RECORDING-LED`, `CONNECT <ssid> <password>`. Marcadores de entrada: `SERIAL STARTED` (reset monitor + LED verde), `TEST-BENCH CONNECTED` (habilita checklist + LED WiFi verde), `RESET` (habilita WiFi), `ABORT` (aborta). Las credenciales WiFi viajan **en claro** por el puerto serial (limitación heredada del firmware ESP32, no de la app).
- **Matplotlib embebido:** todas las figuras van a frames Tk vía `FigureCanvasTkAgg`; reacción con texto LaTeX en la figura.
- Sin red propia más allá del puente serial→ESP32→WiFi (la app no abre sockets).

### 1.8 Concurrencia y defectos observados en el código ✅

1. `front_propDes.run_simulation` escribe en `CTkTextbox` (`console_box`) desde un hilo worker (violación de Tcl; funciona por accidente en Windows).
2. `functions.newtonRaph` y `solve_ode_system` muestran `messagebox` desde cualquier contexto (imposibilita uso headless/testable).
3. **`front_nozDes.export_results` usa atributos que nunca se asignan** (`self.engine_config`, `self.nozzle_config`, `self.defaultState`, `self.P1`, `self.n`, `self.specInputs`; grep sin resultados): el botón EXPORT de toberas lanza `AttributeError` en el estado actual del código. Los JSON existentes (`BN1.json`) provienen de una versión anterior. ⚠️ Inferencia: regresión introducida al refactorizar `calculate_n_show`. El clon implementará la exportación según la intención (claves de `BN1.json`).
4. `calculate_n_show` en toberas accede a `self.P/self.t` sin comprobar que se cargó un motor → excepción Tcl sin manejo (sin ventana de progreso colgada → la ventana de progreso queda abierta).
5. `importLibraries` usa `os.getcwd()` — si el CWD no es el del ejecutable, los plugins no se cargan (PyInstaller onefile fija el CWD al dir del exe, por eso funciona; es frágil).
6. `update_reaction_label` usa `self.latexMap` que solo existe tras añadir la primera fila — error potencial si se actualiza antes.
7. No hay tests en el proyecto (ningún `tests/`; verificado por glob fuera de `venv/`), no hay logging (solo `print`), no hay auto‑actualización, no hay recuperación tras fallo, `geometry` fija 1920×1080.
8. Los valores de `config.json` se restauran con `insert(0, valor)` en entries — sin validación de tipos.
9. `reassign_ids` reescribe todas las IDs de las tablas tras cada operación (comportamiento observable a conservar).

### 1.9 Distribución actual y sus problemas ✅

- `app.spec`: onefile, `console=False`, `icon=['icon.ico']`, UPX on; datas: `icon.ico`, `functions.py`, `imports.py` (⚠️ los módulos `front_modules`/`back_modules` **no** van dentro del exe: el instalador los copia como `.py` junto al exe — el exe los importa desde disco).
- `inno/setup.iss`: rutas absolutas del PC del autor (`D:\Documentos\VS_Code\TFM\source\...`, `LicenseFile=D:\Descargas\LICENSE.txt` → **el build del instalador no es reproducible desde este repo**). Instala en `{autopf}\OpenRED` con `database.db`+módulos junto al exe → origen del problema de permisos del README.

### 1.10 Tests y cobertura

- **Tests propios: 0** (verificado). Cobertura observable: nula. Todo el comportamiento de paridad se definirá desde fixtures reales (§6.2).

---

## 2. Arquitectura del clon

### 2.1 Decisiones (D#)

| # | Decisión | Justificación breve |
|---|---|---|
| D1 | **Shell de escritorio: Tauri 2.x (Rust) + frontend web (React 18 + TypeScript + Vite)** | Ventana nativa, binario pequeño (~10 MB), instaladores por SO (MSI/NSIS, DMG, AppImage/deb), **plugin updater** integrado, plugin single‑instance y dialogs. Se descarta reutilizar CustomTkinter (impide UI nativa moderna, arrastra Tcl/Tk, y no hay “clon nativo” sin rehacer la capa visual); se descarta Electron (peso) y egui puro (menor productividad para 8 pestañas densas y no da updater/instaladores hechos). |
| D2 | **Motor de cálculo: Python conservado** como proceso sidecar headless (`openred_engine`) que **reutiliza** `back_modules/back_0/1/2`, `GrainLibrary`, `NozzleLibrary` y la parte matemática de `functions.py` | Reescribir en Rust termodinámica + Level‑Set + aero de toberas + generador CAD duplicaría ~1.600 líneas numéricas ya validadas por uso real (fixtures existentes) y arriesgaría paridad numérica. Python aporta numpy/scipy/mpl ya probados. **Rust solo donde gana:** ciclo de vida de procesos, IPC, IO serial nativo opcional, updater, instalación, logging. |
| D3 | **Interfaz Python↔Rust↔UI: JSON‑RPC 2.0 sobre stdio (JSONL)** del sidecar; Rust hace de router hacia el webview (comandos Tauri + eventos). Contratos en JSON Schema (única fuente) → tipos TS y modelos Pydantic generados | Simple, portable, sin sockets locales abiertos (superficie mínima), trivialmente testeable headless, y soporta streaming de eventos (progreso, serial) por la misma tubería. |
| D4 | **Figuras: matplotlib en el sidecar renderiza PNG (base64) en fase 1**; gauges y gráficas en vivo del Test Bed se dibujan nativamente en canvas (ECharts) en fase 2 | Paridad exacta de figuras de ingeniería (contornos LSM, mapas de tobera, croquis CAD) con esfuerzo mínimo; latencia de PNG (~50‑150 ms) es aceptable para figuras de análisis. |
| D5 | **Serial (Test Bed) en Python (pyserial) dentro del sidecar** con abstracción `Transport` | El protocolo ESP32 está entrelazado con la grabación de datos y la checklist; moverlo a Rust duplicaría lógica. pyserial ya funciona en los 3 SO. Mitigación del riesgo: tests con transporte simulado + prueba de hardware separada. |
| D6 | **Base de datos: se mantiene SQLite con el mismo esquema** vía `sqlite3` (stdlib) tras una capa DAO; mutable **siempre** en un directorio de datos del usuario, nunca en Program Files | Elimina el defecto conocido de permisos sin tocar el formato (paridad de datos 100%); `sqlite3` es stdlib (cero dependencias). Migración a JSON queda como fase opcional futura (README ya la anticipa). |
| D7 | **Sustitución de Tk/CustomTkinter/Pillow‑UI:** el runtime Python embebido **excluye tkinter**; backend de matplotlib forzado a `Agg`; `Pillow` se conserva solo como dependencia transitiva de matplotlib | Reduce ~40‑60 MB y elimina toda la frágil integración Tk en hilos. `imports.py` no se reutiliza; `front_modules` no se portan (la UI se rehace en React). |
| D8 | **scipy se conserva en fase 1** (paridad de `fsolve`/`interp1d`); eliminación de scipy vía `newtonRaph` propio + `np.interp` queda como optimización opcional fase 3 con suite de paridad como guard | scipy son ~110 MB sin comprimir; se sacrifica primero paridad y luego tamaño, no al revés. |
| D9 | **SO objetivo:** Windows 10/11 x64 (paridad 1:1 con hoy, MSI+NSIS), macOS 13+ arm64/x64 (DMG) y Linux x64 (AppImage/deb) como objetivos secundarios | El proyecto es Windows‑only hoy; Tauri y python-build-standalone cubren los tres. Las diferencias de serial (`/dev/ttyUSB*`) y firmas de macOS quedan en riesgos. |
| D10 | **Datos mutables fuera de la carpeta de instalación:** `%APPDATA%\OpenRED` (o XDG) para DB, logs, cache matplotlib, config de app; el “directorio de trabajo” del usuario sigue siendo un folder elegible igual que hoy (con `config.json`) | Paridad funcional del concepto “working directory” + soluciona el bug de Program Files. |

### 2.2 Vista de componentes

```
┌────────────────────────────────────────────────────────────────────┐
│ Tauri 2 (Rust)  apps/desktop/src-tauri                             │
│  • Ventana/webview, icono, single-instance                          │
│  • Supervisor del sidecar (spawn, restart con backoff, kill on exit)│
│  • Router JSON-RPC  request→sidecar / sidecar→event→webview         │
│  • Comandos: diálogos, paths (data_dir), updater, logs              │
│  • tracing → %APPDATA%\OpenRED\logs\openred.log (rotación)          │
└───────────┬───────────────────────────────────▲────────────────────┘
            │ stdio JSON-RPC (JSONL)            │ eventos (progress/serial/log)
┌───────────▼───────────────────────────────────┴────────────────────┐
│ openred_engine  (Python 3.12 embebido, headless)                    │
│  rpc.py (dispatcher) · services/{adiabatic,engine,nozzle,cad,       │
│  workspace,testbed,db}.py · modules/{back_0,back_1,back_2}.py       │
│  plugins/{GrainLibrary,NozzleLibrary} · store.py (SQLite DAO)       │
│  matplotlib(Agg)→PNG · pyserial + Transport (mock en tests)         │
└────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────┐
│ Frontend React/TS  apps/desktop/src                                  │
│  Layout: sidebar 8 pestañas + menú (File/Preferences/Database)       │
│  Módulos por pestaña (§5) · render de figuras PNG · KaTeX reacción   │
│  Charts nativos para Test Bed · estado de config.json vía workspace  │
└────────────────────────────────────────────────────────────────────┘
```

### 2.3 Contrato IPC (borrador normativo, se congela en M0)

- **Transporte:** stdio del proceso `python.exe -s -X utf8 -m openred_engine`; una línea JSON por mensaje (`\n` escapado). Requests `{id, method, params}`, respuestas `{id, result|error}`, notificaciones de eventos `{method:"event/<name>", params}`.
- **Métodos previstos** (≈30): `workspace.open_dir`, `workspace.save_config`, `workspace.load_config`, `workspace.pick_dir/file` (delegan a diálogo de Rust), `db.components.{list,add,edit,delete}`, `db.propellants.{list,add,edit,delete,burning_rate}`, `adiabatic.calculate`, `engine.calculate` (streaming `event/progress` + `event/console`), `engine.save`, `nozzle.load_engine`, `nozzle.calculate` (streaming + cancelable), `nozzle.op_point` (P1t,P0 → F,Pe,PR,tipo de régimen), `cad.load_nozzle`, `cad.update_views`, `cad.export.{engine,cover,tools}`, `testbed.{run,connect_com,disconnect,connect_wifi,abort,list_ports,enable_checklist}` + `event/serial_line`, `event/record`, `app.shutdown`.
- **Cancelación:** `request.cancel {id}` → el sidecar aborta el cálculo en curso (equivalente funcional a cerrar la ventana de progreso en `on_progress_window_close`).
- **Imágenes:** `{mime:"image/png", data_b64}` en las respuestas de figuras.
- Contratos: `contracts/schemas/*.json` (JSON Schema draft 2020-12) + fixtures en `contracts/fixtures/`.

### 2.4 Ciclo de vida, errores, logs y tareas en segundo plano

- Arranque: Tauri valida recursos (hash del runtime Python), lanza sidecar, espera `event/ready` (timeout 10 s → pantall de error con logs). Al cerrar la app: `app.shutdown` → drain → kill; si el sidecar muere: 1 reinicio automático + aviso al usuario; el estado de UI sobrevive (config.json).
- Todo cálculo pesado vive en el sidecar (hilos internos propios); el webview nunca bloquea. Los eventos de progreso sustituyen a los bucles `after()` de `front_propDes`/`front_nozDes`.
- Logging: Rust `tracing` + Python `logging` (JSON por línea por stdio también) → fichero rotado; visor "Help > Logs" (carpeta). Los `print` actuales se convierten en eventos de log.
- Errores de dominio: JSON‑RPC `error{code, message, detail}`; equivalencia de los `messagebox` actuales (p. ej. "Invalid file.", "A configuration file already exists…") mapeada a diálogos/UI (ver matriz §5).
- Escritura atómica de JSON/CSV (tmp+rename) y snapshot de `database.db` antes de operaciones de escritura.

### 2.5 Seguridad, permisos y credenciales

- Sin sockets abiertos; IPC por stdio local; validación estricta de params contra schemas; rutas de lectura/escritura restringidas a: directorio de trabajo elegido por el usuario, carpeta de recursos (solo lectura) y carpeta de datos del usuario.
- La contraseña WiFi del banco va por serial en claro **por diseño del firmware** — se mantiene (paridad) y se documenta en la UI; no se almacena en disco (hoy no se guarda: verificado, `front_test.connect_wifi` no persiste nada).
- No hay credenciales en repos ni cifrado adicional requerido; `database.db` y ficheros JSON de trabajo son del usuario.
- Binario firmado (Windows: certificado OV o Azure Trusted Signing; macOS: ad‑hoc hasta disponer de Developer ID — declarado pendiente) y `tauri-plugin-updater` con firmas minisign.

---

## 3. Python portable y distribución

### 3.1 Fuente del intérprete y empaquetado

- **python-build-standalone (astral-sh)**, release fijado por tag en `tools/python.lock` (p. ej. `cpython-3.12.11+20250915`), sabores: `x86_64-pc-windows-msvc-shared-install_only`, `aarch64-apple-darwin-install_only`, `x86_64-unknown-linux-gnu-install_only`. Download con checksum verificado en CI.
- Dependencias instaladas **en build time** con `pip install -r engine/requirements-core.txt --target <pkg>/site-packages --only-binary :all:` y **lockfile** (`requirements-core.lock` generado con `uv pip compile` sobre Python 3.12): `numpy==2.1.2, scipy==1.14.1, matplotlib==3.9.2, pyserial==3.5` (+ deps transitivas wheels: contourpy, cycler, kiwisolver, pillow, pyparsing, python-dateutil, six). **Excluidas:** `customtkinter`, `tk`, `darkdetect`, PyInstaller.
- Se exigen wheels para evitar toolchains nativos en CI; todo el set existe para win/mac/linux x64+arm64.

### 3.2 Estructura del paquete instalado (Windows; equivalente en mac/linux)

```
<install_dir>/OpenRED/
├── OpenRED.exe                 # binario Tauri (shell)
├── engine/                     # recursos Python (solo lectura)
│   ├── python/                 # CPython 3.12 (python.exe, python312.dll, Lib/ stdlib)
│   │   └── site-packages/      # wheels preinstalados (numpy, scipy, matplotlib, serial…)
│   ├── openred_engine/         # código del sidecar (módulos .py)
│   │   ├── plugins/GrainLibrary/… plugins/NozzleLibrary/…
│   └── engine.lock             # hashes SHA-256 de los ficheros (integridad)
├── resources/  (icon.ico, assets frontend, LICENSES/, LICENSE(GPLv3))
└── (instalador MSI/NSIS creado por tauri bundler)
```

Datos mutables: `%APPDATA%\OpenRED\{database.db (migrada), logs/, mpl-data/, config/}`. El “working directory” lo elige el usuario como hoy (por defecto `Documents\OpenRED`).

### 3.3 Aislamiento y resolución de rutas

- Lanzamiento desde Rust con env: `PYTHONNOUSERSITE=1`, `PYTHONUTF8=1`, `MPLBACKEND=Agg`, `MPLCONFIGDIR=<data>\mpl-data`, `OPENRED_DATA_DIR=<data>`, `OPENRED_RESOURCE_DIR=<install>\engine`, `OPENRED_WORKDIR=<directorio de trabajo>` y args `["-s", "-X", "utf8", "-m", "openred_engine"]`. **No se usan `-I`/`-E`** (anularían `PYTHONPATH`/env que necesitamos para apuntar a `site-packages`); el aislamiento se logra con `-s` + `PYTHONNOUSERSITE` + layout interno (el `python.exe` de install_only localiza su stdlib relativa a sí mismo). Verificación obligatoria en máquina limpia (§6.6).
- `engine/openred_engine/paths.py` centraliza: recursos (recursos de app), datos (APPDATA), trabajo (OPENRED_WORKDIR) y **elimina todos los usos de CWD relativo**: `get_data`, `get_engine_data` (NozzleLibrary), `create_checklist`, `run_test`, `initialize_database`, todas las conexiones `'database.db'` de `front_*`/`back_*`.
- `importLibraries` se reescribe para escanear `OPENRED_RESOURCE_DIR/plugins/<Lib>` (manteniendo el contrato `nozzle_type`/`get_input_labels` para que los plugins de usuario sigan funcionando).
- `sys.dont_write_bytecode` via `PYTHONDONTWRITEBYTECODE=1` (instalación en Program Files es read‑only).

### 3.4 Builds por plataforma

| Target | Runtime Python | Notas |
|---|---|---|
| Windows x64 (primario) | `x86_64-pc-windows-msvc-shared` | MSI (WiX) + NSIS; icono de `icon.ico`; upgrade de AppId nuevo (distinto del antiguo {909DBF9A…} para convivir o migrar — decisión en §6) |
| macOS arm64/x64 | `aarch64/x86_64-apple-darwin` | DMG sin firmar (ad‑hoc) fase 1; firma Developer ID pendiente |
| Linux x64 | `x86_64-unknown-linux-gnu` | AppImage + `.deb` (parches de paths respetando XDG) |

- **Tamaño estimado** (sin comprimir ~250‑290 MB; instalador ~110‑140 MB con LZMA): mitigaciones en §8.
- Licencias a distribuir: GPLv3 (app), PSF (CPython), BSD-3 (numpy, scipy, pyserial), matplotlib PSF‑based, Pillow HPND, DejaVu fonts (incluidas en matplotlib) → `resources/LICENSES/` generadas con `pip-licenses`.

### 3.5 Instalación, desinstalación, actualización

- **Instalación:** MSI/NSIS por usuario (por defecto, sin UAC) con opción por‑máquina; acceso directo opcional; asociación de archivos no requerida.
- **Desinstalación:** estándar del bundler; los datos de `%APPDATA%\OpenRED` se conservan (opción “borrar datos”).
- **Actualización:** `tauri-plugin-updater` contra `https://github.com/marcosflz/OpenRED-desktop/releases/latest/latest.json` (firmado). El sidecar se actualiza completo (intérprete+paquetes) porque vive dentro del paquete. Fallback manual (descarga). **No se inventa estado actual:** hoy el proyecto no tiene updater; es una función nueva documentada como tal.
- **CI/CD (GitHub Actions):**
  1. `engine-ci`: matrix (win/linux/mac) — `uv sync`/`pip check`, `pytest` con fixture workspace, `ruff`, build del sidecar zip + SBOM.
  2. `desktop-ci`: `cargo test`, `pnpm build && pnpm tauri build`, pruebas de la UI (vitest) + E2E `tauri-driver`.
  3. `parity`: ejecuta el **harness de paridad** (§6.2) original vs clon.
  4. `release`: build de los 3 SO, firma (Windows), manifest de updater, artefacto `OpenRED-<ver>-setup.(msi|exe)` + `portable.zip`.
  5. `clean-machine`: job con Python removido del PATH (`Remove-Path` de las entradas de Python; runner no sirve para “sin nada”, así que la prueba canónica se hace con **Windows Sandbox / VM** — ver §6.5) instalando el MSI y ejecutando el smoke test.

---

## 4. Paridad funcional y pruebas

### 4.1 Alcance de paridad

Paridad **funcional y de datos** (mismos entradas → mismos resultados/ficheros), **no pixel‑a‑píxel**. La UI se rediseña visualmente con los tokens de `themes/red.json` (color acento `#D03434`, modos dark/light, temas seleccionables). Los placeholders "Soon" (Documentation, OpenFOAM Maker, Post‑Processing) se mantienen como pantallas placeholder idénticas en función.

### 4.2 Matriz de paridad

Leyenda: **Resp.** = agente responsable (§7). Original = fichero:función. Acept. = criterio verificable.

**G. Globales / shell**

| ID | Funcionalidad | Original | Clon (previsto) | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| G1 | Ventana principal, título "OpenRED", icono | `app.py:463-466` | Ventana Tauri 1280×800 redimensionable, icono convertido | A3 | E2E | Abre, título e icono correctos |
| G2 | Menú File > Open (elegir dir trabajo + cargar config) | `open_directory` `app.py:33` | `workspace.open_dir` + carga `config.json` | A2/A4 | Integración+E2E | Los 4 tabs restauran valores exactos de `workingDirectory/config.json` |
| G3 | Menú File > Save (guardar config.json) | `save_configuration` `app.py:108` | ídem; JSON **estructura y valores‑cadena idénticos** | A2/A4 | Golden | `diff` semántico JSON == original con misma sesión |
| G4 | Diálogo si la carpeta ya tiene config.json al guardar | `open_on_saving_directory` `app.py:63` | error equivalente | A4 | E2E | Mensaje y no‑escritura |
| G5 | Salida: preguntar guardar, limpiar temp‑path, cerrar | `on_closing` `app.py:410` | `onCloseRequested` → prompt → save → shutdown sidecar | A2/A3 | E2E | Sin pérdida de datos; sidecar termina limpio |
| G6 | Modos dark/light | `app.py:509-510` | tokens CSS equivalentes | A3 | Visual | Conmuta y persiste en sesión |
| G7 | Temas red/orange (+ futuros `themes/*.json`) | `app.py:492-500, 489` | theme tokens JSON mismos colores clave | A3 | Unit | Paleta de red.json aplicada (accent #D03434…) |
| G8 | Database > Thermochemical Data (ventana) | `app.py:522`, `front_chemWin` | modal React | A4 | E2E | CRUD completo contra DB |
| G9 | Database > Propellants Data (ventana + curva quemado) | `app.py:523`, `front_propWin` | modal React + gráfica nativa | A4 | E2E | r=a·P^n sobre [P1_min,P1_max], 1000 pts |
| G10 | Singleton de ventanas DB ("already open") | `front_chemWin.py:13`, `front_propWin.py:12` | una instancia por ventana | A4 | E2E | Segunda apertura muestra aviso |
| G11 | Ciclo de vida `temp_dir.txt` (save/read/clear al salir) | `functions.py:164-214` | reemplazado por estado Rust+workspace; **sin fichero temp** (intención equivalente: recordar último dir) | A2 | Unit | Reabrir app recuerda último directorio |
| G12 | Placeholders Documentation/OpenFOAM/Post | 3 ficheros "Soon" | pantallas placeholder | A3 | E2E | Visibles y sin funcionalidad (igual que hoy) |

**T0. Temperatura adiabática**

| ID | Funcionalidad | Original | Clon | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| T0-1 | Añadir/quitar reactivo y producto (moles+componente) | `front_adTemp.py:442-523` | filas dinámicas | A4 | E2E | Mismo conjunto de componentes que DB |
| T0-2 | Render de reacción (LaTeX, auto‑fit) | `update_reaction_label` l.404 | KaTeX/MathJax (decisión de diseño) | A4 | E2E visual | Fórmula con subíndices correcta |
| T0-3 | Cálculo T_ad y 7 resultados | `back_0.adiabaticTemp_calc` | método sidecar idéntico (código migrado) | A1/A5 | **Golden numérico** | Δ rel ≤1e‑9 vs referencia en fixture KNSU (config.json tab_0) |
| T0-4 | Errores de entrada (moles no numéricos→0; hStep≤0) | `calculate` l.340, `back_0.py:105` | misma degradación + aviso | A1/A5 | Unit | hStep=0 → error "Invalid integration step value." |
| T0-5 | Guardar propelente en DB (13 campos) | `save_propellant` l.273 | mismo INSERT | A4/A1 | Integración | Fila persistida; IDs reasignados |
| T0-6 | Tabla propelente (14 col) refresco on‑hover | `populate_treeview`/`update_propellant_menu` | tabla virtualizada | A4/A5 | E2E | Refleja DB actualizada |

**T1. Diseño de motor**

| ID | Funcionalidad | Original | Clon | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| T1-1 | Plugins de grano (Tubular) con inputs dinámicos | `importLibraries`+`front_propDes:334-419` | mismos plugins, mismos labels | A1 | Unit | Labels `{"X  (m)":"cx_real","Y  (m)":"cy_real","R1 (m)":"r_in"}` |
| T1-2 | Plot de geometría vivo (focus‑out) | `update_plot` l.584 | render PNG en sub‑pestaña GEOMETRY | A5 | E2E | PNG contiene contorno círculo exterior+interior |
| T1-3 | Simulación LSM en hilo con consola en vivo | `calculate_n_show`+`back_1.run` | job streaming (`event/console`/`event/progress`), cancelable | A1/A5 | Integración+Golden | Líneas `Iter\t t(s)\t P1 (Pa)\t G (kg/s)\t Mp (kg)`; parada por masa<0.1%, rango P1, divergencia |
| T1-4 | Resultados DATA (8 métricas + tabla) | `update_results` l.518 | mismos cálculos (`np.mean/max/min[1:]`, `MP[0]`, `TIME[-1]`) | A5/A1 | Golden | Valores ≤1e‑6 rel vs fixture |
| T1-5 | GRAPHS presión/caudal/masa | `back_1.plot_*` | 3 figuras PNG | A5 | E2E | Renderizan con datos del run |
| T1-6 | Export engine JSON (+CADx/CADy/CAD0) | `export_results` l.611 | misma estructura exacta | A5/A1 | Golden | JSON diffs 0 vs original sobre fixture Tubular (KNSU‑32‑RT65 regenerado) |
| T1-7 | Sin dir de trabajo → error | l.613-616 | mismo aviso | A5 | E2E | Mensaje y no‑crash |
| T1-8 | ROUND‑TRIP: engine JSON → Nozzle Design/CAD | `get_engine_data`, `back_2` | misma lectura | A6/A7 | Integración | `BN1.json`+`KNSU-32-RT65.json` cargan y producen mismos números |

**T2. Diseño de tobera**

| ID | Funcionalidad | Original | Clon | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| T2-1 | Cargar engine JSON; label; range slider min/max | `get_engine_data` l.748 | misma lectura y validación "Invalid file." | A6 | Unit+E2E | JSON corrupto → error, label "Invalid File" |
| T2-2 | Switch P1 medio + slider + entry con validación rango | l.49-64, `update_from_entry` l.863 | mismos comportamientos | A6 | E2E | Valor fuera de [minP,maxP] → error |
| T2-3 | Tipos de tobera (CONE-LN, TOPN-BN) + inputs dinámicos | `importLibraries` | mismos 4/2 inputs (`TOP-BN_k`, `theta_t`, `theta_e`, `% L. Cono`) | A1/A6 | Unit | Clases cargadas con sus labels |
| T2-4 | Perfil de presión con punto marcado y ratio en leyenda | `update_plot` l.1073 | fig PNG equivalente | A6 | E2E | Punto rojo en P interpolado |
| T2-5 | CALCULATE con progreso **y cancelación** | `create_progress_window`+`run_calculations_step` l.367-433 | barra nativa + cancel | A6/A1 | E2E | Cancel a mitad → `calculation_running=False`, sin resultados parciales corruptos |
| T2-6 | Resultados: 17 numéricos + PR_Crit0..3 + régimen de operación | `calculated_results` (TOPBN/LAVAL) + `updateMapPlots` l.522 | idénticos | A1/A6 | **Golden numérico** | Δ rel ≤1e‑9 vs referencia (fixture `BN1.json` params de config tab_2); clasificación de régimen idéntica para 8 puntos barridos |
| T2-7 | Sliders off‑design en vivo (mapas P/Mach, ratios, empuje) | `updatePercentLabels`/`updateMapPlots` l.499-597 | interacción debounced→sidecar | A6/A1 | E2E | Mismos 4 ratios y etiqueta de régimen en 6 posiciones |
| T2-8 | Tablas TIME RESULTS / GEOMETRY | `_create_treeview_in_tab` l.710 | tablas nativas | A6 | E2E | Filas= n_res; formatos `.4e`/`.4f`/`.6f` |
| T2-9 | Export JSON de tobera | `export_results` l.1120 | **implementado correctamente** (bug #1.4.3 corregido): atributos tomados del cálculo real | A6 | Golden+Integración | JSON con las mismas claves que `BN1.json` (nota: typo `DP. Thrust (kg)1` normalizado; delta documentada) |
| T2-10 | Protección: calcular sin motor cargado | defecto 1.4.4 | aviso claro, sin crash | A6 | E2E | Estado original falla; clon no debe |

**T3. CAD**

| ID | Funcionalidad | Original | Clon | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| T3-1 | Cargar nozzle JSON → 12 entries + 12 checks + menú type | `build_entries` l.165 | mismos labels (ES ok) | A7 | E2E | Widgets equivalentes; checks marcados por defecto |
| T3-2 | 6 vistas en vivo (Engine, CoverFront, NozzleFront, Tools, Mould, MouldFix) | `update_plots`+`back_2.plot_*` | PNG por vista | A7/A1 | E2E visual | Toggles alteran vistas al instante |
| T3-3 | Export Engine/Cover/Tools CSV (×100, multi‑sketch) | `export_*` `back_2.py:625-719` | escritura por sidecar | A7/A1 | **Golden CSV** | Byte‑a‑byte (redondeos incluidos) vs referencia con settings de `config.json tab_3` |
| T3-4 | Confirmación de sobrescritura | `front_cad.py:378` | diálogo | A7 | E2E | Cancela sin escribir |
| T3-5 | `AS-Nozzle` guard (arquitectura no soportada) | `front_cad.py:197` | mensaje equivalente | A7 | Unit | NozzleConfig no convencional → sin entries |

**T4. Banco de pruebas**

| ID | Funcionalidad | Original | Clon | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| T4-1 | Run: elegir nozzle JSON → CSV de test con nombre `<nozzle>-<HH.MM.SS-DD.MM.yy>.csv` | `run_test` l.440 | mismo naming y cabecera | A8 | Unit | Cabecera `t(s),F(kg),T(K)` |
| T4-2 | Listado y monitor de puertos COM (1 s) | `monitor_ports` l.511 | pyserial + evento | A8 | Unit (mock) | Añadir/quitar puerto actualiza menú |
| T4-3 | Conectar COM 115200 + RESET; monitor de líneas | `connect_com`/`read_serial_data` l.532/684 | Transport abstracción | A8 | Integración (mock serial) | LEDs/estado como original |
| T4-4 | Detección SERIAL STARTED / TEST-BENCH CONNECTED / RESET / ABORT | ídem | misma máquina de estados | A8 | Integración (fixtures de líneas) | Transiciones idénticas |
| T4-5 | WiFi: envío `CONNECT ssid pass` | `connect_wifi` l.769 | ídem | A8 | Integración | Comando exacto en el wire |
| T4-6 | Checklist desde `checklist.json`; completa → `SWITCH START-RECORDING-LED` | `create_checklist`/`checklist_status` l.301 | ídem | A8 | E2E (mock) | Grabación arranca con checklist completa |
| T4-7 | Parseo de líneas t/F/T + dedupe + append CSV + plots/gauges | `on_textbox_change` l.161, `getSerialValues` | ídem; plots nativos | A8/A1 | Golden CSV | CSV byte‑a‑byte vs `Tests/TOPBN-KNSU-32mm-19.28.35-15.09.24.csv` reproducido con replay |
| T4-8 | Abort + RESET; cierre con LEDs azules | `abort_test`/`on_close` l.284/319 | ídem | A8 | Integración | Secuencia de comandos idéntica |
| T4-9 | Hardware real (ESP32) | — | igual protocolo | A8 | **Manual (pendiente)** | ⚠️ No verificable sin banco: plan de prueba de campo (§6.5) |

**DB windows (común)**

| ID | Funcionalidad | Original | Clon | Resp. | Prueba | Aceptación |
|---|---|---|---|---|---|---|
| D-1 | CRUD termoquimica con validación científica y coma→punto | `front_chemWin.py:115-282` | idéntico | A4/A1 | Integración | Aviso al insertar coma; rojo si no válido |
| D-2 | CRUD propelente | `front_propWin.py` | idéntico | A4/A1 | Integración | ídem |
| D-3 | Reasignación de IDs tras add/edit/delete | `reassign_ids` (ambas) | idéntico | A1 | Unit | IDs 1..N consecutivos |
| D-4 | Nombres `Component (id)` y limpieza `\(\d+\)$` | `get_clean_component_name` | idéntico | A1 | Unit | `"H2O (12)"→"H2O"` |

### 4.3 Estrategia de comparación con el original

1. **Referencia dorada:** el código original (`back_modules`, `functions.py` refactorizado mínimamente para quitar `messagebox` mediante shim) se ejecuta en CI con Python 3.12 (imagen oficial) como *implementation of record*. Se generan fixtures JSON/CSV: `contracts/fixtures/{adiabatic_knsu.json, engine_knsu.json, nozzle_bn1.json, cad_bn1_*.csv, tests_replay.csv}`.
2. **Harness de paridad** (`tools/parity/run_parity.py`): misma entrada → llamada a `openred_engine` (clon) y a módulos originales → `numpy.allclose(rtol=1e-9)` para arrays; igualdad exacta para JSON/CSV (con normalizaciones documentadas: typo de label, orden de claves). Se registran como artefactos de CI.
3. **Niveles:** unitarias (pytest + cargo test + vitest), integración (sidecar vs contratos, mock serial), E2E (tauri-driver: flujo completo con fixtures), instalador (§3.4.5 + máquina limpia). Cobertura mínima exigida: engine ≥85 %, Rust shell ≥70 % en módulos de IPC/supervisor.
4. **Ejecución en máquina sin Python:** job dedicado con VM (Windows Sandbox via `windows-latest` + script, o runner self‑hosted limpio): desinstala/bloquea Python (`Set-MpPreference`, PATH scrub), instala MSI, lanza app, ejecuta smoke (abre workspace fixture, corre T0+T1+T2, exporta CSV) y verifica que **ningún proceso `python.exe` fuera de `<install>\engine`** aparece (garantía de autosuficiencia). Aceptación: smoke verde y tamaño de instalación ≈ esperado (±10 %).

---

## 5. Plan de implementación con agent swarm

### 5.1 Estructura de repositorio objetivo

```
OpenRED/                          # repo actual (se conserva legacy/ con el código original)
├── legacy/                       # snapshot del app CustomTkinter (referencia de paridad)
├── contracts/                    # JSON Schemas + fixtures dorados (fuente única)
├── engine/                       # sidecar Python
│   ├── openred_engine/{main,rpc,paths,store,logging}.py
│   ├── openred_engine/modules/{back_0,back_1,back_2}.py
│   ├── openred_engine/plugins/{GrainLibrary,NozzleLibrary}/
│   ├── openred_engine/services/{workspace,adiabatic,engine,nozzle,cad,testbed,db}.py
│   ├── tests/  requirements-core.txt(.lock)  pyproject.toml
├── apps/desktop/                 # Tauri
│   ├── src-tauri/  (main.rs, ipc.rs, sidecar.rs, commands.rs, updater.rs)
│   ├── src/  (ui/ por pestaña, api/, theme/, components/)
│   └── package.json
├── tools/{parity,python-portable,packaging}/
└── tests/{e2e,clean-machine}/
```

### 5.2 Agentes, alcance y coordinación

| Agente | Objetivo y alcance | Entradas / depende de | Archivos propios (exclusividad) | Entregables | Pruebas obligatorias | Aceptación | Integración |
|---|---|---|---|---|---|---|---|
| **A0 Contracts & Fixtures** | Definir JSON Schemas de todos los métodos/eventos; generar fixtures dorados ejecutando el original (back modules) | Acceso a legacy; Python 3.12 en CI | `contracts/**` | Schemas v1 congelados + fixtures + tipos TS/Pydantic generados | Schema validation tests | M0: contratos congelados (no se cambian sin RFC) | Fuente de verdad de todos |
| **A1 Engine core (Python)** | Migrar/refactorizar `back_0/1/2`, plugins, utilidades; eliminar acoplamientos GUI (messagebox/textbox/CWD); servicios JSON‑RPC; DAO SQLite; serial con `Transport` | `contracts/`; legacy | `engine/openred_engine/**`, `engine/tests/**` | Sidecar headless 100 % funcional | pytest ≥85 %; golden vs legacy; mock serial | Todos los métodos de contrato pasan fixtures | Expone stdio; A5‑A8 consumen |
| **A2 Rust shell** | Tauri app: ventanas, sidecar supervisor, router IPC, comandos (diálogos, paths, updater, logs), single‑instance | Tauri 2 docs; `contracts/` | `apps/desktop/src-tauri/**` | Shell estable con sidecar vivo | cargo test; prueba de crash/restart del sidecar | App abre y habla con el sidecar | A3 consume comandos; A1 es supervisado |
| **A3 UI shell + design system** | Layout (sidebar, menús, modales), tokens de temas red/orange + dark/light, componentes base (tables, plots, forms, console) | Figma-equivalente: tokens de `themes/red.json`; D‑decisions | `apps/desktop/src/{theme,components,app}` | Shell navegable con 8 pestañas placeholder | vitest + screenshots | Navegación, tema, menús operativos | A4‑A8 construyen encima |
| **A4 UI Adiabatic + DB windows** | Pestaña T0 + modales CRUD + curva quemado | A1 (métodos), A3 (componentes) | `apps/desktop/src/ui/adiabatic/**`, `ui/db-windows/**` | Módulos completos | E2E módulo | Matriz T0-1..T0-6, D-1..D-4 verde | PR contra trunk tras M2 |
| **A5 UI Engine Design** | Pestaña T1 (inputs, geometría, consola, resultados, export) | A1 engine service | `apps/desktop/src/ui/engine/**` | ídem | E2E + golden export | T1-1..T1-8 verde | ídem |
| **A6 UI Nozzle** | Pestaña T2 (carga, sliders, cálculo con progreso/cancel, off‑design interactivo, tablas, export corregido) | A1 nozzle service | `apps/desktop/src/ui/nozzle/**` | ídem | E2E + golden numérico | T2-1..T2-10 verde | ídem |
| **A7 UI CAD** | Pestaña T3 (entries/checks dinámicos, 6 vistas, 3 exports) | A1 cad service | `apps/desktop/src/ui/cad/**` | ídem | Golden CSV | T3-1..T3-5 verde | ídem |
| **A8 UI Test Bed** | Pestaña T4 (checklist, puertos, monitor, wifi, gauges/plots live, CSV) | A1 testbed + Transport mock | `apps/desktop/src/ui/testbed/**` | ídem | Integración mock + golden CSV | T4-1..T4-8 verde | ídem |
| **A9 Packaging & CI/CD** | Python portable reproducible, bundlers MSI/NSIS+DMG+AppImage, updater, SBOM/licencias, pipelines | §3 | `tools/**`, `.github/workflows/**`, `apps/desktop/src-tauri/tauri.conf.json` (solo ese fichero compartido con A2, coordinado) | Instaladores firmados (win) + portable.zip + latest.json updater | build reproducible (2 runs→mismo hash) | Instalador instala y arranca en runner limpio | A2 coordina tauri.conf.json |
| **A10 QA & Parity** | Harness de paridad, E2E global, suite clean‑machine, triage de defectos, gestión de la matriz §4.2 | fixtures A0; builds de todos | `tests/**`, `tools/parity/**` | Informe de paridad ejecutable por release | Ejecuta todo el pipeline | Matriz 100 % verde o defectos abiertos con severidad | Bloqueo de hitos |
| **A11 Integration lead** | Revisión de PRs, resolución de conflictos de contratos, coordinación A0‑A10, release notes | — | repo completo (solo merge) | trunk estable por hito | CI completo en verde | Sin regresiones entre hitos | Orquesta |

### 5.3 Fases, dependencias e hitos verificables

- **Fase 0 (M0, sem 1):** A0 congela contratos+fixtures; A2 anda el shell con sidecar "echo"; A9 prepara toolchain Python portable (POC de spawn en máquina limpia). *Gate:* schemas validados, POC sidecar viviente.
- **Fase 1 (M1, sem 2‑3):** A1 migra el core completo y pasa golden vs legacy (sin UI). *Gate:* `pytest -m golden` verde; sidecar responde los ~30 métodos con fixtures.
- **Fase 2 (M2, sem 3‑5):** A3 entrega design system; A2 integra eventos; primer módulo E2E completo (T0 por A4). *Gate:* E2E T0 verde en CI.
- **Fase 3 (M3, sem 4‑7, paralelo):** A5, A6, A7 (dependen solo de A1+contratos) + A1 optimiza rendimiento (precompute de curvas M/PR, caché). *Gate:* matriz T1, T2, T3 verde.
- **Fase 4 (M4, sem 6‑8):** A8 con mock serial; A9 empaqueta instalador alpha. *Gate:* E2E mock T4 verde; MSI instalable.
- **Fase 5 (M5, sem 8‑10):** A10 ejecuta paridad total + clean‑machine; defectos a A11→reasignados. *Gate:* clean‑machine verde, updater funcional.
- **Fase 6 (M6, sem 10‑12):** release candidate: firma Windows, pruebas de hardware del banco (manual, con registro), documentación de usuario, publicación. *Gate:* matriz §4.2 al 100 % (T4-9 documentado como "pendiente de hardware" si no hay banco disponible).

**Reglas de coordinación:** trunk‑based con PRs; contratos inmutables post‑M0 (cambios vía RFC en `contracts/RFC-*.md`); cada agente solo toca sus rutas (conflicto previsto único: `tauri.conf.json` → A9 abre PR y A11 lo aplica); los eventos/progress usan versionado de payload; feature flags `ui_engine/ui_nozzle/…` para desacoplar merges de hitos; todo defecto entra en `tests/defects/DEF-*.md` con repro y estado.

---

## 6. Riesgos y decisiones

| # | Riesgo | Impacto | Mitigación | Verificación |
|---|---|---|---|---|
| R1 | Paridad numérica (`fsolve` semillas, tolerancias del Newton propio, BFS de frente) | Alto | Conservar scipy; fixtures dorados del original; tolerancias 1e‑9 | `tools/parity` en CI por PR |
| R2 | Tamaño del instalador (≈110‑140 MB; original 72 MB) | Medio | Excluir Tcl/Tk; LZMA; fase 3: swap de scipy por `newtonRaph`+`np.interp` tras validación | Job de CI que falla si > 160 MB; informe de tamaño por release |
| R3 | Import dinámico de plugins en runtime embebido | Alto | Plugins como `.py` en recursos (no zip); tests de carga en clean‑machine | Smoke E2E en clean‑machine con plugin de usuario de ejemplo |
| R4 | SmartScreen/AV falsos positivos | Medio | Binario firmado (Trusted Signing); evitar PyInstaller para el runtime (carpeta plana) | Prueba de descarga en VM limpia con Defender |
| R5 | Licencias (GPLv3 app; Tauri MIT; wheels BSD/PSF/HPND) | Bajo/Medio | El clon hereda GPLv3; incluir `LICENSES/` y texto matplotlib/Pillow/DejaVu | `pip-licenses` + revisión legal en M5 |
| R6 | Protocolo ESP32 no replicable sin hardware | Alto para T4 | Mock serial para CI; grabaciones reales (`Tests/*.csv`) como replay; plan de prueba de campo documentado | Tests mock verdes + checklist manual de campo en M6 (marcado como no verificable aquí) |
| R7 | Regresión de formatos (config.json/engine/nozzle/CSV/db) | Alto | Tests de esquema + golden files; versión de `config.json` sin cambios de claves | Golden tests T1-6/T2-9/T3-3 |
| R8 | UX de sliders off‑design (fsolve por movimiento) | Medio | Debounce 100 ms + worker en sidecar + precomputadas | Perf test: <200 ms por actualización |
| R9 | Python embebido roto en algún SO/AV (DLL, MSVC runtime) | Medio | install_only incluye lo necesario; prueba en VM limpia win10/11; fallback portable.zip | Job clean‑machine |
| R10 | Bug original del export de toberas (§1.4.3) — decisión: clon exporta **correctamente** | Documental | Delta documentada en matriz T2‑9; JSON de referencia `BN1.json` como guía de claves | Golden T2‑9 |
| R11 | CWD/temp_dir.txt semántica (se borra al salir) cambia a estado persistente | Bajo | Decisión D‑G11: recordar último dir en config de app; documentado como mejora | Unit G11 |
| R12 | Windows‑only → mac/linux: serial, paths, firmas | Medio | Fase 1 solo Windows en release; mac/linux beta detrás de flag | Jobs matrix CI con xfail documentados |
| R13 | `messagebox`/hilos actuales: comportamiento accidental (consola escribe desde hilo) puede diferir en clon | Bajo | El clon encola y envía por IPC (más correcto); se valida que la secuencia de líneas de consola sea idéntica | Golden T1‑3 |
| R14 | No poder ejecutar nada en el entorno de análisis (Python ausente) | Proceso | Plan 100 % basado en CI; hito M0 incluye "arrancar legacy y capturar outputs reales" antes de congelar fixtures | M0 gate |

### 6.1 Supuestos declarados

- El repo local refleja el estado publicable v0.1 (instalador `inno/setup.exe` ≡ HEAD).
- No existe backend remoto, telemetría ni auto‑actualización que clonar.
- El firmware del ESP32 no forma parte del repo: el protocolo se replica tal cual está codificado en `front_test.py` (única fuente disponible).
- `SQUARE.py` es código en transición (sin clase plugin); se mantiene el archivo en `plugins/` sin registro hasta que el autor lo complete (paridad: hoy no aparece en UI).
- La normalización del typo `"DP. Thrust (kg)1"` → `"DP. Thrust (kg)"` se acepta como mejora documentada (afecta solo a claves de `calculatedResults` en exports nuevos).

### 6.2 Qué no puede verificarse aquí y cómo se validará durante la ejecución

- Comportamiento en runtime de la app original (no ejecutable en este entorno): se captura en M0 ejecutando el legacy en CI y en una máquina con Python 3.12 para generar los fixtures dorados.
- Hardware del banco de pruebas (ESP32, célula de carga): plan de prueba de campo con banco real en M6; hasta entonces T4 solo está probado con replay/mock.
- Instalación en macOS sin firma (Gatekeeper) y actualizaciones firmadas: verificación manual planificada en M5/M6 (requiere certificados que no existen hoy).
