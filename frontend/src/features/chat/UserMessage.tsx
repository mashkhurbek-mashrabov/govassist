import { useTranslation } from "react-i18next";

/** Props of {@link UserMessage}. */
interface UserMessageProps {
  text: string;
}

/**
 * The user's question as a bubble (stored text is PII-scrubbed, so `[PASSPORT]` shows as plain text).
 *
 * @param props Question text.
 * @returns The thread item.
 */
export function UserMessage({ text }: UserMessageProps) {
  const { t } = useTranslation();
  return (
    <li className="msg-user">
      <p className="sr-only">{t("chat.you")}:</p>
      <p>{text}</p>
    </li>
  );
}
