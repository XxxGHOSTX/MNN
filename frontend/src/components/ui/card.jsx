import { cn } from "../../lib/utils";

export const Card = ({ className, ...props }) => (
  <section
    className={cn(
      "rounded-sm border border-white/10 bg-[#0A0A0A] p-6 shadow-[0_0_0_1px_rgba(255,255,255,0.05)]",
      className
    )}
    {...props}
  />
);
