import { BookOpen, Info } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSources } from "../../api/queries";
import { Alert } from "../../components/ui/Alert";
import { ExternalLink } from "../../components/ui/ExternalLink";
import { formatDate } from "../../lib/format";
import { Disclaimer } from "../answer/Disclaimer";

/** The four "How answers are made" and "Privacy" points. */
const POINTS = [1, 2, 3, 4] as const;

/**
 * About (screen 15): not-official note, what it is, how answers are made, privacy, and the source list
 * from `GET /sources`. Public.
 *
 * @returns The page.
 */
export function AboutPage() {
  const { t } = useTranslation();
  const sources = useSources();
  return (
    <main className="page" id="main">
      <h1>{t("about.title")}</h1>
      <Alert tone="warning" icon={Info} title={t("about.not_official_title")} role="note">
        {t("app.not_official_long")}
      </Alert>
      <section className="prose" aria-labelledby="about-what">
        <h2 id="about-what">{t("about.what_title")}</h2>
        <p>{t("about.what")}</p>
      </section>
      <section className="prose" aria-labelledby="about-how">
        <h2 id="about-how">{t("about.how_title")}</h2>
        <ul>
          {POINTS.map((n) => (
            <li key={n}>{t(`about.how_${n}`)}</li>
          ))}
        </ul>
        <Disclaimer />
      </section>
      <section className="prose" aria-labelledby="about-privacy" id="privacy">
        <h2 id="about-privacy">{t("about.privacy_title")}</h2>
        <ul>
          {POINTS.map((n) => (
            <li key={n}>{t(`about.privacy_${n}`)}</li>
          ))}
        </ul>
      </section>
      <section className="section" aria-labelledby="about-sources">
        <h2 id="about-sources">{t("about.sources_title")}</h2>
        <p>{t("about.sources_lead")}</p>
        {sources.isError && <Alert tone="danger">{t("error.server")}</Alert>}
        <ol className="sources">
          {sources.data?.map((source) => {
            const meta = [
              source.publisher,
              t(`answer.source_kind_${source.kind}`),
              t("about.source_docs", { n: source.documents }),
              source.last_fetched_at &&
                t("about.source_updated", { date: formatDate(source.last_fetched_at) }),
            ].filter(Boolean);
            return (
              <li key={source.url} className="source">
                <span className="source__num" aria-hidden="true">
                  <BookOpen className="icon" />
                </span>
                <div>
                  <p className="source__title">
                    <ExternalLink href={source.url}>{source.name}</ExternalLink>
                  </p>
                  <p className="source__meta">{meta.join(" · ")}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </section>
    </main>
  );
}
