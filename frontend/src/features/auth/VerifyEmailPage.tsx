import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { CircleAlert, CircleCheck } from "lucide-react";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router";
import { verifyEmail } from "../../api/auth";
import { resendVerification } from "../../api/endpoints";
import { useAuthMutation } from "../../api/queries";
import { CHECK_EMAIL_PATH, HOME_PATH, LOGIN_PATH } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { CenterState } from "../../components/ui/CenterState";
import { LinkButton } from "../../components/ui/LinkButton";
import { Spinner } from "../../components/ui/Spinner";
import { TextField } from "../../components/ui/TextField";
import { resendFailure } from "./resendFailure";
import { emailSchema, type EmailValues } from "./schemas";

/**
 * Verify email (screen 4): confirms the key on load (decoded by the router, contract v1.3), then
 * success → onboarding, or invalid → ask for a new link.
 *
 * @returns The page.
 */
export function VerifyEmailPage() {
  const { t } = useTranslation();
  const { key = "" } = useParams();
  const navigate = useNavigate();
  const verify = useAuthMutation(verifyEmail);
  const started = useRef(false);

  useEffect(() => {
    // StrictMode runs effects twice in development; the key must be posted once.
    if (started.current) return;
    started.current = true;
    verify.mutate(key);
  }, [key, verify]);

  if (verify.isSuccess) {
    return (
      <>
        <CenterState
          icon={<CircleCheck className="icon" aria-hidden="true" />}
          tone="success"
          title={t("verify.success_title")}
          role="status"
        >
          <p className="t-body-lg">{t("verify.success_lead")}</p>
        </CenterState>
        <Button
          variant="primary"
          block
          onClick={() => void navigate(verify.data.state === "authenticated" ? HOME_PATH : LOGIN_PATH)}
        >
          {t("common.continue")}
        </Button>
      </>
    );
  }
  if (verify.isError)
    return (
      <InvalidLink
        onResent={(email) => void navigate(CHECK_EMAIL_PATH, { state: { email, resent: true } })}
      />
    );
  return <CenterState icon={<Spinner />} title={t("verify.verifying")} role="status" />;
}

/** Props of {@link InvalidLink}. */
interface InvalidLinkProps {
  onResent: (email: string) => void;
}

/**
 * Invalid or expired link: email field + "Send a new link", and a way to log in.
 *
 * @param props Callback after a successful resend.
 * @returns The state.
 */
function InvalidLink({ onResent }: InvalidLinkProps) {
  const { t } = useTranslation();
  const resend = useMutation({ mutationFn: resendVerification });
  const failure = resend.isError ? resendFailure(resend.error) : null;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmailValues>({ resolver: zodResolver(emailSchema) });

  const onSubmit = handleSubmit(({ email }) => resend.mutate(email, { onSuccess: () => onResent(email) }));

  return (
    <>
      <CenterState
        icon={<CircleAlert className="icon" aria-hidden="true" />}
        tone="danger"
        title={t("verify.invalid_title")}
        role="alert"
      >
        <p className="t-body-lg">{t("verify.invalid_lead")}</p>
      </CenterState>
      {failure && (
        <Alert tone={failure.rateLimited ? "warning" : "danger"}>{t(failure.key, failure.values)}</Alert>
      )}
      <form className="form" noValidate onSubmit={(event) => void onSubmit(event)}>
        <TextField
          label={t("auth.email")}
          type="email"
          autoComplete="email"
          placeholder={t("auth.email_placeholder")}
          error={errors.email?.message && t(errors.email.message)}
          {...register("email")}
        />
        <div className="form__actions">
          <Button type="submit" variant="primary" block busy={resend.isPending}>
            {t("verify.request_new")}
          </Button>
          <LinkButton variant="ghost" block to={LOGIN_PATH}>
            {t("login.submit")}
          </LinkButton>
        </div>
      </form>
    </>
  );
}
