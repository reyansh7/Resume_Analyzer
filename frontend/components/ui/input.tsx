import { forwardRef, InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-11 w-full rounded-xl border border-input bg-white/70 px-3 text-sm shadow-sm transition focus:border-primary focus:ring-2 focus:ring-primary/30 dark:bg-white/10",
          className
        )}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";
