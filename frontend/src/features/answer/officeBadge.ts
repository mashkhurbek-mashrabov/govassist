import type { OpenStatus } from "../../lib/openNow";

/**
 * Badge modifier and text for an office status (components.md → OfficeCard badge table).
 *
 * @param status Result of `openStatus`.
 * @param t Translation function.
 * @returns Modifier and text.
 */
export function badgeFor(
  status: OpenStatus,
  t: (key: string, values?: Record<string, string>) => string,
): { tone: "open" | "break" | "closed" | "neutral"; text: string } {
  switch (status.state) {
    case "unknown":
      return { tone: "neutral", text: t("office.hours_unknown") };
    case "open":
      return {
        tone: "open",
        text: `${t("office.open_now")} · ${t("office.closes_at", { time: status.closesAt })}`,
      };
    case "break":
      return {
        tone: "break",
        text: `${t("office.break")} · ${t("office.opens_at", { time: status.reopensAt })}`,
      };
    case "closed": {
      const next = status.opensAt;
      if (!next) return { tone: "closed", text: t("office.closed") };
      const when = next.today
        ? t("office.opens_at", { time: next.time })
        : t("office.opens_on", { day: t(`day.${next.day}`), time: next.time });
      return { tone: "closed", text: `${t("office.closed")} · ${when}` };
    }
  }
}
