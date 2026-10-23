import { zodResolver } from "@hookform/resolvers/zod";
import { CircleCheck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";
import { signup } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { CHECK_EMAIL_PATH, HOME_PATH } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { FieldError } from "../../components/ui/FieldError";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextField } from "../../components/ui/TextField";
import { TURNSTILE_SITE_KEY } from "../../config";
import { authErrorInfo } from "./authErrors";
import { FormSummary } from "./FormSummary";
import { GoogleLoginButton } from "./GoogleLoginButton";
import { PrivacyNote } from "./PrivacyNote";
import { signupSchema, type SignupValues } from "./schemas";
import { TurnstileWidget } from "./TurnstileWidget";

/** Id of the Turnstile error line. */
const TURNSTILE_ERROR_ID = "turnstile-error";

/**
 * Sign up (screen 1): Google, email + password with strength hint, Turnstile, privacy note.
 * allauth errors go to the field named by their `param`; unknown ones become a server-error alert.
 *
 * @returns The page.
 */
export function SignupPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [turnstileToken, setTurnstileToken] = useState("");
  // Turnstile tokens are single-use and the backend spends one even when validation fails, so every
  // failed submit remounts the widget (new key) for a fresh challenge.
  const [turnstileRound, setTurnstileRound] = useState(0);
  const [turnstileError, setTurnstileError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const mutation = useAuthMutation(signup);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<SignupValues>({ resolver: zodResolver(signupSchema) });
  const hasFieldErrors = Object.keys(errors).length > 0 || turnstileError !== null;

  const onSubmit = handleSubmit((values) => {
    setServerError(null);
    setTurnstileError(null);
    mutation.mutate(
      { ...values, turnstile_token: turnstileToken },
      {
        onSuccess: (viewer) =>
          void navigate(viewer.state === "pending_verification" ? CHECK_EMAIL_PATH : HOME_PATH, {
            state: { email: values.email },
          }),
        onError: (error) => {
          setTurnstileToken("");
          setTurnstileRound((round) => round + 1);
          const info = authErrorInfo(error);
          if (info.field === "email" || info.field === "password")
            setError(info.field, { message: info.key });
          else if (info.field === "turnstile_token") setTurnstileError(info.key);
          else setServerError(info.key);
        },
      },
    );
  });

  return (
    <>
      <div className="auth__intro">
        <h1>{t("signup.title")}</h1>
        <p className="t-muted">{t("signup.lead")}</p>
      </div>
      <FormSummary show={hasFieldErrors} />
      {serverError && <Alert tone="danger">{t(serverError)}</Alert>}
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
          autoComplete="new-password"
          showStrength
          hint={t("auth.password_hint")}
          disabled={mutation.isPending}
          error={errors.password?.message && t(errors.password.message)}
          {...register("password")}
        />
        <div
          className={TURNSTILE_SITE_KEY ? "turnstile turnstile--live" : "turnstile"}
          role="group"
          aria-label="Cloudflare Turnstile"
          aria-describedby={turnstileError ? TURNSTILE_ERROR_ID : undefined}
        >
          {TURNSTILE_SITE_KEY ? (
            <TurnstileWidget
              key={turnstileRound}
              siteKey={TURNSTILE_SITE_KEY}
              language={i18n.language}
              onToken={setTurnstileToken}
            />
          ) : (
            // Placeholder slot (mocks, tests): the dashed box from the design.
            <CircleCheck className="icon" aria-hidden="true" />
          )}
        </div>
        <p className="field__hint">{t("auth.turnstile_note")}</p>
        {turnstileError && <FieldError id={TURNSTILE_ERROR_ID}>{t(turnstileError)}</FieldError>}
        <div className="form__actions">
          <Button
            type="submit"
            variant="primary"
            block
            busy={mutation.isPending}
            busyLabel={t("signup.submitting")}
            disabled={TURNSTILE_SITE_KEY !== "" && turnstileToken === ""}
          >
            {t("signup.submit")}
          </Button>
        </div>
      </form>
      <PrivacyNote />
      <p>
        {t("signup.have_account")} <Link to="/login">{t("signup.login_link")}</Link>
      </p>
    </>
  );
}
