import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[#5B197B] text-white hover:bg-[#4A1463] shadow-md hover:shadow-lg transition-all",
        destructive:
          "bg-[#EF4444] text-white hover:bg-[#DC2626] shadow-sm",
        outline:
          "border-[0.5px] border-[#E5E5E5] bg-white hover:bg-[#E3F2FD] hover:border-[#64B5F6] text-[#1A237E]",
        secondary:
          "bg-[#64B5F6] text-[#1A237E] hover:bg-[#42A5F5] font-semibold",
        ghost: "hover:bg-[#E3F2FD] text-[#1A237E]",
        link: "text-[#1A237E] underline-offset-4 hover:underline hover:text-[#64B5F6]",
      },
      size: {
        default: "h-11 px-6 py-2",
        sm: "h-9 rounded-xl px-4",
        lg: "h-12 rounded-xl px-8",
        icon: "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }

