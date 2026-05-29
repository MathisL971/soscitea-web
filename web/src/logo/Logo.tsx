import type { CSSProperties } from "react";
import {
  CUP_BODY,
  HANDLE,
  LOGO_VIEWBOX,
  MOUTH,
  SAUCER,
  STEAM_CENTER,
  STEAM_LEFT,
  STEAM_RIGHT,
  TEA,
} from "./paths";

export type LogoVariant = "mark" | "wordmark" | "lockup";
export type LogoTone = "default" | "mono" | "inverse";

export interface LogoProps {
  variant?: LogoVariant;
  tone?: LogoTone;
  className?: string;
  style?: CSSProperties;
  size?: number;
  title?: string;
}

const toneClass: Record<LogoTone, string> = {
  default: "logo--default",
  mono: "logo--mono",
  inverse: "logo--inverse",
};

export function Logo({
  variant = "mark",
  tone = "default",
  className,
  style,
  size,
  title,
}: LogoProps) {
  const classes = ["logo", `logo--${variant}`, toneClass[tone], className]
    .filter(Boolean)
    .join(" ");
  const dimStyle = size
    ? ({ ...style, "--logo-size": `${size}px` } as CSSProperties)
    : style;

  if (variant === "wordmark") {
    return <LogoWordmark className={classes} style={dimStyle} title={title} />;
  }

  if (variant === "lockup") {
    return <LogoLockup className={classes} style={dimStyle} title={title} />;
  }

  return <LogoMark className={classes} style={dimStyle} title={title} decorative={!title} />;
}

interface MarkProps {
  className?: string;
  style?: CSSProperties;
  title?: string;
  decorative?: boolean;
}

export function LogoMark({ className, style, title, decorative = true }: MarkProps) {
  return (
    <svg
      className={["logo__mark", className].filter(Boolean).join(" ")}
      style={style}
      viewBox={LOGO_VIEWBOX}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role={decorative ? undefined : "img"}
      aria-hidden={decorative ? true : undefined}
      aria-label={decorative ? undefined : title}
    >
      {title && !decorative ? <title>{title}</title> : null}

      <g className="logo__scene">
        <path d={SAUCER} className="logo__stroke" />
        <path d={CUP_BODY} className="logo__cup" />
        <path d={HANDLE} className="logo__stroke" />
        <ellipse cx={MOUTH.cx} cy={MOUTH.cy} rx={MOUTH.rx} ry={MOUTH.ry} className="logo__cup" />
        <path d={TEA} className="logo__tea" />
        <path d={STEAM_LEFT} className="logo__steam logo__steam--side" />
        <path d={STEAM_CENTER} className="logo__steam logo__steam--center" />
        <path d={STEAM_RIGHT} className="logo__steam logo__steam--side" />
      </g>
    </svg>
  );
}

function LogoWordmark({ className, style, title }: MarkProps) {
  return (
    <span
      className={className}
      style={style}
      role={title ? "img" : undefined}
      aria-label={title}
    >
      <span className="logo__word logo__word--sosci">Sosci</span>
      <span className="logo__word logo__word--tea">tea</span>
    </span>
  );
}

function LogoLockup({ className, style, title }: MarkProps) {
  return (
    <div className={className} style={style} role={title ? "img" : undefined} aria-label={title}>
      <LogoMark className="logo__lockup-mark" decorative />
      <LogoWordmark className="logo__lockup-type" />
    </div>
  );
}
