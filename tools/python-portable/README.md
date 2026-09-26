# tools/python-portable — runtime Python del sidecar

Empaqueta **CPython 3.12 de python-build-standalone** (astral-sh) + las wheels del motor en una
carpeta copiable a los recursos de Tauri.

## Ficheros

| Fichero | Función |
|---|---|
| `python.lock` | Release fijado (`20260924`, CPython 3.12.14) + SHA-256 de cada tar.gz `install_only` por plataforma |
| `fetch_python.ps1` | Windows/CI: descarga, verifica SHA-256, extrae a `engine/python/` e instala las wheels |
| `fetch_python.sh` | Linux/macOS/CI: equivalente |
| `refresh_python_lock.ps1` | Regenera `python.lock` desde la API de GitHub + `SHA256SUMS` (revisar el diff antes de commitear) |

## Uso

```powershell
pwsh tools/python-portable/fetch_python.ps1                 # plataforma detectada
pwsh tools/python-portable/fetch_python.ps1 -Force          # reinstala aunque ya exista
pwsh tools/python-portable/fetch_python.ps1 -SkipDeps       # solo el intérprete
```

```bash
bash tools/python-portable/fetch_python.sh
bash tools/python-portable/fetch_python.sh --flavor aarch64-apple-darwin
```

El script es **idempotente**: guarda `engine/python/.openred-runtime.json` con el asset y su hash;
si coinciden con `python.lock`, no descarga nada. Si el archivo cacheado no cuadra con el hash del
lock, se borra y se aborta (nunca se usa un runtime no verificado).

## Layout resultante

```
engine/python/
├── python.exe / bin/python3      # intérprete 3.12 (stdlib incluida, sin tkinter)
├── Lib/ …
│   └── site-packages/            # wheels de engine/requirements-core.lock (instaladas por uv)
└── .openred-runtime.json         # asset + sha256 + release_tag (marcador de idempotencia)
```

> **uv:** las dependencias se instalan *dentro* del runtime con
> `uv pip install --system --python engine/python/python.exe -r engine/requirements-core.lock`
> (fallback: el pip del propio intérprete). Al quedar en el `site-packages` del runtime, el
> sidecar arranca sin `PYTHONPATH`; el supervisor Tauri sigue exportando el directorio del motor
> (`OPENRED_RESOURCE_DIR`), tal como se documenta en `tests/clean-machine/smoke.ps1` y el plan §3.3.

## Regenerar el pin

```powershell
pwsh tools/python-portable/refresh_python_lock.ps1
git diff tools/python-portable/python.lock
```

`refresh_python_lock.ps1` consulta `https://api.github.com/repos/astral-sh/python-build-standalone/releases`,
elige el release más reciente con assets `cpython-3.12.*-install_only.tar.gz`, descarga `SHA256SUMS`
y reescribe el lock con tag, versión y hashes reales.

## Licencias

CPython se distribuye bajo PSF-2.0; python-build-standalone redistribuye el intérprete y sus
dependencias. `tools/packaging/build_engine_bundle.ps1` copia el `LICENSE` del runtime a
`artifacts/engine-bundle/LICENSES/` para que el bundle Tauri lo incluya.
