import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { changePassword } from "../../api/auth";
import { refreshViewer } from "../../api/queries";
import { Alert } from "../../components/ui/Alert";
import { PasswordField } from "../../components/ui/PasswordField";
import { AuthErrorAlert } from "../auth/AuthErrorAlert";
import { changePasswordSchema, MIN_PASSWORD_LENGTH, type ChangePasswordValues } from "../auth/schemas";

/** Props of {@link ChangePasswordForm}. */
interface ChangePasswordFormProps {
  /** `Me.has_password`; false for Google-only accounts setting a first password. */
  hasPassword: boolean;
}

/**
 * Change the password, or set a first one for a Google-only account (allauth). Clears the form and
 * re-reads `Me` (for `has_password`) on success.
 *
 * @param props Whether the account already has a password.
 * @returns The form.
 */
export function ChangePasswordForm({ hasPassword }: ChangePasswordFormProps) {
  const { t } = useTranslation();
  const client = useQueryClient();
  const mutation = useMutation({ mutationFn: changePassword, onSuccess: () => refreshViewer(client) });
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordValues>({ resolver: zodResolver(changePasswordSchema(hasPassword)) });

  const onSubmit = handleSubmit(({ current, password }) =>
    mutation.mutate(
      hasPassword ? { current_password: current, new_password: password } : { new_password: password },
      { onSuccess: () => reset() },
    ),
  );

  return (
    <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
      {hasPassword && (
        <PasswordField
          label={t("auth.fields.currentPassword")}
          autoComplete="current-password"
          error={errors.current?.message && t(errors.current.message)}
          {...register("current")}
        />
      )}
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
        {t(hasPassword ? "settings.password.submit" : "settings.password.set")}
      </button>
    </form>
  );
}
