import { cn } from "../../lib/utils";

export const Button = ({ className, variant = "default", type = "button", ...props }) => {
  const variants = {
    default: "bg-[#007AFF] text-white hover:bg-[#1d8cff]",
    outline: "border border-white/20 text-white hover:bg-white/10",
    ghost: "text-white hover:bg-white/10",
    danger: "bg-[#ef4444] text-white hover:bg-[#f15c5c]",
  };

  return (
    <button
      type={type}
      className={cn(
        "rounded-sm px-4 py-2 text-sm font-semibold transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-[#007AFF] disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
};
