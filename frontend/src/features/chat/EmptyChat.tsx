import { FileText, ListChecks, MapPin, Scale } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSuggestions } from "../../api/queries";
import { Skeleton } from "../../components/ui/Skeleton";
import { Chips } from "../answer/Chips";

/** "What I can help with" rows: copy key and icon. */
const HELP = [
  { key: "chat.help_1", Icon: ListChecks },
  { key: "chat.help_2", Icon: FileText },
  { key: "chat.help_3", Icon: MapPin },
  { key: "chat.help_4", Icon: Scale },
] as const;
/** Skeleton chips while suggestions load. */
const SKELETON_CHIPS = 4;

/** Props of {@link EmptyChat}. */
interface EmptyChatProps {
  onAsk: (question: string) => void;
}

/**
 * New chat (screen 7): greeting, suggestion chips (skeletons while loading) and what the assistant can do.
 *
 * @param props Ask callback.
 * @returns The empty state.
 */
export function EmptyChat({ onAsk }: EmptyChatProps) {
  const { t } = useTranslation();
  const suggestions = useSuggestions();
  return (
    <>
      <section className="greeting" aria-labelledby="chat-greeting">
        <h1 className="t-display" id="chat-greeting">
          {t("chat.greeting")}
        </h1>
        <p className="t-body-lg t-muted">{t("chat.greeting_lead")}</p>
      </section>
      <section className="section" aria-labelledby="chat-suggestions">
        <h2 className="t-h3" id="chat-suggestions">
          {t("chat.suggestions")}
        </h2>
        {suggestions.isPending ? (
          <div role="status">
            <p className="sr-only">{t("common.loading")}</p>
            <ul className="chips" aria-hidden="true">
              {Array.from({ length: SKELETON_CHIPS }, (_, chip) => (
                <li key={chip}>
                  <span className="chip chip--skeleton">
                    <Skeleton />
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <Chips questions={suggestions.data?.map((item) => item.text) ?? []} onAsk={onAsk} />
        )}
      </section>
      <section className="card" aria-labelledby="chat-can-help">
        <h2 className="t-h3" id="chat-can-help">
          {t("chat.can_help")}
        </h2>
        <ul className="help-list">
          {HELP.map(({ key, Icon }) => (
            <li key={key}>
              <Icon className="icon" aria-hidden="true" />
              <span>{t(key)}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
