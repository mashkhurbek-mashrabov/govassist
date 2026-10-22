import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { changePassword } from "../../api/auth";
import { Alert } from "../../components/ui/Alert";
import { PasswordField } from "../../components/ui/PasswordField";
import { AuthErrorAlert } from "../auth/AuthErrorAlert";
import { changePasswordSchema, MIN_PASSWORD_LENGTH, type ChangePasswordValues } from "../auth/schemas";

/**
 * Change the password (allauth). Clears the form on success.
 *
 * @returns The form.
 */
export function ChangePasswordForm() {
  const { t } = useTranslation();
  const mutation = useMutation({ mutationFn: changePassword });
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordValues>({ resolver: zodResolver(changePasswordSchema) });

  const onSubmit = handleSubmit(({ current, password }) =>
    mutation.mutate({ current_password: current, new_password: password }, { onSuccess: () => reset() }),
  );

  return (
    <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
      <PasswordField
        label={t("auth.fields.currentPassword")}
        autoComplete="current-password"
        error={errors.current?.message && t(errors.current.message)}
        {...register("current")}
      />
      <PasswordField
        label={t("auth.fields.newPassword")}
        autoComplete="new-password"
        hint={t("auth.fields.passwordHint", { count: MIN_PASSWORD_LENGTH })}
        error={errors.password?.message && t(errors.password.message, { count: MIN_PASSWORD_LENGTH })}
        {...register("password")}
      />
      <AuthErrorAlert error={mutation.error} />
      {mutation.isSuccess && <Alert>{t("settings.password.saved")}</Alert>}
      <button type="submit" className="min-h-11 border" disabled={mutation.isPending}>
        {t("settings.password.submit")}
      </button>
    </form>
  );
}
