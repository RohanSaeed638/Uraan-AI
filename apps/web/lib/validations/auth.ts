// Messages are keys of `auth.errors` in messages/*.json; the forms translate them.
import { z } from "zod";

export const loginSchema = z.object({
  email: z.email("emailInvalid"),
  password: z.string().min(8, "passwordShort"),
  remember: z.boolean().optional(),
});

export const registerSchema = loginSchema.extend({
  fullName: z.string().min(2, "nameRequired"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  path: ["confirmPassword"],
  message: "mismatch",
});

export const forgotPasswordSchema = z.object({
  email: z.email("emailInvalid"),
});

export const resetPasswordSchema = z
  .object({
    password: z.string().min(8, "passwordShort"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ["confirmPassword"],
    message: "mismatch",
  });

export type LoginForm = z.infer<typeof loginSchema>;
export type RegisterForm = z.infer<typeof registerSchema>;
export type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;