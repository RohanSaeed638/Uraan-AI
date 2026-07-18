"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { toast } from "sonner";

import {
  registerSchema,
  type RegisterForm as RegisterFormValues,
} from "@/lib/validations/auth";

import { authService } from "@/services/auth/auth";

import AuthCard from "./AuthCard";
import AuthHeader from "./AuthHeader";

import PasswordInput from "@/components/shared/PasswordInput";
import LoadingButton from "@/components/shared/LoadingButton";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterForm() {
  const router = useRouter();

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
        toast.error(error.message);
        return;
      }

      toast.success(
        "Account created successfully. Please verify your email."
      );

      reset();

      router.push("/login");
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
        title="Create Account 🚀"
        subtitle="Start your journey toward your dream career."
      />

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-5"
      >
        <div>
          <Label>Full Name</Label>

          <Input
            placeholder="Muhammad Ali"
            {...register("fullName")}
          />

          {errors.fullName && (
            <p className="text-sm text-red-500 mt-1">
              {errors.fullName.message}
            </p>
          )}
        </div>

        <div>
          <Label>Email</Label>

          <Input
            type="email"
            placeholder="you@example.com"
            {...register("email")}
          />

          {errors.email && (
            <p className="text-sm text-red-500 mt-1">
              {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <Label>Password</Label>

          <PasswordInput
            placeholder="********"
            {...register("password")}
          />

          {errors.password && (
            <p className="text-sm text-red-500 mt-1">
              {errors.password.message}
            </p>
          )}
        </div>

        <div>
          <Label>Confirm Password</Label>

          <PasswordInput
            placeholder="********"
            {...register("confirmPassword")}
          />

          {errors.confirmPassword && (
            <p className="text-sm text-red-500 mt-1">
              {errors.confirmPassword.message}
            </p>
          )}
        </div>

        <LoadingButton
          type="submit"
          loading={loading}
          className="w-full"
        >
          Create Account
        </LoadingButton>
      </form>

      <div className="mt-8 text-center text-sm">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-violet-600 hover:underline"
        >
          Login
        </Link>
      </div>
    </AuthCard>
  );
}