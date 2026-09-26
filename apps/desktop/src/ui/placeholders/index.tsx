import { cx } from "../../utils/cx";
import type { TabModuleProps } from "../types";

/**
 * Placeholder idéntico en función a `front_doc.py` / `front_cfd.py` /
 * `front_post.py` del legacy (un único label "Soon").
 */
export function SoonTab({ title, className }: TabModuleProps & { title: string }) {
  return (
    <div className={cx("or-soon", className)} data-module="soon">
      <span className="or-soon__text">Soon</span>
      <span className="or-soon__caption">{title}</span>
    </div>
  );
}

export function DocumentationTab(props: TabModuleProps) {
  return <SoonTab title="Documentation" {...props} />;
}

export function OpenFoamTab(props: TabModuleProps) {
  return <SoonTab title="OpenFOAM Maker" {...props} />;
}

export function PostProcessingTab(props: TabModuleProps) {
  return <SoonTab title="Post-Processing" {...props} />;
}
