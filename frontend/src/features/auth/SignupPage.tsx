import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";
import { signup } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { CHECK_EMAIL_PATH, HOME_PATH } from "../../app/guards";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextField } from "../../components/ui/TextField";
import { TURNSTILE_SITE_KEY } from "../../config";
import { AuthErrorAlert } from "./AuthErrorAlert";
import { GoogleLoginButton } from "./GoogleLoginButton";
import { MIN_PASSWORD_LENGTH, signupSchema, type SignupValues } from "./schemas";
import { TurnstileWidget } from "./TurnstileWidget";

/**
 * Email + password signup with Turnstile. On success the guards route to "check your email".
 *
 * @returns The page.
 */
export function SignupPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [turnstileToken, setTurnstileToken] = useState("");
  const mutation = useAuthMutation(signup);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupValues>({ resolver: zodResolver(signupSchema) });
  const waitingForTurnstile = TURNSTILE_SITE_KEY !== "" && turnstileToken === "";

  const onSubmit = handleSubmit((values) =>
    mutation.mutate(
      { ...values, turnstile_token: turnstileToken },
      {
        onSuccess: (viewer) =>
          void navigate(viewer.state === "pending_verification" ? CHECK_EMAIL_PATH : HOME_PATH, {
            state: { email: values.email },
          }),
      },
    ),
  );

  return (
    <>
      <h1>{t("auth.signup.title")}</h1>
      <GoogleLoginButton />
      <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
        <TextField
          label={t("auth.fields.email")}
          type="email"
          autoComplete="email"
          error={errors.email?.message && t(errors.email.message)}
          {...register("email")}
        />
        <PasswordField
          label={t("auth.fields.password")}
          autoComplete="new-password"
          hint={t("auth.fields.passwordHint", { count: MIN_PASSWORD_LENGTH })}
          error={errors.password?.message && t(errors.password.message, { count: MIN_PASSWORD_LENGTH })}
          {...register("password")}
        />
        {TURNSTILE_SITE_KEY && (
          <TurnstileWidget
            siteKey={TURNSTILE_SITE_KEY}
            language={i18n.language}
            onToken={setTurnstileToken}
          />
        )}
        <AuthErrorAlert error={mutation.error} />
        <button
          type="submit"
          className="min-h-11 border"
          disabled={mutation.isPending || waitingForTurnstile}
        >
          {t("auth.signup.submit")}
        </button>
      </form>
      <p>
        {t("auth.signup.haveAccount")} <Link to="/login">{t("auth.signup.loginLink")}</Link>
      </p>
    </>
  );
}
