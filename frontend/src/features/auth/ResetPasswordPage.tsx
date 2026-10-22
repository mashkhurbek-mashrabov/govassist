import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import { resetPassword } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { HOME_PATH } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { PasswordField } from "../../components/ui/PasswordField";
import { AuthErrorAlert } from "./AuthErrorAlert";
import { MIN_PASSWORD_LENGTH, newPasswordSchema, type NewPasswordValues } from "./schemas";

/**
 * Set a new password with the key from the reset email.
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
    formState: { errors },
  } = useForm<NewPasswordValues>({ resolver: zodResolver(newPasswordSchema) });

  const onSubmit = handleSubmit(({ password }) =>
    mutation.mutate(
      { key, password },
      {
        onSuccess: (viewer) => {
          if (viewer.state === "authenticated") void navigate(HOME_PATH);
        },
      },
    ),
  );

  if (mutation.data && mutation.data.state !== "authenticated") {
    return (
      <>
        <h1>{t("auth.reset.title")}</h1>
        <Alert>{t("auth.reset.success")}</Alert>
        <Link to="/login">{t("auth.backToLogin")}</Link>
      </>
    );
  }

  return (
    <>
      <h1>{t("auth.reset.title")}</h1>
      <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
        <PasswordField
          label={t("auth.fields.newPassword")}
          autoComplete="new-password"
          hint={t("auth.fields.passwordHint", { count: MIN_PASSWORD_LENGTH })}
          error={errors.password?.message && t(errors.password.message, { count: MIN_PASSWORD_LENGTH })}
          {...register("password")}
        />
        <PasswordField
          label={t("auth.fields.confirmPassword")}
          autoComplete="new-password"
          error={errors.confirm?.message && t(errors.confirm.message)}
          {...register("confirm")}
        />
        <AuthErrorAlert error={mutation.error} />
        <button type="submit" className="min-h-11 border" disabled={mutation.isPending}>
          {t("auth.reset.submit")}
        </button>
      </form>
    </>
  );
}
