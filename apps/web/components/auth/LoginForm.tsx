"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { toast } from "sonner";

import {
  loginSchema,
  type LoginForm as LoginFormValues,
} from "@/lib/validations/auth";

import { authService } from "@/services/auth/auth";
import { authErrorKey } from "@/lib/auth-errors";

import AuthCard from "./AuthCard";
import AuthHeader from "./AuthHeader";
import OAuthButtons from "./OAuthButtons";
import PasswordInput from "@/components/shared/PasswordInput";
import { setRememberMe } from "@/services/auth/session-preference";
import LoadingButton from "@/components/shared/LoadingButton";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginForm() {
  const router = useRouter();
  const t = useTranslations("auth");
  const tErrors = useTranslations("auth.errors");

  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginFormValues) {
    try {
      setLoading(true);

      const { data: result, error } =
        await authService.login(
          data.email,
          data.password
        );

      if (error) {
        const key = authErrorKey(error.message);

        toast.error(key ? tErrors(key) : error.message);
        return;
      }

      if (!result.session) {
        toast.error(tErrors("loginFailed"));
        return;
      }

      setRememberMe(data.remember !== false);

      toast.success(t("welcomeToast"));

      router.push("/dashboard");

      router.refresh();
    } catch (error) {
      console.error(error);

      toast.error(tErrors("generic"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard>
      <AuthHeader
        title={t("welcomeBack")}
        subtitle={t("signInSubtitle")}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">{t("email")}</Label>

          <Input
            id="email"
            type="email"
            placeholder={t("emailPlaceholder")}
            {...register("email")}
          />

          {errors.email && (
            <p className="text-sm text-destructive">
              {tErrors(errors.email.message as "emailInvalid")}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">{t("password")}</Label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
            >
              {t("forgot")}
            </Link>
          </div>

          <PasswordInput
            id="password"
            placeholder={t("passwordPlaceholder")}
            {...register("password")}
          />

          {errors.password && (
            <p className="text-sm text-destructive">
              {tErrors(errors.password.message as "passwordShort")}
            </p>
          )}
        </div>

        <label className="flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            className="size-4 accent-gold"
            defaultChecked
            {...register("remember")}
          />
          {t("remember")}
        </label>

        <LoadingButton
          type="submit"
          loading={loading}
          className="w-full"
          size="lg"
        >
          {t("signIn")}
        </LoadingButton>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs text-muted-foreground">
          {t("orContinue")}
        </span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <OAuthButtons />

      <p className="mt-7 text-center text-sm text-muted-foreground">
        {t.rich("noAccount", {
          link: (chunks) => (
            <Link
              href="/register"
              className="font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
            >
              {chunks}
            </Link>
          ),
        })}
      </p>
    </AuthCard>
  );
}
