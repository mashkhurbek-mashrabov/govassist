import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router";
import { resendVerification } from "../../api/endpoints";
import { ApiError } from "../../api/http";
import { Alert } from "../../components/ui/Alert";
import { TextField } from "../../components/ui/TextField";
import { retryMinutes } from "../../lib/format";
import { forgotSchema, type ForgotValues } from "./schemas";

/** Navigation state signup/login pass here so the address is prefilled. */
export interface CheckEmailState {
  email?: string;
}

/**
 * Translated text for a failed resend: the wait time on 429, else a generic error.
 *
 * @param error What the resend threw.
 * @param t Translation function.
 * @returns The message.
 */
function resendErrorText(
  error: unknown,
  t: (key: string, options?: Record<string, number>) => string,
): string {
  if (error instanceof ApiError && error.code === "rate_limited" && error.retryAfter !== null) {
    return t("auth.checkEmail.resendWait", { minutes: retryMinutes(error.retryAfter) });
  }
  return t("auth.errors.generic");
}

/**
 * "Check your email" after signup: resend the link (`POST /auth/resend-verification`) or go back to
 * signup to use another address (there is no change-email endpoint).
 *
 * @returns The page.
 */
export function CheckEmailPage() {
  const { t } = useTranslation();
  const state = useLocation().state as CheckEmailState | null;
  const resend = useMutation({ mutationFn: resendVerification });
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: state?.email ?? "" },
  });

  const onSubmit = handleSubmit(({ email }) => resend.mutate(email));

  return (
    <>
      <h1>{t("auth.checkEmail.title")}</h1>
      <p>{t("auth.checkEmail.body")}</p>
      <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
        <TextField
          label={t("auth.fields.email")}
          type="email"
          autoComplete="email"
          error={errors.email?.message && t(errors.email.message)}
          {...register("email")}
        />
        {resend.isSuccess && <Alert>{t("auth.checkEmail.resent")}</Alert>}
        {resend.isError && <Alert tone="error">{resendErrorText(resend.error, t)}</Alert>}
        <button type="submit" className="min-h-11 border" disabled={resend.isPending}>
          {t("auth.checkEmail.resend")}
        </button>
      </form>
      <Link to="/signup">{t("auth.checkEmail.otherEmail")}</Link>
      <Link to="/login">{t("auth.backToLogin")}</Link>
    </>
  );
}
