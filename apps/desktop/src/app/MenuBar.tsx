import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { THEME_NAMES, useTheme } from "../theme";
import { cx } from "../utils/cx";

export interface MenuBarProps {
  onOpenWorkdir: () => void;
  onSaveConfig: () => void;
  onExport: () => void;
  onOpenComponents: () => void;
  onOpenPropellants: () => void;
  onOpenLogs: () => void;
  onAbout: () => void;
  onExit: () => void;
}

type MenuEntry =
  | { kind: "item"; label: string; onSelect: () => void; checked?: boolean }
  | { kind: "separator" }
  | { kind: "submenu"; label: string; entries: MenuEntry[] };

interface MenuGroup {
  id: string;
  label: string;
  entries: MenuEntry[];
}

function MenuEntryView({
  entry,
  depth,
  onRun,
}: {
  entry: MenuEntry;
  depth: number;
  onRun: (action: () => void) => void;
}) {
  if (entry.kind === "separator") return <div className="or-menu__separator" role="separator" />;

  if (entry.kind === "submenu") {
    return (
      <div className="or-menu__sub">
        <button type="button" className="or-menu__item" role="menuitem" aria-haspopup="menu">
          <span className="or-menu__check" aria-hidden="true" />
          <span className="or-menu__label">{entry.label}</span>
          <span className="or-menu__chevron" aria-hidden="true">
            ›
          </span>
        </button>
        <div
          className={cx("or-menu", "or-menu__subpanel", `or-menu__subpanel--depth-${depth}`)}
          role="menu"
        >
          {entry.entries.map((child, index) => (
            <MenuEntryView key={index} entry={child} depth={depth + 1} onRun={onRun} />
          ))}
        </div>
      </div>
    );
  }

  const radio = entry.checked !== undefined;
  return (
    <button
      type="button"
      className={cx("or-menu__item", radio && "or-menu__item--check", entry.checked && "is-checked")}
      role={radio ? "menuitemradio" : "menuitem"}
      aria-checked={radio ? entry.checked : undefined}
      onClick={() => onRun(entry.onSelect)}
    >
      <span className="or-menu__check" aria-hidden="true">
        {entry.checked ? "✓" : ""}
      </span>
      <span className="or-menu__label">{entry.label}</span>
    </button>
  );
}

/** Barra de menú nativa del shell (File / Preferences / Database / Help). */
export function MenuBar({
  onOpenWorkdir,
  onSaveConfig,
  onExport,
  onOpenComponents,
  onOpenPropellants,
  onOpenLogs,
  onAbout,
  onExit,
}: MenuBarProps) {
  const { theme, mode, setTheme, setMode } = useTheme();
  const [open, setOpen] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(null);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(null);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const run = useCallback((action: () => void) => {
    setOpen(null);
    action();
  }, []);

  const groups = useMemo<MenuGroup[]>(() => {
    const themeEntries: MenuEntry[] = THEME_NAMES.map((name) => ({
      kind: "item",
      label: name.charAt(0).toUpperCase() + name.slice(1),
      checked: theme === name,
      onSelect: () => setTheme(name),
    }));

    return [
      {
        id: "file",
        label: "File",
        entries: [
          { kind: "item", label: "Open Working Directory…", onSelect: onOpenWorkdir },
          { kind: "item", label: "Save Configuration", onSelect: onSaveConfig },
          { kind: "item", label: "Export…", onSelect: onExport },
          { kind: "separator" },
          { kind: "item", label: "Exit", onSelect: onExit },
        ],
      },
      {
        id: "preferences",
        label: "Preferences",
        entries: [
          {
            kind: "submenu",
            label: "Modes",
            entries: [
              {
                kind: "item",
                label: "Dark Mode",
                checked: mode === "dark",
                onSelect: () => setMode("dark"),
              },
              {
                kind: "item",
                label: "Light Mode",
                checked: mode === "light",
                onSelect: () => setMode("light"),
              },
            ],
          },
          { kind: "submenu", label: "Themes", entries: themeEntries },
        ],
      },
      {
        id: "database",
        label: "Database",
        entries: [
          { kind: "item", label: "Thermochemical Data", onSelect: onOpenComponents },
          { kind: "item", label: "Propellants Data", onSelect: onOpenPropellants },
        ],
      },
      {
        id: "help",
        label: "Help",
        entries: [
          { kind: "item", label: "Open Logs Folder", onSelect: onOpenLogs },
          { kind: "item", label: "About", onSelect: onAbout },
        ],
      },
    ];
  }, [theme, mode, setTheme, setMode, onOpenWorkdir, onSaveConfig, onExport, onOpenComponents, onOpenPropellants, onOpenLogs, onAbout, onExit]);

  return (
    <div className="or-menubar" ref={rootRef}>
      {groups.map((group) => (
        <div key={group.id} className="or-menubar__group">
          <button
            type="button"
            className={cx("or-menubar__button", open === group.id && "is-open")}
            aria-haspopup="menu"
            aria-expanded={open === group.id}
            onClick={() => setOpen((current) => (current === group.id ? null : group.id))}
            onMouseEnter={() => {
              if (open !== null) setOpen(group.id);
            }}
          >
            {group.label}
          </button>
          {open === group.id ? (
            <div className="or-menu" role="menu">
              {group.entries.map((entry, index) => (
                <MenuEntryView key={index} entry={entry} depth={0} onRun={run} />
              ))}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
