import { useTranslation } from "react-i18next";

/** Props of {@link UserBubble}. */
interface UserBubbleProps {
  text: string;
}

/**
 * The user's question (stored text is already PII-scrubbed).
 *
 * @param props Question text.
 * @returns The bubble.
 */
export function UserBubble({ text }: UserBubbleProps) {
  const { t } = useTranslation();
  return (
    <div className="self-end border p-2 whitespace-pre-wrap">
      <span className="sr-only">{t("chat.you")}: </span>
      {text}
    </div>
  );
}
