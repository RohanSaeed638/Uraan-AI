"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { toast } from "sonner";

import {
  registerSchema,
  type RegisterForm as RegisterFormValues,
} from "@/lib/validations/auth";

import { authService } from "@/services/auth/auth";
import { authErrorKey } from "@/lib/auth-errors";

import AuthCard from "./AuthCard";
import AuthHeader from "./AuthHeader";
import OAuthButtons from "./OAuthButtons";

import PasswordInput from "@/components/shared/PasswordInput";
import LoadingButton from "@/components/shared/LoadingButton";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterForm() {
  const router = useRouter();
  const t = useTranslations("auth");
  const tErrors = useTranslations("auth.errors");

  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  async function onSubmit(data: RegisterFormValues) {
    try {
      setLoading(true);

      const { data: result, error } =
        await authService.register(
          data.fullName,
          data.email,
          data.password
        );

      if (error) {
        const key = authErrorKey(error.message);

        toast.error(key ? tErrors(key) : error.message);
        return;
      }

      toast.success(t("created"));

      reset();

      router.push("/login");
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
        title={t("createTitle")}
        subtitle={t("createSubtitle")}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="fullName">{t("fullName")}</Label>

          <Input
            id="fullName"
            placeholder={t("fullNamePlaceholder")}
            {...register("fullName")}
          />

          {errors.fullName && (
            <p className="text-sm text-destructive">
              {tErrors(errors.fullName.message as "nameRequired")}
            </p>
          )}
        </div>

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

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="password">{t("password")}</Label>

            <PasswordInput
              id="password"
              placeholder={t("createPassword")}
              {...register("password")}
            />

            {errors.password && (
              <p className="text-sm text-destructive">
                {tErrors(errors.password.message as "passwordShort")}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="confirmPassword">{t("confirm")}</Label>

            <PasswordInput
              id="confirmPassword"
              placeholder={t("confirmPlaceholder")}
              {...register("confirmPassword")}
            />

            {errors.confirmPassword && (
              <p className="text-sm text-destructive">
                {tErrors(errors.confirmPassword.message as "mismatch")}
              </p>
            )}
          </div>
        </div>

        <LoadingButton
          type="submit"
          loading={loading}
          className="w-full"
          size="lg"
        >
          {t("createAccount")}
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
        {t.rich("haveAccount", {
          link: (chunks) => (
            <Link
              href="/login"
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
