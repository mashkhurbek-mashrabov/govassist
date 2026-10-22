import { Building2, MapPin, Phone } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import type { OfficeMatch } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { ExternalLink } from "../../components/ui/ExternalLink";
import { formatDate } from "../../lib/format";
import { OfficeHours } from "./OfficeHours";
import { OpenBadge } from "./OpenBadge";

/** Props of {@link OfficeCard}. */
interface OfficeCardProps {
  match: OfficeMatch;
  /** Injected for tests; defaults to the current time. */
  now?: Date;
}

/**
 * Where to go (components.md → OfficeCard): directory data only, never model output. Type label and place
 * names come localized; the office name and address are shown as stored (contract v1.5).
 *
 * @param props Office match and the current moment.
 * @returns The card.
 */
export function OfficeCard({ match, now = new Date() }: OfficeCardProps) {
  const { t } = useTranslation();
  const headingId = useId();
  const { office } = match;
  const typeLabel = (
    <span className="office__type-label">
      <Building2 className="icon" aria-hidden="true" />
      {match.office_type.label}
    </span>
  );
  return (
    <section className="card office" aria-labelledby={headingId}>
      <h3 className="card__head" id={headingId}>
        <MapPin className="icon" aria-hidden="true" />
        {t("answer.where_to_go")}
      </h3>
      {match.match === "none" || !office ? (
        <>
          <div className="office__type">{typeLabel}</div>
          <Alert>
            <p>{t("office.match_none")}</p>
            <p>{t("office.match_none_type", { office_type: match.office_type.label })}</p>
          </Alert>
        </>
      ) : (
        <>
          {match.match === "region" && <Alert tone="warning">{t("office.match_region")}</Alert>}
          <div className="office__type">
            {typeLabel}
            <OpenBadge hours={office.working_hours} now={now} />
          </div>
          <p className="t-h3 t-strong">{office.name}</p>
          <p className="office__row">
            <MapPin className="icon" aria-hidden="true" />
            <span>
              {office.address}, {office.district.name}, {office.region.name}
            </span>
          </p>
          {office.working_hours.length > 0 && <OfficeHours hours={office.working_hours} now={now} />}
          <div className="office__actions">
            {office.phone ? (
              <a className="btn btn--secondary" href={`tel:${office.phone.replaceAll(" ", "")}`}>
                <Phone className="icon" aria-hidden="true" />
                <span>
                  <span className="sr-only">{t("office.call")}: </span>
                  <span className="nowrap">{office.phone}</span>
                </span>
              </a>
            ) : (
              <p className="office__row">
                <Phone className="icon" aria-hidden="true" />
                <span>{t("office.phone_unknown")}</span>
              </p>
            )}
            <ExternalLink href={office.map_url} className="btn btn--primary">
              <MapPin className="icon" aria-hidden="true" />
              <span>{t("office.map")}</span>
            </ExternalLink>
          </div>
          <p className="office__meta">
            <span>{t("office.data_as_of", { date: formatDate(office.data_as_of) })}</span>
            <ExternalLink href={office.source_url} className="">
              {t("office.source")}
            </ExternalLink>
          </p>
        </>
      )}
    </section>
  );
}
