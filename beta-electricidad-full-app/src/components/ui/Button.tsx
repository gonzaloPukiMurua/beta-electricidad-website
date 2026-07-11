import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center font-semibold tracking-wide transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 shadow-sm rounded-lg",
        secondary:
          "border border-[var(--outline-variant)] text-[var(--primary)] hover:bg-[var(--surface-container)] rounded-lg",
        ghost:
          "text-[var(--on-surface-variant)] hover:text-[var(--primary)] hover:bg-[var(--surface-container)] rounded-lg",
        whatsapp:
          "bg-[#25d366] text-white hover:brightness-110 shadow-lg rounded-full",
        danger:
          "bg-[var(--secondary)] text-white hover:opacity-90 shadow-sm rounded-lg",
      },
      size: {
        sm: "px-4 py-2 text-xs",
        md: "px-6 py-2.5 text-sm",
        lg: "px-8 py-4 text-base",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { buttonVariants };