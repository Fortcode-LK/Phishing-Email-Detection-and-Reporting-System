import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  icon: string;
  error?: string;
  rightSlot?: ReactNode;
}

const FormField = forwardRef<HTMLInputElement, FormFieldProps>(function FormField(
  {
    id,
    label,
    icon,
    error,
    rightSlot,
    ...inputProps
  },
  ref
) {
  return (
    <div className="space-y-2">
      <label
        htmlFor={id}
        className="block text-slate-300 text-xs font-semibold uppercase tracking-wider px-1"
      >
        {label}
      </label>
      <div className="relative group">
        <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-xl group-focus-within:text-primary transition-colors select-none pointer-events-none">
          {icon}
        </span>
        <input
          id={id}
          ref={ref}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          className={[
            "w-full h-14 pl-12 rounded-xl border bg-slate-900/50 text-slate-100",
            "placeholder:text-slate-600 transition-all backdrop-blur-sm",
            "focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary",
            rightSlot ? "pr-12" : "pr-4",
            error
              ? "border-red-500/70 focus:ring-red-500/30 focus:border-red-500"
              : "border-slate-800",
          ].join(" ")}
          {...inputProps}
        />
        {rightSlot && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            {rightSlot}
          </div>
        )}
      </div>
      {error && (
        <p
          id={`${id}-error`}
          role="alert"
          className="text-red-400 text-xs px-1 flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-sm">error</span>
          {error}
        </p>
      )}
    </div>
  );
});

export default FormField;
