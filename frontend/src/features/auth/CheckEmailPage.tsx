import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Mail, RefreshCw } from "lucide-react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router";
import { resendVerification } from "../../api/endpoints";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { CenterState } from "../../components/ui/CenterState";
import { Interpolate, SLOT } from "../../components/ui/Interpolate";
import { LinkButton } from "../../components/ui/LinkButton";
import { TextField } from "../../components/ui/TextField";
import { resendFailure } from "./resendFailure";
import { emailSchema, type EmailValues } from "./schemas";

/** Navigation state from signup/login (and from verify after a resend). */
export interface CheckEmailState {
  email?: string;
  resent?: boolean;
}

/**
 * Check your email (screen 3): resend (`POST /auth/resend-verification`, always 204, 429 → wait), or use
 * another email (back to signup). Without the address in the navigation state, an email field is shown.
 *
 * @returns The page.
 */
export function CheckEmailPage() {
  const { t } = useTranslation();
  const state = useLocation().state as CheckEmailState | null;
  const knownEmail = state?.email;
  const resend = useMutation({ mutationFn: resendVerification });
  const failure = resend.isError ? resendFailure(resend.error) : null;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmailValues>({
    resolver: zodResolver(emailSchema),
    defaultValues: { email: knownEmail ?? "" },
  });

  const onSubmit = handleSubmit(({ email }) => resend.mutate(email));

  return (
    <>
      <CenterState icon={<Mail className="icon" aria-hidden="true" />} title={t("check_email.title")}>
        <p className="t-body-lg">
          {knownEmail ? (
            <Interpolate text={t("check_email.lead", { email: SLOT })}>
              <strong>{knownEmail}</strong>
            </Interpolate>
          ) : (
            t("check_email.lead_no_email")
          )}
        </p>
        <p className="t-muted">{t("check_email.spam")}</p>
      </CenterState>
      {(resend.isSuccess || (state?.resent === true && resend.isIdle)) && (
        <Alert tone="success">{t("check_email.resent")}</Alert>
      )}
      {failure && (
        <Alert tone={failure.rateLimited ? "warning" : "danger"}>{t(failure.key, failure.values)}</Alert>
      )}
      <form className="form" noValidate onSubmit={(event) => void onSubmit(event)}>
        {!knownEmail && (
          <TextField
            label={t("auth.email")}
            type="email"
            autoComplete="email"
            placeholder={t("auth.email_placeholder")}
            error={errors.email?.message && t(errors.email.message)}
            {...register("email")}
          />
        )}
        <div className="form__actions">
          <Button
            type="submit"
            block
            icon={<RefreshCw className="icon" aria-hidden="true" />}
            busy={resend.isPending}
            disabled={failure?.rateLimited === true}
          >
            {t("check_email.resend")}
          </Button>
          <LinkButton variant="ghost" block to="/signup">
            {t("check_email.change")}
          </LinkButton>
        </div>
      </form>
    </>
  );
}
