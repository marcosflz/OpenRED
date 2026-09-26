import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "../utils/cx";
import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Muestra un spinner y deshabilita el botón. */
  loading?: boolean;
  icon?: ReactNode;
  /** Ocupa el 100 % del ancho. */
  block?: boolean;
}

export function Button({
  variant = "secondary",
  size = "md",
  loading = false,
  icon,
  block = false,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cx("or-btn", `or-btn--${variant}`, `or-btn--${size}`, block && "or-btn--block", className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner size={14} label="" /> : icon ? <span className="or-btn__icon">{icon}</span> : null}
      <span className="or-btn__label">{children}</span>
    </button>
  );
}
