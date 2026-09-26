import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "../utils/cx";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Etiqueta accesible obligatoria (se usa como `aria-label` y `title`). */
  label: string;
  size?: "sm" | "md";
  variant?: "ghost" | "solid";
  children: ReactNode;
}

export function IconButton({
  label,
  size = "md",
  variant = "ghost",
  className,
  children,
  type = "button",
  ...rest
}: IconButtonProps) {
  return (
    <button
      type={type}
      className={cx("or-icon-btn", `or-icon-btn--${size}`, `or-icon-btn--${variant}`, className)}
      aria-label={label}
      title={label}
      {...rest}
    >
      {children}
    </button>
  );
}
