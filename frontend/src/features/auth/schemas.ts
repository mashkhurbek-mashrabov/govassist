/** zod schemas mirroring the backend rules. Messages are copy.md keys, translated where shown. */
import { z } from "zod";
import { MIN_PASSWORD_LENGTH } from "../../lib/passwordStrength";

/** A required, valid email. */
const email = z.email({ error: "error.email_invalid" });
/** A password meeting the length rule. */
const password = z.string().min(MIN_PASSWORD_LENGTH, { error: "error.password_short" });
/** Any non-empty value. */
const required = z.string().min(1, { error: "error.required" });

/** Signup form. */
export const signupSchema = z.object({ email, password });
/** Login form: any non-empty password (the backend decides). */
export const loginSchema = z.object({ email, password: required });
/** A form with just an email (forgot password, resend link). */
export const emailSchema = z.object({ email });
/** Reset-password form. */
export const resetSchema = z.object({ password });
/**
 * Change-password form. Google-only accounts (`has_password: false`) set a first password without the current one.
 *
 * @param hasPassword `Me.has_password`.
 * @returns The schema.
 */
export function changePasswordSchema(hasPassword: boolean) {
  return z.object({ current: hasPassword ? required : z.string().optional(), password });
}

export type SignupValues = z.infer<typeof signupSchema>;
export type LoginValues = z.infer<typeof loginSchema>;
export type EmailValues = z.infer<typeof emailSchema>;
export type ResetValues = z.infer<typeof resetSchema>;
export type ChangePasswordValues = z.infer<ReturnType<typeof changePasswordSchema>>;
