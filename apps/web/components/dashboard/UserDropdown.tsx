"use client";

import { User } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { authService } from "@/services/auth/auth";

import { Button } from "@/components/ui/button";

export default function UserDropdown({
  user,
}: {
  user: User;
}) {
  const router = useRouter();

  async function logout() {
    await authService.logout();

    toast.success("Logged out");

    router.replace("/login");

    router.refresh();
  }

  return (
    <div className="flex items-center gap-4">
      <div className="text-right">
        <p className="font-medium">
          {user.user_metadata.full_name}
        </p>

        <p className="text-xs text-muted-foreground">
          {user.email}
        </p>
      </div>

      <Button
        variant="outline"
        onClick={logout}
      >
        Logout
      </Button>
    </div>
  );
}