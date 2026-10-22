import { useTranslation } from "react-i18next";
import type { Lang, OfficeMatch } from "../../api/types";
import { formatDate } from "../../lib/format";
import { OfficeHours } from "./OfficeHours";

/** Props of {@link OfficeCard}. */
interface OfficeCardProps {
  match: OfficeMatch;
  /** Injected for tests; defaults to the current time. */
  now?: Date;
}

/**
 * The office to visit, from the directory (never model output). Handles district, region and "none" matches.
 *
 * @param props Office match and the current moment.
 * @returns The card.
 */
export function OfficeCard({ match, now = new Date() }: OfficeCardProps) {
  const { t, i18n } = useTranslation();
  const { office } = match;
  if (match.match === "none" || !office) {
    return (
      <section aria-label={t("office.title")} className="border p-3">
        <p>{t("office.matchNone", { type: match.office_type.label })}</p>
      </section>
    );
  }
  return (
    <section aria-label={t("office.title")} className="flex flex-col gap-2 border p-3">
      <h3 className="font-bold">{office.name}</h3>
      <p>{office.office_type.label}</p>
      {match.match === "region" && <p>{t("office.matchRegion", { region: office.region.name })}</p>}
      <p>
        {office.address}, {office.district.name}, {office.region.name}
      </p>
      {office.phone && (
        <p>
          {t("office.phone")}: <a href={`tel:${office.phone.replaceAll(" ", "")}`}>{office.phone}</a>
        </p>
      )}
      <OfficeHours hours={office.working_hours} now={now} />
      <a href={office.map_url} target="_blank" rel="noopener noreferrer" className="min-h-11 border p-2">
        {t("office.map")}
      </a>
      <p className="text-sm">
        {t("office.dataAsOf", { date: formatDate(office.data_as_of, i18n.language as Lang) })}{" "}
        <a href={office.source_url} target="_blank" rel="noopener noreferrer">
          {t("office.source")}
        </a>
      </p>
    </section>
  );
}
