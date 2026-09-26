# `apps/desktop/src` — shell de UI + design system (agente A3)

Frontend React 19 + TypeScript + Vite 8 del clon OpenRED. La app se monta en
`src/main.tsx` y el shell navegable vive en `src/app/`.

## Estructura

```
src/
├── api/
│   ├── engine.ts        # request/onEngineEvent/invokeCommand + atajos del contrato
│   ├── errors.ts        # RpcError, isCancel (1005), toRpcError
│   ├── mock.ts          # backend simulado (dev en navegador y tests)
│   └── types.ts         # tipos de dominio (WorkspaceConfig, EnginePayload, …)
├── theme/
│   ├── tokens.css       # variables CSS: data-theme=red|orange, data-mode=dark|light
│   └── ThemeProvider.tsx# contexto + persistencia openred.theme / openred.mode
├── components/          # design system (Button, Table, Modal, Console, …)
├── styles/              # global.css, components.css, app.css
├── app/
│   ├── AppShell.tsx     # raíz: ThemeProvider > ToastProvider > WorkspaceProvider
│   ├── MenuBar.tsx      # File / Preferences / Database / Help
│   ├── Sidebar.tsx      # 8 módulos (activo en openred.tab)
│   ├── WorkspaceProvider.tsx
│   ├── StatusBar.tsx    # estado del motor + workdir
│   └── bus.ts           # evento openred:export para el módulo activo
├── ui/
│   ├── adiabatic|engine|nozzle|cad|testbed/  # esqueletos (A4-A8)
│   ├── db-windows/      # ComponentsWindow / PropellantsWindow (A4)
│   └── placeholders/    # Documentation / OpenFOAM Maker / Post-Processing ("Soon")
└── test/                # setup + tests de vitest
```

## Comandos

No se ha añadido script a `package.json` (exclusividad de A3 sobre `src/**`);
ejecuta vitest directamente:

```powershell
cd apps/desktop
npx vitest run            # suite completa (jsdom + Testing Library)
npx vitest                # modo watch
npx tsc --noEmit          # type-check
npx vite build            # build de producción
```

## Modo mock (sin Tauri)

Si `window.__TAURI_INTERNALS__` no existe (`npm run dev` en navegador, vitest),
`request()` e `invokeCommand()` responden desde `src/api/mock.ts` con datos de
ejemplo (`app.info`, `workspace.*`, `db.*`, `engine.calculate`, …). Dentro de
Tauri se usan los comandos Rust reales: `engine_request`, `engine_status`,
`engine_restart`, `app_info`, `pick_*`, `save_workdir`, `open_logs_folder`, y el
evento `engine-event`.

## Contrato para los módulos (A4-A8)

Cada módulo exporta un componente con props `TabModuleProps`
(`src/ui/types.ts`): `{ active?: boolean; className?: string }`, registrado en
`src/app/tabs.tsx`.

- Estado de trabajo: `useWorkspace()` → `{ workdir, config, hasConfig,
  openWorkdir(), saveConfig(), setTabConfig(tab, patch) }`.
- Errores: lanza/deja propagar `RpcError`; el shell los muestra con `Toast`
  (el código 1005 se ignora). También puedes usar `useToast()`.
- Eventos: `onEngineEvent(handler)` / `onEngineEventOf("progress", cb)`.
- Figuras: `FigureView` (PNG base64), `LineChart` (ECharts), `Gauge`, `Console`,
  `Table`, `ProgressDialog` (cancelable con `requestId` → `request.cancel {id}`).
- Números: `NumberField` con semántica `get_entry_value` (vacío -> `"0"`).

## Temas

Tokens extraídos de `legacy/themes/red.json` y `orange.json`; por defecto
`red` + `dark`. El acento de red es `#D03434` y el de orange `#FF6505` (dark).
Preferences → Modes/Themes cambia y persiste `openred.theme`/`openred.mode`.
