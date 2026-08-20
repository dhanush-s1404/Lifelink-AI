import { cn } from "@/lib/utils";

type BadgeTone = "success" | "warning" | "danger" | "neutral" | "brand";

const tones: Record<BadgeTone, string> = {
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  neutral: "badge-neutral",
  brand: "badge-brand",
};

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone;
  icon?: React.ReactNode;
};

export function Badge({ tone = "neutral", icon, className, children, ...rest }: BadgeProps) {
  return (
    <span className={cn("badge", tones[tone], className)} {...rest}>
      {icon}
      {children}
    </span>
  );
}