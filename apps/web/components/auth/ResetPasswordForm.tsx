"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { Loader2, MailX } from "lucide-react";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import {
  resetPasswordSchema,
  type ResetPasswordForm as ResetPasswordFormValues,
} from "@/lib/validations/auth";
import { authService } from "@/services/auth/auth";
import { authErrorKey } from "@/lib/auth-errors";

import AuthCard from "./AuthCard";
import AuthHeader from "./AuthHeader";
import LoadingButton from "@/components/shared/LoadingButton";
import PasswordInput from "@/components/shared/PasswordInput";

import { Label } from "@/components/ui/label";
import { buttonVariants } from "@/components/ui/button";

type Status = "checking" | "ready" | "expired";

/**
 * Where the link in the password-reset email lands (via /auth/callback, which
 * turns the link into a signed-in session). Without that session the link was
 * already used, expired, or opened in another browser.
 */
export default function ResetPasswordForm() {
  const router = useRouter();
  const t = useTranslations("auth");
  const tErrors = useTranslations("auth.errors");
  const [status, setStatus] = useState<Status>("checking");
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    let cancelled = false;

    authService
      .getUser()
      .then(({ data }) => {
        if (!cancelled) setStatus(data.user ? "ready" : "expired");
      })
      .catch(() => {
        if (!cancelled) setStatus("expired");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(values: ResetPasswordFormValues) {
    setSaving(true);

    try {
      const { error } = await authService.updatePassword(values.password);

      if (error) {
        const key = authErrorKey(error.message);

        setError("password", { message: key ? tErrors(key) : error.message });
        return;
      }

      toast.success(t("updated"));
      router.replace("/dashboard");
      router.refresh();
    } catch (error) {
      console.error(error);
      toast.error(tErrors("generic"));
    } finally {
      setSaving(false);
    }
  }

  if (status === "checking") {
    return (
      <AuthCard>
        <div className="flex justify-center py-10" role="status" aria-label={t("checkingLink")}>
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      </AuthCard>
    );
  }

  if (status === "expired") {
    return (
      <AuthCard>
        <div className="flex flex-col items-center py-4 text-center">
          <span className="flex size-14 items-center justify-center rounded-full bg-destructive/10">
            <MailX className="size-6 text-destructive" />
          </span>
          <h1 className="font-heading mt-5 text-xl font-bold text-foreground">
            {t("expiredTitle")}
          </h1>
          <p className="mt-2 max-w-xs text-sm text-muted-foreground">
            {t("expiredText")}
          </p>
          <Link
            href="/forgot-password"
            className={buttonVariants({ className: "mt-7 w-full" })}
          >
            {t("sendNew")}
          </Link>
          <Link
            href="/login"
            className="mt-3 text-sm text-muted-foreground hover:text-foreground"
          >
            {t("backToSignIn")}
          </Link>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard>
      <AuthHeader
        title={t("newPasswordTitle")}
        subtitle={t("newPasswordSubtitle")}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="password">{t("newPassword")}</Label>
          <PasswordInput
            id="password"
            autoComplete="new-password"
            placeholder={t("newPasswordPlaceholder")}
            {...register("password")}
          />
          {errors.password && (
            <p role="alert" className="text-sm text-destructive">
              {tErrors(errors.password.message as "passwordShort")}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">{t("confirmNew")}</Label>
          <PasswordInput
            id="confirmPassword"
            autoComplete="new-password"
            placeholder={t("confirmNewPlaceholder")}
            {...register("confirmPassword")}
          />
          {errors.confirmPassword && (
            <p role="alert" className="text-sm text-destructive">
              {tErrors(errors.confirmPassword.message as "mismatch")}
            </p>
          )}
        </div>

        <LoadingButton type="submit" loading={saving} className="w-full" size="lg">
          {t("update")}
        </LoadingButton>
      </form>
    </AuthCard>
  );
}
