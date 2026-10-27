"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Eye, EyeOff } from "lucide-react";

import { Input } from "@/components/ui/input";

const PasswordInput = React.forwardRef<
  HTMLInputElement,
  React.ComponentProps<typeof Input>
>((props, ref) => {
  const t = useTranslations("auth");
  const [show, setShow] = React.useState(false);

  return (
    <div className="relative">
      <Input
        ref={ref}
        {...props}
        type={show ? "text" : "password"}
      />

      <button
        type="button"
        onClick={() => setShow(!show)}
        aria-label={show ? t("hide") : t("show")}
        aria-pressed={show}
        className="absolute end-3 top-1/2 -translate-y-1/2"
      >
        {show ? (
          <EyeOff className="h-4 w-4" size={18}/>
        ) : (
          <Eye className="h-4 w-4" size={18}/>
        )}
      </button>
    </div>
  );
});

PasswordInput.displayName = "PasswordInput";

export default PasswordInput;