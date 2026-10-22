import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { requestPasswordReset } from "../../api/auth";
import { Alert } from "../../components/ui/Alert";
import { TextField } from "../../components/ui/TextField";
import { AuthErrorAlert } from "./AuthErrorAlert";
import { forgotSchema, type ForgotValues } from "./schemas";

/**
 * Request a password-reset email. Always reports success, so it does not reveal which emails exist.
 *
 * @returns The page.
 */
export function ForgotPasswordPage() {
  const { t } = useTranslation();
  const mutation = useMutation({ mutationFn: requestPasswordReset });
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotValues>({ resolver: zodResolver(forgotSchema) });

  const onSubmit = handleSubmit(({ email }) => mutation.mutate(email));

  return (
    <>
      <h1>{t("auth.forgot.title")}</h1>
      {mutation.isSuccess ? (
        <Alert>{t("auth.forgot.sent")}</Alert>
      ) : (
        <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
          <p>{t("auth.forgot.body")}</p>
          <TextField
            label={t("auth.fields.email")}
            type="email"
            autoComplete="email"
            error={errors.email?.message && t(errors.email.message)}
            {...register("email")}
          />
          <AuthErrorAlert error={mutation.error} />
          <button type="submit" className="min-h-11 border" disabled={mutation.isPending}>
            {t("auth.forgot.submit")}
          </button>
        </form>
      )}
      <Link to="/login">{t("auth.backToLogin")}</Link>
    </>
  );
}
