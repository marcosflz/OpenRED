# Migrar los datos del legacy (OpenRED Python/Tk) al clon de escritorio

Este documento describe cómo pasar una instalación existente del OpenRED legacy al clon
Tauri + motor headless, y qué se verificó con datos reales.

## De dónde a dónde

| Dato legacy | Ubicación legacy | Ubicación en el clon |
|---|---|---|
| Base de datos SQLite | `app_dir\database.db` (junto al ejecutable) | `%APPDATA%\OpenRED\database.db` |
| Directorio de trabajo | el elegido por el usuario (`temp_dir.txt`, p. ej. `...\workingDirectory`) | `%USERPROFILE%\Documents\OpenRED` (por defecto) |
| `config.json` y `checklist.json` | dentro del directorio de trabajo | igual, dentro del directorio de trabajo |
| `Engines\ Nozzles\ Sketches\ Tests\` | dentro del directorio de trabajo | igual, dentro del directorio de trabajo |
| Último directorio elegido | `app_dir\temp_dir.txt` | `%APPDATA%\OpenRED\config\app.json` (`{"workdir": "..."}`) |

Las **tablas son idénticas** (`propelente`, `termoquimica`): el fichero `database.db` del legacy
se puede copiar tal cual, no hay conversión.

## Procedimiento

```powershell
# 1) Copia de seguridad de la BD actual del clon (si existe)
$data = "$env:APPDATA\OpenRED"
if (Test-Path "$data\database.db") { Copy-Item "$data\database.db" "$data\database.db.bak-empty" }

# 2) Base de datos legacy -> carpeta de datos del clon
Copy-Item "<legacy>\database.db" "$data\database.db" -Force

# 3) Directorio de trabajo legacy -> Documents\OpenRED (o el que se prefiera)
New-Item -ItemType Directory -Force "$HOME\Documents\OpenRED" | Out-Null
Copy-Item "<legacy>\workingDirectory\*" "$HOME\Documents\OpenRED" -Recurse -Force

# 4) Fijar el directorio de trabajo (la app también recuerda el último elegido en app.json)
#    Opción A: abrir la app y seleccionarlo con File/Pick working directory.
#    Opción B: escribirlo a mano:
'{ "workdir": "' + "$HOME\Documents\OpenRED".Replace('\', '\\') + '" }' |
    Set-Content "$data\config\app.json" -Encoding utf8
```

> `temp_dir.txt`, `venv\`, `build\`, `dist\` y las fuentes Python del legacy **no se migran**:
> el clon trae su propio motor y su propio Python portable.

## Repetir la verificación

El script `tools/migration/verify_migration.py` arranca el motor empaquetado contra los datos
migrados y comprueba todo lo de abajo (41 comprobaciones). Requiere el bundle del motor
(`artifacts/engine-bundle`, ver README) y los fixtures (`contracts/fixtures/`).

```powershell
python tools/migration/verify_migration.py
# rutas no estándar:
python tools/migration/verify_migration.py --workdir "D:\datos\OpenRED" --data-dir "D:\perfil\OpenRED"
```

Sin `--legacy` solo comprueba que los datos se leen; con `--legacy <workingDirectory>` compara
listados y BD fila a fila contra el legacy.


## Qué se verificó con datos reales (2026-09-25)

Datos migrados: `legacy/database.db` (propelente **KNSU** + 13 componentes termoquímicos) y
`legacy/workingDirectory` (1 motor `KNSU-32-RT65.json`, 1 tobera `BN1.json`, 9 bocetos CAD,
8 ensayos CSV, `config.json` con 4 pestañas y `checklist.json`).

Con el **motor empaquetado** (`artifacts/engine-bundle`, CPython portable) y JSON-RPC real,
37/37 comprobaciones en verde:

* `workspace.set_dir` detecta `config.json` (4 pestañas) y crea lo que falte.
* `workspace.list` devuelve exactamente los mismos ficheros que el directorio legacy en
  `Engines`, `Nozzles`, `Sketches` y `Tests`.
* `db.propellants.list` / `db.components.list`: KNSU y los 13 componentes con los **mismos
  valores** que el legacy (T_ad, gamma, cChar, Density, a, n, Hf0…).
* `engine.load KNSU-32-RT65.json` y `nozzle.load BN1.json` leen los ficheros migrados.
* `nozzle.calculate` con los datos migrados reproduce los 21 valores del fixture dorado.
* `cad.export` de engine/cover/tools escribe en el `Sketches` migrado 3 CSV **idénticos** a
  los dorados (normalizando CRLF).
* `testbed.checklist.load` lee los 4 pasos de `checklist.json`.
* El workdir queda persistido en `%APPDATA%\OpenRED\config\app.json` y se restaura al
  reiniciar (segundo proceso del motor y app real).
* Arranque del portable sin variables de entorno: la barra de estado muestra
  `C:/Users/marco/Documents/OpenRED`, el desplegable de propelente `KNSU (1)` y la geometría
  `Tubular-Grain` con los valores de `config.json`.

> El motor crea `database.db.bak` en la primera escritura (`store.backup_once`), como red de
> seguridad adicional.
