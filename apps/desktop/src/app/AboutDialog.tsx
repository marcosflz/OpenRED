import { Modal } from "../components";
import { useWorkspace } from "./WorkspaceProvider";

export interface AboutDialogProps {
  open: boolean;
  onClose: () => void;
}

/** `Help > About`: versión y rutas del motor (equivalente informativo). */
export function AboutDialog({ open, onClose }: AboutDialogProps) {
  const { info, workdir } = useWorkspace();

  return (
    <Modal open={open} onClose={onClose} title="About OpenRED" width={560}>
      <div className="or-about">
        <div className="or-about__logo">OpenRED</div>
        <p className="or-about__tagline">
          Diseño de motores cohete de propelente sólido.
        </p>
        <dl className="or-about__meta">
          <dt>Versión</dt>
          <dd>{info?.version ?? "—"}</dd>
          <dt>Datos</dt>
          <dd className="or-mono">{info?.dataDir ?? "—"}</dd>
          <dt>Recursos</dt>
          <dd className="or-mono">{info?.resourceDir ?? "—"}</dd>
          <dt>Directorio de trabajo</dt>
          <dd className="or-mono">{workdir ?? "—"}</dd>
        </dl>
        <p className="or-about__license">GPL-3.0 · shell Tauri 2 + React 19</p>
      </div>
    </Modal>
  );
}
