# tools/parity — contratos, fixtures y paridad

| Fichero | Función |
|---|---|
| `validate_schemas.py` | Valida `contracts/schemas/*.schema.json` (draft 2020-12), comprueba que los métodos/eventos declarados coinciden con `contracts/methods.md` y valida cada fixture contra su esquema |
| `gen_fixtures.py` | Ejecuta el **legacy real** headless y escribe los fixtures dorados en `contracts/fixtures/` |
| `run_parity.py` | Arranca el sidecar `openred_engine` y compara sus respuestas RPC contra los fixtures |

## Ciclo completo

```bash
# desde la raíz del repo (--project engine usa el venv del motor)
uv run --project engine python tools/parity/validate_schemas.py

uv run --project engine python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures
uv run --project engine python tools/parity/gen_fixtures.py --full   # añade T1 completo

# paridad (sidecar real)
uv run --project engine python tools/parity/run_parity.py
uv run --project engine python tools/parity/run_parity.py --only t0,t1
uv run --project engine python tools/parity/run_parity.py --full     # incluye engine_knsu.json

# alternativa: desde engine/ (los defaults resuelven la raíz del repo)
cd engine && uv run python ../tools/parity/run_parity.py
```

Códigos de salida de `run_parity.py`:

| Código | Significado |
|---|---|
| `0` | Todas las comprobaciones en verde |
| `1` | Alguna comprobación falla (el informe `parity-report.json` detalla el primer problema de cada una) |
| `2` | El sidecar no arranca (comando no encontrado, muere antes de `event/ready`, timeout) — mensaje claro, sin traza |

## Entorno del generador

`gen_fixtures.py` prepara un CWD temporal con `database.db`, `temp_dir.txt` y
`Engines/ Nozzles/ Sketches/ Tests/`, stubea `customtkinter` y parchea `tkinter.messagebox`.
No necesita display (matplotlib `Agg`); en Linux basta `python3-tk` para importar `tkinter`.

En CI (`.github/workflows/parity.yml`) los fixtures se generan con el Python del runner
(dependencias del legacy) y el sidecar se ejecuta con el venv de `engine/` (`uv sync`).

## Normalizaciones documentadas

- Consola: se comparan las líneas tras normalizar los saltos de línea sobrantes.
- Tobera: si el motor devuelve valores ya formateados como la UI (`:.4e`/`:.4f`/`:.6f`),
  se comparan contra la representación canónica del fixture; si devuelve dobles crudos, se
  comparan contra `raw.*` con `rtol=1e-9`.
- CSV: comparación exacta tras normalizar CRLF (`\r\n` → `\n`).
- JSON: se comparan valores y conjuntos de claves; el orden de claves no importa.
- `nozzle.op_point`: se aceptan los alias de ratios `p0_p1`/`P0_P1t` (etc.) y `PR = Pe/P1t`.
- Errores: `code` y `message` son normativos; `detail` es libre.

Los defectos abiertos que bloquean la paridad viven en `tests/defects/DEF-*.md`.
