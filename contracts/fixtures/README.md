# Fixtures dorados — OpenRED Engine

> **Generado** por `tools/parity/gen_fixtures.py`. No editar a mano: los cambios requieren RFC
> (`contracts/RFC-*.md`) porque son la referencia de paridad T0–T4.

## Provenance

- Fecha de generación: 2026-09-25
- Comando: `python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures --full`
- Commit legacy: `c2250d0` (repo OpenRED, subdirectorio `legacy/`)
- Intérprete: Python 3.12.12
- Sin rutas absolutas ni timestamps dentro de los fixtures: la regeneración es determinista.

## Cómo regenerar

```bash
uv run --project engine python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures
uv run --project engine python tools/parity/gen_fixtures.py --full       # añade engine_knsu.json (ItMax real)
uv run --project engine python tools/parity/gen_fixtures.py --only t0,t4 # subconjunto
```

El generador copia `legacy/database.db` a un CWD temporal, escribe `temp_dir.txt` apuntando a un
workspace temporal con `Engines/ Nozzles/ Sketches/ Tests/`, stubea `customtkinter` y parchea
`tkinter.messagebox` para capturar los avisos. **No modifica `legacy/`**.

## Metodología

Cada fixture JSON incrusta un objeto `rpc` con la llamada contractual reconstruida
(`method`, `params`, `result_from`/`calls_from`), validado por `tools/parity/validate_schemas.py`
contra `contracts/schemas/`. `rpc.result_from` es un puntero JSON al resultado esperado dentro del
propio fixture. Los CSV se comparan byte a byte por `tools/parity/run_parity.py`.

## Smoke vs full

- **smoke**: reducción para CI rápido. `engine_knsu_smoke.json` usa `It=300, dt=0.01`
  (el legacy con `It=300, dt=0.005` desborda su vector de tiempos, ver `tests/defects/DEF-0002.md`).
- **full**: parámetros reales de `workingDirectory/config.json` (T0, T2, T3, T4 y, con `--full`,
  `engine_knsu.json` con `ItMax=10000` y `dh=0.0001`).

## Ficheros

| Fixture | Tag | Origen |
|---|---|---|
| `adiabatic_error.json` | error | source |
| `adiabatic_knsu.json` | full | source |
| `cad_bn1_cover.csv` | full | derived from |
| `cad_bn1_engine.csv` | full | derived from |
| `cad_bn1_sketches.json` | full | source |
| `cad_bn1_tools.csv` | full | derived from |
| `engine_knsu.json` | full | source |
| `engine_knsu_smoke.json` | smoke | source |
| `nozzle_bn1.json` | full | source |
| `nozzle_bn1_op_points.json` | full | source |
| `tests_replay.json` | full | source |

### Notas de normalización

- `adiabatic_error.json`: mensaje capturado de `messagebox.showinfo` → error `-32602`
  `"Invalid integration step value."`.
- `engine_knsu_*.json`: `expected` reproduce `front_propDes.export_results` (incluye `tree_data`
  sin la fila inicial y el tiempo formateado con los decimales de `dt`); `console` son las líneas
  insertadas en el textbox, sin el `\n` final. Las líneas deben compararse tras normalizar los
  saltos de línea (el contrato `event/console {line}` no los incluye).
- `nozzle_bn1.json`: `result.*` es la representación canónica del contrato (valores formateados
  como la UI/export legacy: `:.4e` si ≥1e6, si no `:.4f`; geometría `:.6f`) y `raw.*` guarda los
  dobles sin formato de `calculated_results()` para las comprobaciones a 1e-9. `rpc.params`
  incluye `dt`, `defCheck` y `engineName`; `engine` es el payload crudo del motor
  ({inputs, results}, igual que el fichero `Engines/*.json`). El typo `DP. Thrust (kg)1` solo
  existe en `CONE-LN`, no en TOPN-BN.
- `nozzle_bn1_op_points.json`: `regime` aplica las reglas de `front_nozDes.updateMapPlots`
  (ratios redondeados a 4 decimales). La tobera se construye con la P1 de diseño
  (`params_base.p1`, el valor de `tab_2`; por defecto `engine.results.meanPressure`), igual que
  `updateMapPlots` sobre `self.calculatedNozzle` (ver `tests/defects/DEF-0004.md`).
- `cad_bn1_*.csv`: bytes exactos de `back_2.export_*` (cabecera `Sketch,Plane,x,y,z`, `\r\n`).
- `tests_replay.json`: líneas reconstruidas desde el CSV (`t(s): .. F(kg): .. T(K): ..`),
  parseadas con `functions.getSerialValues` y deduplicadas como `front_test.on_textbox_change`;
  el CSV resultante es byte-idéntico al de referencia.

## Inputs

Copias byte a byte de los ficheros de `legacy/` usados como entrada (`database.db` incluida:
`run_parity.py` la siembra en `OPENRED_DATA_DIR` para que el motor encuentre componentes y
propelentes). `manifest.json` repite los hashes para consumo programático.

| Fichero | SHA-256 |
|---|---|
| `inputs/BN1.json` | `0d2e36fc58262404a301b182cb16591950c815795e5f938f21c684978cb84ef5` |
| `inputs/KNSU-32-RT65.json` | `8bbcf211e60a4c7f564fd29b8b1482c7aedf3a1b2b0a45cd728f0d957e32e263` |
| `inputs/checklist.json` | `d450aae211f3d13d9f782b38188de06779f6f03992ce40c718a8b4f554a26084` |
| `inputs/config.json` | `f9f3e104cb45bbab2ba7b2bf5871b841255a1df06187d193388da835324a6bb9` |
| `inputs/database.db` | `e1731443446ac72612377a88ca327a39678c993de320efdfdf0864498a51370a` |
