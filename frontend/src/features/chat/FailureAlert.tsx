import { RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import type { FailureMessage } from "./failureMessage";

/** Props of {@link FailureAlert}. */
interface FailureAlertProps {
  message: FailureMessage;
  /** Resend the same question; shown only when the message allows it. */
  onRetry?: (() => void) | undefined;
}

/**
 * Inline alert in place of the answer (screen 12) with Retry when it makes sense.
 *
 * @param props Message and retry callback.
 * @returns The alert.
 */
export function FailureAlert({ message, onRetry }: FailureAlertProps) {
  const { t } = useTranslation();
  return (
    <Alert
      tone={message.tone}
      role="alert"
      title={t(message.titleKey)}
      actions={
        message.retry &&
        onRetry && (
          <Button small icon={<RefreshCw className="icon" aria-hidden="true" />} onClick={onRetry}>
            {t("common.retry")}
          </Button>
        )
      }
    >
      {t(message.key, message.values)}
    </Alert>
  );
}
