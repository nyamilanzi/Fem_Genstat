import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-11 w-full rounded-xl border-[0.5px] border-[#E5E5E5] bg-white px-4 py-2.5 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-[#737373] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5B197B] focus-visible:border-[#5B197B] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 text-[#171717] transition-all",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }

