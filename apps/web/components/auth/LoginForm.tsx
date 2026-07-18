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
        title="Welcome Back 👋"
        subtitle="Sign in to continue your learning journey."
      />

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-5"
      >
        <div>
          <Label>Email</Label>

          <Input
            type="email"
            placeholder="you@example.com"
            {...register("email")}
          />

          {errors.email && (
            <p className="text-red-500 text-sm mt-1">
              {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <Label>Password</Label>

          <PasswordInput
            placeholder="••••••••"
            {...register("password")}
          />

          {errors.password && (
            <p className="text-red-500 text-sm mt-1">
              {errors.password.message}
            </p>
          )}
        </div>

        <div className="flex justify-end">
          <Link
            href="/forgot-password"
            className="text-sm text-violet-600 hover:underline"
          >
            Forgot password?
          </Link>
        </div>

        <LoadingButton
          type="submit"
          loading={loading}
          className="w-full"
        >
          Login
        </LoadingButton>
      </form>

      <div className="mt-8 text-center text-sm">
        Don't have an account?{" "}
        <Link
          href="/register"
          className="font-medium text-violet-600 hover:underline"
        >
          Register
        </Link>
      </div>
    </AuthCard>
  );
}