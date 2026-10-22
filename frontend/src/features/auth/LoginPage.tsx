import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router";
import { login } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { CHECK_EMAIL_PATH, safeNext } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextField } from "../../components/ui/TextField";
import { authErrorInfo, type AuthErrorInfo } from "./authErrors";
import { FormSummary } from "./FormSummary";
import { GoogleLoginButton } from "./GoogleLoginButton";
import { loginSchema, type LoginValues } from "./schemas";

/**
 * Log in (screen 2). Notices for an ended session (`?session=ended`) and a failed Google login
 * (`?error=social`); wrong credentials and rate limits come back as form-level alerts.
 *
 * @returns The page.
 */
export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [failure, setFailure] = useState<AuthErrorInfo | null>(null);
  const mutation = useAuthMutation(login);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit((values) => {
    setFailure(null);
    mutation.mutate(values, {
      onSuccess: (viewer) =>
        void navigate(
          viewer.state === "pending_verification" ? CHECK_EMAIL_PATH : safeNext(params.get("next")),
          {
            state: { email: values.email },
          },
        ),
      onError: (error) => setFailure(authErrorInfo(error)),
    });
  });

  return (
    <>
      <div className="auth__intro">
        <h1>{t("login.title")}</h1>
        <p className="t-muted">{t("login.lead")}</p>
      </div>
      {params.get("session") === "ended" && <Alert tone="warning">{t("chat_error.session_ended")}</Alert>}
      {params.get("error") === "social" && <Alert tone="danger">{t("error.social")}</Alert>}
      {failure && (
        <Alert tone={failure.warning ? "warning" : "danger"} role="alert">
          {t(failure.key)}
        </Alert>
      )}
      <FormSummary show={Object.keys(errors).length > 0} />
      <GoogleLoginButton />
      <form className="form" noValidate onSubmit={(event) => void onSubmit(event)}>
        <TextField
          label={t("auth.email")}
          type="email"
          autoComplete="email"
          placeholder={t("auth.email_placeholder")}
          disabled={mutation.isPending}
          error={errors.email?.message && t(errors.email.message)}
          {...register("email")}
        />
        <PasswordField
          label={t("auth.password")}
          autoComplete="current-password"
          disabled={mutation.isPending}
          error={errors.password?.message && t(errors.password.message)}
          {...register("password")}
        />
        <Link to="/forgot-password">{t("login.forgot")}</Link>
        <div className="form__actions">
          <Button
            type="submit"
            variant="primary"
            block
            busy={mutation.isPending}
            busyLabel={t("login.submitting")}
          >
            {t("login.submit")}
          </Button>
        </div>
      </form>
      <p>
        {t("login.no_account")} <Link to="/signup">{t("login.signup_link")}</Link>
      </p>
    </>
  );
}
