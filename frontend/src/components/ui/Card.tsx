import { cn } from "@/lib/utils";

type CardProps = React.HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...rest }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200 bg-white shadow-card dark:border-slate-700/70 dark:bg-night-900",
        className
      )}
      {...rest}
    />
  );
}

export function CardHeader({ className, ...rest }: CardProps) {
  return (
    <div
      className={cn("border-b border-slate-100 px-5 py-4 dark:border-slate-800", className)}
      {...rest}
    />
  );
}

export function CardBody({ className, ...rest }: CardProps) {
  return <div className={cn("px-5 py-5", className)} {...rest} />;
}

export function CardTitle({ className, ...rest }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-base font-semibold text-slate-900 dark:text-white", className)} {...rest} />
  );
}