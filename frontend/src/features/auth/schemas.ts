/** zod schemas mirroring the backend rules. Error messages are i18n keys, translated where shown. */
import { z } from "zod";

/** Minimum password length (backend: Django validator, ≥ 10). */
export const MIN_PASSWORD_LENGTH = 10;

/** A required, valid email. */
const email = z.email({ error: "auth.errors.invalidEmail" });
/** A password meeting the length rule. */
const password = z.string().min(MIN_PASSWORD_LENGTH, { error: "auth.errors.passwordTooShort" });

/** Signup form. */
export const signupSchema = z.object({ email, password });
/** Login form: any non-empty password (the backend decides). */
export const loginSchema = z.object({
  email,
  password: z.string().min(1, { error: "auth.errors.required" }),
});
/** Forgot-password form. */
export const forgotSchema = z.object({ email });
/** New password + confirmation. */
export const newPasswordSchema = z
  .object({ password, confirm: z.string() })
  .refine((values) => values.password === values.confirm, {
    error: "auth.errors.passwordsDiffer",
    path: ["confirm"],
  });
/**
 * Change-password form (Settings). Google-only accounts (`has_password: false`) set a first password,
 * so the current one is not asked for.
 *
 * @param hasPassword `Me.has_password`.
 * @returns The schema.
 */
export function changePasswordSchema(hasPassword: boolean) {
  return z.object({
    current: hasPassword ? z.string().min(1, { error: "auth.errors.required" }) : z.string().optional(),
    password,
  });
}

export type SignupValues = z.infer<typeof signupSchema>;
export type LoginValues = z.infer<typeof loginSchema>;
export type ForgotValues = z.infer<typeof forgotSchema>;
export type NewPasswordValues = z.infer<typeof newPasswordSchema>;
export type ChangePasswordValues = z.infer<ReturnType<typeof changePasswordSchema>>;
