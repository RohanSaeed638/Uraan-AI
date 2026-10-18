"use client";

import { toast } from "sonner";

import { Card } from "@/components/ui/card";
import ThemeToggle from "@/components/shared/ThemeToggle";

export default function AppearanceTab() {
  return (
    <Card className="max-w-xl p-7">
      <h2 className="text-sm font-semibold">Appearance</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Choose how Uraan AI looks. &ldquo;System&rdquo; follows your device and
        switches automatically between light and dark. Your choice follows you
        to your other devices.
      </p>
      <div className="mt-5">
        <ThemeToggle
          onSaveError={() =>
            toast.error(
              "Applied here, but couldn't save it to your account. It may not carry over to other devices."
            )
          }
        />
      </div>
    </Card>
  );
}
