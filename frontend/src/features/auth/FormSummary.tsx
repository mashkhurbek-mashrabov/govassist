import { useTranslation } from "react-i18next";
import { Alert } from "../../components/ui/Alert";

/** Props of {@link FormSummary}. */
interface FormSummaryProps {
  show: boolean;
}

/**
 * Error summary at the top of a form ("There are problems in the form…").
 *
 * @param props Whether the form has field errors.
 * @returns The alert, or nothing.
 */
export function FormSummary({ show }: FormSummaryProps) {
  const { t } = useTranslation();
  return show ? <Alert tone="danger" title={t("error.form_summary")} /> : null;
}
