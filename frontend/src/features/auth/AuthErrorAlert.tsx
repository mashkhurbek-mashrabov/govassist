import { useTranslation } from "react-i18next";
import { Alert } from "../../components/ui/Alert";
import { authErrorKey } from "./authErrors";

/** Props of {@link AuthErrorAlert}. */
interface AuthErrorAlertProps {
  error: unknown;
}

/**
 * Translated alert for a failed auth call; renders nothing without an error.
 *
 * @param props The error.
 * @returns The alert or nothing.
 */
export function AuthErrorAlert({ error }: AuthErrorAlertProps) {
  const { t } = useTranslation();
  if (!error) return null;
  return <Alert tone="error">{t(authErrorKey(error))}</Alert>;
}
