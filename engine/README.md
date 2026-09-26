# openred_engine

Sidecar headless de cálculo de OpenRED. Habla JSON-RPC 2.0 por stdio (una línea JSON por mensaje).

- Contrato: [`../contracts/methods.md`](../contracts/methods.md)
- Arranque: `python -s -X utf8 -m openred_engine`
- Tests: `uv run pytest`
- Paridad con la app original: `uv run pytest -m golden`

El paquete no importa tkinter ni customtkinter. Las figuras se renderizan con matplotlib (backend `Agg`)
a PNG en base64. La base de datos SQLite y las rutas de trabajo se resuelven vía `openred_engine.paths`.
