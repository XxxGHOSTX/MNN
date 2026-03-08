import { cn } from "../../lib/utils";

export const Input = ({ className, ...props }) => (
  <input
    className={cn(
      "w-full rounded-sm border border-white/15 bg-black/30 px-3 py-2 text-sm text-white outline-none transition-colors duration-200 placeholder:text-zinc-500 focus:border-[#007AFF] focus:ring-1 focus:ring-[#007AFF]",
      className
    )}
    {...props}
  />
);
