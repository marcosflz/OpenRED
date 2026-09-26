# tools/packaging — bundle del motor e instaladores

| Fichero | Función |
|---|---|
| `make_engine_lock.py` | Genera `engine.lock` (SHA-256 por fichero de `engine/openred_engine/**` + `engine/python/**`); determinista y con modo `--verify` |
| `build_engine_bundle.ps1` | Arma `artifacts/engine-bundle/` (`python/`, `openred_engine/`, `engine.lock`, `LICENSES/`) listo para copiar a los recursos Tauri |
| `build_installer.ps1` | `npm ci` + `npx tauri build` + recogida de MSI/NSIS/DMG/AppImage/deb en `artifacts/` y plantilla `latest.json` |

## Flujo

```powershell
# 1. runtime portable (una vez por release; verifica SHA-256 del lock)
pwsh tools/python-portable/fetch_python.ps1

# 2. bundle del motor
pwsh tools/packaging/build_engine_bundle.ps1

# 3. instaladores (integra el bundle cuando A2/A9 aterricen tauri.conf.json)
pwsh tools/packaging/build_installer.ps1 -BuildEngineBundle
```

## Integridad

`engine.lock` se genera **desde el árbol copiado** (`--root <bundle>`), de modo que los hashes
corresponden a los bytes que se distribuyen. En runtime el supervisor Tauri puede verificar el
lock antes de lanzar el sidecar (decisión de A2); en CI:

```bash
uv run --project engine python tools/packaging/make_engine_lock.py --verify engine/engine.lock
```

Los ficheros excluidos del lock son `__pycache__/`, `*.pyc/*.pyo/*.tmp` y `_downloads/`
(caché de descargas del runtime). El lock no contiene timestamps: dos builds del mismo árbol
producen el mismo hash.

## Layout del bundle (se copia a `<install>/engine`)

```
engine-bundle/
├── python/                 # CPython 3.12 + wheels en su Lib/site-packages
├── openred_engine/         # sidecar + plugins
├── requirements-core.lock  # procedencia de las wheels
├── engine.lock             # SHA-256 por fichero
└── LICENSES/               # PSF + terceros
```

> `tauri.conf.json` declara `bundle.resources` con este bundle copiado a `<install>/engine`
> (ver `apps/desktop/src-tauri/tauri.conf.json`). El lanzador del sidecar exporta
> `OPENRED_RESOURCE_DIR=<install>/engine` y usa `<install>/engine/python/python.exe`; al llevar
> las wheels en su propio `site-packages`, no se necesita `PYTHONPATH`.
