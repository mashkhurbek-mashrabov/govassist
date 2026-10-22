import { useTranslation } from "react-i18next";
import { Alert } from "../../components/ui/Alert";
import type { FailureMessage } from "./failureMessage";

/** Props of {@link FailureAlert}. */
interface FailureAlertProps {
  message: FailureMessage;
  /** A stop is the user's choice, so it is announced politely. */
  tone: "error" | "info";
  /** Resend the same question; omit to hide Retry (older answers). */
  onRetry?: (() => void) | undefined;
}

/**
 * Inline message for a failed or stopped answer, with Retry.
 *
 * @param props Message, tone and retry callback.
 * @returns The alert.
 */
export function FailureAlert({ message, tone, onRetry }: FailureAlertProps) {
  const { t } = useTranslation();
  return (
    <Alert tone={tone}>
      <p>{t(message.key, message.values)}</p>
      {onRetry && (
        <button type="button" className="min-h-11 border px-3" onClick={onRetry}>
          {t("common.retry")}
        </button>
      )}
    </Alert>
  );
}
