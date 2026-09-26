import React from "react";
import ReactDOM from "react-dom/client";
import { AppShell } from "./app/AppShell";
import { applyThemeAttributes, readStoredTheme } from "./theme";

import "./theme/tokens.css";
import "./styles/global.css";
import "./styles/components.css";
import "./styles/app.css";

// Aplica el tema persistido antes del primer render (evita parpadeo).
const stored = readStoredTheme();
applyThemeAttributes(stored.theme, stored.mode);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AppShell />
  </React.StrictMode>,
);
