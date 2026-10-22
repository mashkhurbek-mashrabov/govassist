import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router";
import { login } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { safeNext } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextField } from "../../components/ui/TextField";
import { AuthErrorAlert } from "./AuthErrorAlert";
import { GoogleLoginButton } from "./GoogleLoginButton";
import { loginSchema, type LoginValues } from "./schemas";

/**
 * Email + password login. Returns to `?next=` (same-origin only) on success.
 *
 * @returns The page.
 */
export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const mutation = useAuthMutation(login);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit((values) =>
    mutation.mutate(values, { onSuccess: () => void navigate(safeNext(params.get("next"))) }),
  );

  return (
    <>
      <h1>{t("auth.login.title")}</h1>
      {params.get("error") === "social" && <Alert tone="error">{t("auth.errors.social")}</Alert>}
      <GoogleLoginButton />
      <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
        <TextField
          label={t("auth.fields.email")}
          type="email"
          autoComplete="email"
          error={errors.email?.message && t(errors.email.message)}
          {...register("email")}
        />
        <PasswordField
          label={t("auth.fields.password")}
          autoComplete="current-password"
          error={errors.password?.message && t(errors.password.message)}
          {...register("password")}
        />
        <AuthErrorAlert error={mutation.error} />
        <button type="submit" className="min-h-11 border" disabled={mutation.isPending}>
          {t("auth.login.submit")}
        </button>
      </form>
      <Link to="/forgot-password">{t("auth.login.forgot")}</Link>
      <p>
        {t("auth.login.noAccount")} <Link to="/signup">{t("auth.login.signupLink")}</Link>
      </p>
    </>
  );
}
