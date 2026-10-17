"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, MailCheck } from "lucide-react";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import {
  forgotPasswordSchema,
  type ForgotPasswordForm as ForgotPasswordFormValues,
} from "@/lib/validations/auth";
import { authService } from "@/services/auth/auth";

import AuthCard from "./AuthCard";
import AuthHeader from "./AuthHeader";
import LoadingButton from "@/components/shared/LoadingButton";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { buttonVariants } from "@/components/ui/button";

export default function ForgotPasswordForm() {
  const [loading, setLoading] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  async function onSubmit(data: ForgotPasswordFormValues) {
    try {
      setLoading(true);
      const { error } = await authService.resetPassword(data.email);

      if (error) {
        toast.error(error.message);
        return;
      }

      setSentTo(data.email);
    } catch (error) {
      console.error(error);
      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  if (sentTo) {
    return (
      <AuthCard>
        <div className="flex flex-col items-center py-4 text-center">
          <span className="flex size-14 items-center justify-center rounded-full bg-brand-violet/10">
            <MailCheck className="size-6 text-brand-violet" />
          </span>
          <h1 className="font-heading mt-5 text-xl font-bold text-foreground">
            Check your email
          </h1>
          <p className="mt-2 max-w-xs text-sm text-muted-foreground">
            We sent a password reset link to{" "}
            <span className="font-medium text-foreground">{sentTo}</span>.
          </p>
          <Link
            href="/login"
            className={buttonVariants({ variant: "outline", className: "mt-7 w-full" })}
          >
            Back to sign in
          </Link>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard>
      <Link
        href="/login"
        className="mb-5 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} /> Back to sign in
      </Link>

      <AuthHeader
        title="Forgot password?"
        subtitle="Enter your email and we'll send you a reset link."
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email address</Label>

          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            {...register("email")}
          />

          {errors.email && (
            <p className="text-sm text-destructive">
              {errors.email.message}
            </p>
          )}
        </div>

        <LoadingButton
          type="submit"
          loading={loading}
          className="w-full"
          size="lg"
        >
          Send Reset Link
        </LoadingButton>
      </form>
    </AuthCard>
  );
}
