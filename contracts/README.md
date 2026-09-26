# contracts/ — contrato IPC congelado y fixtures dorados

Este directorio es la **fuente de verdad** de la comunicación entre el shell Tauri y el sidecar
Python. Cualquier consumidor (Rust, TS, Pydantic, tests) deriva de aquí; ningún otro sitio
redefine métodos, params, resultados ni errores.

| Ruta | Contenido |
|---|---|
| `methods.md` | Contrato IPC v1 congelado en M0 (transporte, códigos de error, métodos, eventos, reglas de paridad) |
| `schemas/*.schema.json` | JSON Schema **draft 2020-12** del sobre y de cada namespace (`oneOf` de `{method, params, result}` + variantes de error documentadas) |
| `fixtures/` | Fixtures dorados generados ejecutando el legacy real (`legacy/`) + README con provenance |
| `RFC-XXXX-*.md` | Propuestas de cambio del contrato (obligatorias post-M0) |

## Esquemas

- `envelope.schema.json`: peticiones `{id?, method, params}`, respuestas OK/error y
  notificaciones `{method:"event", params:{name,...}}`; códigos de error de `methods.md` §2.
- Un fichero por namespace: `app`, `workspace`, `db`, `adiabatic`, `plugins`, `engine`,
  `nozzle`, `cad`, `testbed` y `events` (eventos transversales de `methods.md` §3.10).
- Los parámetros desconocidos se rechazan (`additionalProperties: false`) salvo donde el
  contrato los declara extensibles (p. ej. `payload`, `spec`, `settings`).
- Los resultados aceptan claves adicionales sólo cuando el contrato lo prevé; los fixtures y el
  harness comparan las claves obligatorias y, en el caso del `payload` exportable (T1-6/T2-9),
  también rechazan extras para garantizar el byte-parity.

### Validación

```bash
uv run --project engine python tools/parity/validate_schemas.py
```

Comprueba que: los esquemas son JSON Schema válido; los métodos declarados coinciden **exactamente**
con los de `methods.md` (49 en v1) y los eventos con la tabla §3.10 (10 en v1); cada fixture JSON
con `rpc` valida como llamada contractual (o como variante de error / barrido `calls_from`); y los
fixtures tienen las claves obligatorias de su `id`.

## Fixtures

```bash
uv run --project engine python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures
uv run --project engine python tools/parity/gen_fixtures.py --full   # añade T1 completo (ItMax real)
uv run --project engine python tools/parity/run_parity.py            # compara el sidecar contra los fixtures
```

Los fixtures se generan **ejecutando el legacy** (no a mano), no contienen rutas absolutas ni
timestamps y documentan su provenance (commit, comando). `fixtures/README.md` distingue los
`smoke` (reducidos para CI) de los completos y enumera las normalizaciones (formato de UI,
typo `DP. Thrust (kg)1`, saltos de línea en consola).

## Proceso RFC (post-M0)

`methods.md` y los esquemas están **congelados**. Cualquier cambio incompatible o adición
requiere un RFC antes de tocar `contracts/`:

1. Copia la plantilla de abajo a `contracts/RFC-XXXX-<slug>.md` (numera secuencialmente).
2. Rellena: motivación, cambio exacto (diff de esquema/fixture), compatibilidad,
   impacto en A1–A10, plan de migración y pruebas.
3. Abre PR **sólo del RFC**; requiere revisión de A0 (contratos), A11 (integración) y del
   agente afectado.
4. Tras el merge del RFC, el PR de implementación actualiza `methods.md`, los esquemas, los
   fixtures y los consumidores en el mismo cambio.
5. Los cambios puramente aditivos y compatibles (nuevo método, nuevo campo opcional, nuevo
   evento) siguen el mismo proceso; los parches de documentación sin efecto en el contrato
   pueden ir directos con revisión de A0.

### Plantilla de RFC

```markdown
# RFC-XXXX — <título>

- **Estado:** borrador | aceptado | rechazado | implementado
- **Autor:** <agente/persona> · **Fecha:** <AAAA-MM-DD>
- **Tipo:** aditivo | incompatible | corrección | documentación
- **Afecta a:** métodos/eventos/esquemas/fixtures (lista)

## Motivación

## Cambio propuesto

```jsonc
// diff o fragmento de esquema/fixture
```

## Compatibilidad y migración

## Impacto por agente (A1..A10)

## Pruebas / criterios de aceptación
```

## Reglas de paridad que condicionan el contrato

- Códigos numéricos literales del legacy; tolerancia `numpy.allclose(rtol=1e-9, atol=0)`.
- Ficheros exportados (`Engines/*.json`, `Nozzles/*.json`, CSV CAD/Tests) byte-compatibles
  salvo normalizaciones documentadas (`DP. Thrust (kg)1`, `Sketch,Plane`, CRLF).
- La consola de T1/T2 conserva el formato exacto (`:.{decimals}f`, `:10.3e`) y el orden.
- `config.json` es opaco para el motor (claves y valores-cadena idénticos).
- Los defectos conocidos del legacy se registran en `tests/defects/DEF-*.md`; una divergencia
  intencionada debe estar justificada allí (p. ej. R10 para el export de toberas).
