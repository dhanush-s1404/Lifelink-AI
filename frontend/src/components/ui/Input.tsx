import { cn } from "@/lib/utils";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
  hint?: string;
};

export function Input({ label, error, hint, className, id, ...rest }: InputProps) {
  const inputId = id ?? rest.name;
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={cn(
          "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20 dark:border-slate-600 dark:bg-night-800 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-brand-500",
          error && "border-red-400 focus:border-red-500 focus:ring-red-500/20",
          className
        )}
        aria-invalid={error ? true : undefined}
        {...rest}
      />
      {error ? (
        <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p>
      ) : null}
    </div>
  );
}