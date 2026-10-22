import { useTranslation } from "react-i18next";
import { useSources } from "../../api/queries";
import type { Lang } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { formatDate } from "../../lib/format";

/**
 * What GovAssist is, the reviewed sources behind the answers (`GET /sources`), and the disclaimer. Public.
 *
 * @returns The page.
 */
export function AboutPage() {
  const { t, i18n } = useTranslation();
  const sources = useSources();
  return (
    <>
      <h1 className="font-bold">{t("about.title")}</h1>
      <p>{t("about.body")}</p>
      <section className="flex flex-col gap-2">
        <h2 className="font-bold">{t("about.sourcesTitle")}</h2>
        <p>{t("about.sources")}</p>
        {sources.isError && <Alert tone="error">{t("common.error")}</Alert>}
        <ul className="list-disc pl-6">
          {sources.data?.map((source) => (
            <li key={source.url}>
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                {source.name}
              </a>
              {" · "}
              {source.publisher}
              {" · "}
              {source.last_fetched_at === null
                ? t("about.sourceCount", { count: source.documents })
                : t("about.sourceMeta", {
                    count: source.documents,
                    date: formatDate(source.last_fetched_at, i18n.language as Lang),
                  })}
            </li>
          ))}
        </ul>
      </section>
      <p>{t("answer.disclaimer")}</p>
    </>
  );
}
