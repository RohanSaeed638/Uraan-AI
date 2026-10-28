"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { User } from "@supabase/supabase-js";
import { toast } from "sonner";

import { patchProfile } from "@/lib/api/profile";
import { apiErrorMessage } from "@/lib/profile-options";
import { authService } from "@/services/auth/auth";
import { useAuthStore } from "@/store/auth";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import LoadingButton from "@/components/shared/LoadingButton";

const MIN_PASSWORD = 8;

function providersOf(user: User): string[] {
  const list = user.app_metadata?.providers;

  if (Array.isArray(list) && list.length > 0) return list as string[];

  return user.app_metadata?.provider ? [user.app_metadata.provider as string] : [];
}

export default function AccountTab({ user }: { user: User }) {
  const router = useRouter();
  const t = useTranslations("settings.account");

  const providerLabel = (p: string) =>
    p === "email" ? t("providerEmail") : p[0].toUpperCase() + p.slice(1);
  const setUser = useAuthStore((state) => state.setUser);
  const clearUser = useAuthStore((state) => state.logout);

  const providers = providersOf(user);
  const hasPassword = providers.includes("email");
  const email = user.email ?? "";

  // ---- name
  const [fullName, setFullName] = useState(
    (user.user_metadata?.full_name as string) ?? ""
  );
  const [savingName, setSavingName] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);

  const initials = (fullName || email || "U")
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    const name = fullName.trim().replace(/\s+/g, " ");

    if (!name) {
      setNameError(t("nameRequired"));
      return;
    }

    setSavingName(true);
    setNameError(null);

    try {
      // The profile table feeds the leaderboard, resume and portfolio; the
      // login's display name feeds the greeting. Keep both the same.
      await patchProfile({ full_name: name });

      const { data, error } = await authService.updateFullName(name);
      if (error) throw error;
      if (data.user) setUser(data.user);

      setFullName(name);
      toast.success(t("nameUpdated"));
      router.refresh();
    } catch (err) {
      setNameError(apiErrorMessage(err, t("nameFailed")));
    } finally {
      setSavingName(false);
    }
  }

  // ---- email
  const [newEmail, setNewEmail] = useState("");
  const [savingEmail, setSavingEmail] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);

  async function changeEmail(e: React.FormEvent) {
    e.preventDefault();
    const next = newEmail.trim().toLowerCase();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(next)) {
      setEmailError(t("emailInvalid"));
      return;
    }

    if (next === email.toLowerCase()) {
      setEmailError(t("emailSame"));
      return;
    }

    setSavingEmail(true);
    setEmailError(null);

    try {
      const { error } = await authService.updateEmail(next);
      if (error) throw error;

      setNewEmail("");
      toast.success(t("emailSent"));
    } catch (err) {
      setEmailError(
        err instanceof Error ? err.message : t("emailFailed")
      );
    } finally {
      setSavingEmail(false);
    }
  }

  // ---- password
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();

    if (!current) return setPasswordError(t("currentRequired"));
    if (next.length < MIN_PASSWORD) {
      return setPasswordError(t("passwordShort", { count: MIN_PASSWORD }));
    }
    if (next === current) {
      return setPasswordError(t("passwordSame"));
    }
    if (next !== confirm) return setPasswordError(t("passwordMismatch"));

    setSavingPassword(true);
    setPasswordError(null);

    try {
      // Confirms the current password first, so a borrowed session can't
      // take over the account.
      const check = await authService.verifyPassword(email, current);
      if (check.error) {
        setPasswordError(t("currentWrong"));
        return;
      }

      const { error } = await authService.updatePassword(next);
      if (error) throw error;

      setCurrent("");
      setNext("");
      setConfirm("");
      toast.success(t("passwordChanged"));
    } catch (err) {
      setPasswordError(
        err instanceof Error ? err.message : t("passwordFailed")
      );
    } finally {
      setSavingPassword(false);
    }
  }

  // ---- sessions
  const [signingOut, setSigningOut] = useState(false);

  async function signOutEverywhere() {
    if (
      !window.confirm(t("signOutConfirm"))
    ) {
      return;
    }

    setSigningOut(true);
    clearUser();

    try {
      await authService.logoutEverywhere();
    } finally {
      window.location.href = "/login";
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <Card className="p-7">
        <h2 className="text-sm font-semibold">{t("profileTitle")}</h2>

        <div className="mt-5 flex items-center gap-4">
          <Avatar size="lg">
            <AvatarImage src={user.user_metadata?.avatar_url} />
            <AvatarFallback className="bg-brand-violet text-white">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="break-words text-sm font-medium">
              {fullName || t("yourName")}
            </p>
            <p className="break-all text-xs text-muted-foreground">{email}</p>
          </div>
        </div>

        <form onSubmit={saveName} className="mt-6 space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="fullName">{t("fullName")}</Label>
            <Input
              id="fullName"
              value={fullName}
              maxLength={100}
              onChange={(e) => setFullName(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              {t("fullNameHint")}
            </p>
          </div>

          {nameError && (
            <p role="alert" className="text-sm text-destructive">
              {nameError}
            </p>
          )}

          <LoadingButton type="submit" loading={savingName}>
            {t("saveName")}
          </LoadingButton>
        </form>
      </Card>

      <Card className="p-7">
        <h2 className="text-sm font-semibold">{t("emailTitle")}</h2>
        <p className="mt-1 break-all text-sm text-muted-foreground">{email}</p>

        {hasPassword ? (
          <form onSubmit={changeEmail} className="mt-5 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="newEmail">{t("newEmail")}</Label>
              <Input
                id="newEmail"
                type="email"
                autoComplete="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                {t("newEmailHint")}
              </p>
            </div>

            {emailError && (
              <p role="alert" className="text-sm text-destructive">
                {emailError}
              </p>
            )}

            <LoadingButton type="submit" loading={savingEmail}>
              {t("changeEmail")}
            </LoadingButton>
          </form>
        ) : (
          <p className="mt-3 text-xs text-muted-foreground">
            {t("emailFromProvider", {
              providers: providers.map(providerLabel).join(", ") || t("providerFallback"),
            })}
          </p>
        )}
      </Card>

      <Card className="p-7">
        <h2 className="text-sm font-semibold">{t("security")}</h2>

        {hasPassword ? (
          <form onSubmit={changePassword} className="mt-5 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="currentPassword">{t("currentPassword")}</Label>
              <Input
                id="currentPassword"
                type="password"
                autoComplete="current-password"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="newPassword">{t("newPassword")}</Label>
              <Input
                id="newPassword"
                type="password"
                autoComplete="new-password"
                value={next}
                onChange={(e) => setNext(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                {t("newPasswordHint", { count: MIN_PASSWORD })}
              </p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirmPassword">{t("confirmPassword")}</Label>
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>

            {passwordError && (
              <p role="alert" className="text-sm text-destructive">
                {passwordError}
              </p>
            )}

            <LoadingButton type="submit" loading={savingPassword}>
              {t("changePassword")}
            </LoadingButton>
          </form>
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">
            {t("noPassword", {
              providers: providers.map(providerLabel).join(", ") || t("providerGeneric"),
            })}
          </p>
        )}

        <div className="mt-6 border-t pt-5">
          <p className="text-sm font-medium">{t("signOutEverywhere")}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("signOutText")}
          </p>
          <LoadingButton
            type="button"
            variant="outline"
            className="mt-3"
            loading={signingOut}
            onClick={signOutEverywhere}
          >
            {t("signOutAll")}
          </LoadingButton>
        </div>
      </Card>
    </div>
  );
}
