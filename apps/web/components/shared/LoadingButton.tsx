"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function LoadingButton({
  loading,
  children,
  ...props
}: React.ComponentProps<typeof Button> & {
  loading?: boolean;
}) {
  return (
    <Button
      {...props}
      disabled={loading || props.disabled}
    >
      {loading && (
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      )}

      {children}
    </Button>
  );
}