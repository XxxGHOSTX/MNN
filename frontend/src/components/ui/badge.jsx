import { cn } from "../../lib/utils";

const variantClass = {
  healthy: "border border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
  degraded: "border border-amber-500/25 bg-amber-500/10 text-amber-400",
  down: "border border-red-500/25 bg-red-500/10 text-red-400",
  mock: "border border-sky-500/25 bg-sky-500/10 text-sky-400",
};

export const Badge = ({ variant = "healthy", className, children, ...props }) => (
  <span
    className={cn(
      "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
      variantClass[variant] || variantClass.healthy,
      className
    )}
    {...props}
  >
    {children}
  </span>
);
