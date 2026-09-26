import { useEffect, useState } from "react";
import { cx } from "../utils/cx";
import { IconButton } from "./IconButton";
import { Spinner } from "./Spinner";

/** Convierte un PNG base64 (sin prefijo) en `data:` URL. */
export function pngDataUrl(png: string): string {
  return png.startsWith("data:") ? png : `data:image/png;base64,${png}`;
}

export interface FigureViewProps {
  /** PNG en base64 (con o sin prefijo `data:`). */
  png?: string | null;
  alt?: string;
  loading?: boolean;
  error?: string | null;
  /** `contain` ajusta a la caja; `actual` permite zoom/scroll. */
  initialFit?: "contain" | "actual";
  toolbar?: boolean;
  height?: number | string;
  className?: string;
}

/** Renderiza figuras PNG del motor (matplotlib) con zoom y ajuste. */
export function FigureView({
  png,
  alt = "Figura",
  loading = false,
  error = null,
  initialFit = "contain",
  toolbar = true,
  height = 320,
  className,
}: FigureViewProps) {
  const [zoom, setZoom] = useState(1);
  const [fit, setFit] = useState<"contain" | "actual">(initialFit);

  useEffect(() => {
    setZoom(1);
  }, [png]);

  const zoomBy = (factor: number) =>
    setZoom((current) => Math.min(8, Math.max(0.1, Number((current * factor).toFixed(2)))));

  return (
    <div className={cx("or-figure", className)}>
      {toolbar ? (
        <div className="or-figure__toolbar">
          <IconButton label="Reducir" size="sm" onClick={() => zoomBy(1 / 1.25)} disabled={fit === "contain"}>
            −
          </IconButton>
          <span className="or-figure__zoom">{Math.round(zoom * 100)}%</span>
          <IconButton label="Ampliar" size="sm" onClick={() => zoomBy(1.25)} disabled={fit === "contain"}>
            +
          </IconButton>
          <IconButton
            label="Restablecer zoom"
            size="sm"
            onClick={() => {
              setZoom(1);
              setFit("actual");
            }}
          >
            ⟲
          </IconButton>
          <IconButton
            label={fit === "contain" ? "Tamaño real" : "Ajustar a la ventana"}
            size="sm"
            onClick={() => setFit((current) => (current === "contain" ? "actual" : "contain"))}
          >
            {fit === "contain" ? "⤢" : "⤡"}
          </IconButton>
        </div>
      ) : null}
      <div className="or-figure__canvas" style={{ height }}>
        {loading ? (
          <div className="or-figure__placeholder">
            <Spinner size={22} />
            <span>Generando figura…</span>
          </div>
        ) : error ? (
          <div className="or-figure__error" role="alert">
            {error}
          </div>
        ) : !png ? (
          <div className="or-figure__placeholder">
            <span>Sin figura</span>
          </div>
        ) : (
          <img
            src={pngDataUrl(png)}
            alt={alt}
            className={cx("or-figure__image", fit === "contain" && "or-figure__image--fit")}
            style={fit === "contain" ? undefined : { transform: `scale(${zoom})` }}
            draggable={false}
          />
        )}
      </div>
    </div>
  );
}
