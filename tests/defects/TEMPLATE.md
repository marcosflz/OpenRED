# DEF-XXXX — <título corto>

| Campo | Valor |
|---|---|
| **ID** | DEF-XXXX |
| **Severidad** | crítico / alto / medio / bajo |
| **Estado** | abierto / en curso / corregido / descartado / "no se corrige" |
| **Componente** | engine / shell / UI T0..T4 / packaging / CI / legacy (referencia) |
| **Detectado en** | commit `<sha>` · fecha `<AAAA-MM-DD>` · agente `<A0..A11>` |
| **Matriz §4.2** | `T?` / `G?` / `D?` (si aplica) |
| **Fixture / prueba** | `contracts/fixtures/<fichero>` · `tests/...` · comando |

## Resumen

Una o dos frases: qué falla, dónde y con qué impacto observable para el usuario o para la paridad.

## Reproducción

```bash
# Comandos exactos, desde la raíz del repo. Sin rutas absolutas de la máquina.
uv run python tools/parity/run_parity.py --only t2
```

Entradas mínimas (fichero/valores) y resultado observado:

```
<salida relevante, recortada>
```

Resultado esperado (referencia legacy, fixture o matriz §4.2):

```
<salida esperada>
```

## Causa raíz

Explicación técnica, con `fichero:línea` de legacy y del clon. Si es una divergencia
intencionada de paridad, indicar la decisión y el RFC/normalización que la ampara.

## Impacto

Módulos afectados, releases bloqueadas, datos que podrían corromperse o diferencias
numéricas cuantificadas (Δ rel/abs y dónde se midió).

## Corrección propuesta

Plan concreto (fichero y cambio), más la prueba que debe quedar en verde.

## Verificación

- [ ] Test automático añadido/actualizado (`<ruta>`)
- [ ] `tools/parity/run_parity.py` en verde para el fixture afectado
- [ ] `legacy/` no se ha modificado (salvo shim documentado)
