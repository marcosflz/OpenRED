import { useEffect, useState } from "react";
import { engineStatus, onEngineEvent, type EngineStatus } from "../api/engine";
import { cx } from "../utils/cx";
import { useWorkspace } from "./WorkspaceProvider";

/** Indicador de estado del sidecar + directorio de trabajo activo. */
export function StatusBar() {
  const { workdir } = useWorkspace();
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let mounted = true;
    engineStatus()
      .then((value) => {
        if (mounted) setStatus(value);
      })
      .catch(() => {
        if (mounted) setFailed(true);
      });

    let unlisten: (() => void) | null = null;
    void onEngineEvent((event) => {
      if (event.name === "ready") {
        setFailed(false);
        setStatus((previous) => ({
          ...(previous ?? { running: true }),
          running: true,
          version: event.version,
          pid: event.pid,
        }));
      }
      if (event.name === "exiting") setFailed(true);
    }).then((fn) => {
      unlisten = fn;
    });

    return () => {
      mounted = false;
      unlisten?.();
    };
  }, []);

  const running = !failed && status?.running !== false;

  return (
    <div className="or-status">
      <span
        className={cx("or-status__dot", running ? "is-on" : "is-off")}
        aria-hidden="true"
      />
      <span className="or-status__text">{running ? "Motor activo" : "Motor detenido"}</span>
      <span
        className="or-status__path"
        title={workdir ?? "Sin directorio de trabajo"}
        data-testid="status-workdir"
      >
        {workdir ?? "Sin dir. de trabajo"}
      </span>
    </div>
  );
}
