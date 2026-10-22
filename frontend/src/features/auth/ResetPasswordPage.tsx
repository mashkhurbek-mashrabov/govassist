import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import { AuthError, resetPassword } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { HOME_PATH, LOGIN_PATH } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { LinkButton } from "../../components/ui/LinkButton";
import { PasswordField } from "../../components/ui/PasswordField";
import { authErrorInfo } from "./authErrors";
import { resetSchema, type ResetValues } from "./schemas";

/** allauth code for a bad or expired key. */
const INVALID_KEY = "invalid";

/**
 * Reset password (screen 5): new password with strength hint; invalid key and success states.
 *
 * @returns The page.
 */
export function ResetPasswordPage() {
  const { t } = useTranslation();
  const { key = "" } = useParams();
  const navigate = useNavigate();
  const mutation = useAuthMutation(resetPassword);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ResetValues>({ resolver: zodResolver(resetSchema) });
  const invalidKey = mutation.error instanceof AuthError && mutation.error.codes.includes(INVALID_KEY);
  const serverError = mutation.isError && !invalidKey && authErrorInfo(mutation.error).field === null;

  const onSubmit = handleSubmit(({ password }) =>
    mutation.mutate(
      { key, password },
      {
        onSuccess: (viewer) => {
          if (viewer.state === "authenticated") void navigate(HOME_PATH);
        },
        onError: (error) => {
          const info = authErrorInfo(error);
          if (info.field === "password") setError("password", { message: info.key });
        },
      },
    ),
  );

  if (mutation.isSuccess) {
    return (
      <>
        <div className="auth__intro">
          <h1>{t("reset.title")}</h1>
        </div>
        <Alert tone="success">{t("reset.success")}</Alert>
        <LinkButton variant="primary" block to={LOGIN_PATH}>
          {t("login.submit")}
        </LinkButton>
      </>
    );
  }

  return (
    <>
      <div className="auth__intro">
        <h1>{t("reset.title")}</h1>
      </div>
      {invalidKey && (
        <Alert tone="danger">
          <p>{t("reset.invalid")}</p>
          <Link to="/forgot-password">{t("forgot.submit")}</Link>
        </Alert>
      )}
      {serverError && <Alert tone="danger">{t("error.server")}</Alert>}
      <form className="form" noValidate onSubmit={(event) => void onSubmit(event)}>
        <PasswordField
          label={t("reset.new_password")}
          autoComplete="new-password"
          showStrength
          hint={t("auth.password_hint")}
          error={errors.password?.message && t(errors.password.message)}
          {...register("password")}
        />
        <div className="form__actions">
          <Button
            type="submit"
            variant="primary"
            block
            busy={mutation.isPending}
            busyLabel={t("common.saving")}
          >
            {t("reset.submit")}
          </Button>
        </div>
      </form>
    </>
  );
}
