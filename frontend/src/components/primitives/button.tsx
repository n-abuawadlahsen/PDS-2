import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Slot } from "radix-ui";

const buttonVariants = cva("ui-button", {
  variants: {
    variant: {
      default: "primary",
      destructive: "danger",
      outline: "outline",
      secondary: "secondary",
      ghost: "quiet",
      link: "quiet",
    },
    size: {
      default: "",
      xs: "compact",
      sm: "compact",
      lg: "large",
      icon: "icon-button",
      "icon-xs": "icon-button",
      "icon-sm": "icon-button",
      "icon-lg": "icon-button",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
});

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : "button";

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
