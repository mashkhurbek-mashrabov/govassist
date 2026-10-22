import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { requestPasswordReset } from "../../api/auth";
import { Mail } from "lucide-react";
import { Alert } from "../../components/ui/Alert";
import { authErrorInfo } from "./authErrors";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { emailSchema, type EmailValues } from "./schemas";

/**
 * Forgot password (screen 5): the same "sent" message whether or not the account exists.
 *
 * @returns The page.
 */
export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const mutation = useMutation({ mutationFn: requestPasswordReset });
  // An unknown email answers 200 like a known one (contract v1.9); failures are rate limits or server errors.
  const failure = mutation.isError ? authErrorInfo(mutation.error) : null;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmailValues>({ resolver: zodResolver(emailSchema) });

  const onSubmit = handleSubmit(({ email }) => mutation.mutate(email));

  return (
    <>
      <div className="auth__intro">
        <h1>{t("forgot.title")}</h1>
        {!mutation.isSuccess && <p className="t-muted">{t("forgot.lead")}</p>}
      </div>
      {mutation.isSuccess ? (
        <Alert tone="success" icon={Mail}>
          {t("forgot.sent")}
        </Alert>
      ) : (
        <form className="form" noValidate onSubmit={(event) => void onSubmit(event)}>
          {failure && <Alert tone={failure.warning ? "warning" : "danger"}>{t(failure.key)}</Alert>}
          <TextField
            label={t("auth.email")}
            type="email"
            autoComplete="email"
            placeholder={t("auth.email_placeholder")}
            error={errors.email?.message && t(errors.email.message)}
            {...register("email")}
          />
          <div className="form__actions">
            <Button type="submit" variant="primary" block busy={mutation.isPending}>
              {t("forgot.submit")}
            </Button>
          </div>
        </form>
      )}
      <Link to="/login">{t("forgot.back_to_login")}</Link>
    </>
  );
}
