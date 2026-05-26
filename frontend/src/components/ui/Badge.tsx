import clsx from "clsx";

type Variant = "default" | "success" | "warning" | "danger" | "info";

const VARIANT_CLASS: Record<Variant, string> = {
  default: "bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200",
  success: "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300",
  warning: "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
  danger: "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300",
  info: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
};

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        VARIANT_CLASS[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
