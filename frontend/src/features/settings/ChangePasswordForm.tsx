import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { changePassword } from "../../api/auth";
import { refreshViewer } from "../../api/queries";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { PasswordField } from "../../components/ui/PasswordField";
import { authErrorInfo } from "../auth/authErrors";
import { changePasswordSchema, type ChangePasswordValues } from "../auth/schemas";

/** Props of {@link ChangePasswordForm}. */
interface ChangePasswordFormProps {
  /** `Me.has_password`; false for Google-only accounts setting a first password. */
  hasPassword: boolean;
  onCancel: () => void;
  onSaved: () => void;
}

/**
 * Inline change-password form in the Account card (components.md → ChangePasswordForm). A Google-only
 * account sets a first password without the current one; `Me` is re-read afterwards for `has_password`.
 *
 * @param props Password flag and callbacks.
 * @returns The form.
 */
export function ChangePasswordForm({ hasPassword, onCancel, onSaved }: ChangePasswordFormProps) {
  const { t } = useTranslation();
  const client = useQueryClient();
  const mutation = useMutation({ mutationFn: changePassword, onSuccess: () => refreshViewer(client) });
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ChangePasswordValues>({ resolver: zodResolver(changePasswordSchema(hasPassword)) });
  const serverError = mutation.isError && authErrorInfo(mutation.error).field === null;

  const onSubmit = handleSubmit(({ current, password }) =>
    mutation.mutate(
      hasPassword ? { current_password: current, new_password: password } : { new_password: password },
      {
        onSuccess: onSaved,
        onError: (error) => {
          const info = authErrorInfo(error);
          if (info.field === "current_password") setError("current", { message: info.key });
          if (info.field === "password") setError("password", { message: info.key });
        },
      },
    ),
  );

  return (
    <form
      className="card"
      aria-labelledby="password-form-title"
      noValidate
      onSubmit={(event) => void onSubmit(event)}
    >
      <h3 id="password-form-title">
        {t(hasPassword ? "settings.change_password" : "password_change.set_title")}
      </h3>
      {!hasPassword && <p className="t-muted">{t("password_change.set_lead")}</p>}
      {serverError && <Alert tone="danger">{t("error.server")}</Alert>}
      {hasPassword && (
        <PasswordField
          label={t("password_change.current")}
          autoComplete="current-password"
          error={errors.current?.message && t(errors.current.message)}
          {...register("current")}
        />
      )}
      <PasswordField
        label={t("reset.new_password")}
        autoComplete="new-password"
        showStrength
        hint={t("auth.password_hint")}
        error={errors.password?.message && t(errors.password.message)}
        {...register("password")}
      />
      <div className="row-actions">
        <Button type="submit" variant="primary" busy={mutation.isPending} busyLabel={t("common.saving")}>
          {t("reset.submit")}
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </form>
  );
}
