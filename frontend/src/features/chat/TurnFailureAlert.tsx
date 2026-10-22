import { useTranslation } from "react-i18next";
import { Alert } from "../../components/ui/Alert";
import { failureMessage } from "./failureMessage";
import type { TurnFailure } from "./useChatStream";

/** Props of {@link TurnFailureAlert}. */
interface TurnFailureAlertProps {
  failure: TurnFailure;
  onRetry: () => void;
}

/**
 * Inline error for a failed or stopped turn, with Retry (resends the same text).
 *
 * @param props Failure and retry callback.
 * @returns The alert.
 */
export function TurnFailureAlert({ failure, onRetry }: TurnFailureAlertProps) {
  const { t } = useTranslation();
  const { key, values } = failureMessage(failure);
  return (
    <Alert tone={failure.kind === "stopped" ? "info" : "error"}>
      <p>{t(key, values)}</p>
      <button type="button" className="min-h-11 border px-3" onClick={onRetry}>
        {t("common.retry")}
      </button>
    </Alert>
  );
}
