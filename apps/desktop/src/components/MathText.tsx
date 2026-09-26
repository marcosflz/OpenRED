import katex from "katex";
import "katex/dist/katex.min.css";
import { cx } from "../utils/cx";

export interface RenderLatexOptions {
  displayMode?: boolean;
}

/**
 * Renderiza LaTeX a HTML con KaTeX (nunca lanza: `throwOnError: false`).
 * Equivalente a la etiqueta de reacción del módulo adiabático original.
 */
export function renderLatex(text: string, options: RenderLatexOptions = {}): string {
  const source = text ?? "";
  if (!source.trim()) return "";
  try {
    return katex.renderToString(source, {
      throwOnError: false,
      displayMode: options.displayMode ?? false,
      strict: false,
    });
  } catch {
    return source;
  }
}

export interface MathTextProps {
  text: string;
  display?: boolean;
  className?: string;
}

export function MathText({ text, display = false, className }: MathTextProps) {
  return (
    <span
      className={cx("or-math", display && "or-math--display", className)}
      dangerouslySetInnerHTML={{ __html: renderLatex(text, { displayMode: display }) }}
    />
  );
}
