"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { toast } from "sonner";

import {
  loginSchema,
  type LoginForm as LoginFormValues,
} from "@/lib/validations/auth";

import { authService } from "@/services/auth/auth";

import AuthCard from "./AuthCard";
import AuthHeader from "./AuthHeader";
import OAuthButtons from "./OAuthButtons";
import PasswordInput from "@/components/shared/PasswordInput";
import LoadingButton from "@/components/shared/LoadingButton";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginForm() {
  const router = useRouter();

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
        toast.error(error.message);
        return;
      }

      if (!result.session) {
        toast.error("Login failed.");
        return;
      }

      toast.success("Welcome back!");

      router.push("/dashboard");

      router.refresh();
    } catch (error) {
      console.error(error);

      toast.error("Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard>
      <AuthHeader
        title="Welcome back!"
        subtitle="Sign in to continue your journey."
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

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-brand-violet hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          <PasswordInput
            id="password"
            placeholder="Enter your password"
            {...register("password")}
          />

          {errors.password && (
            <p className="text-sm text-destructive">
              {errors.password.message}
            </p>
          )}
        </div>

        <LoadingButton
          type="submit"
          loading={loading}
          className="w-full"
          size="lg"
        >
          Sign In
        </LoadingButton>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs text-muted-foreground">
          or continue with
        </span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <OAuthButtons />

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="font-medium text-brand-violet hover:underline"
        >
          Sign up
        </Link>
      </p>
    </AuthCard>
  );
}
