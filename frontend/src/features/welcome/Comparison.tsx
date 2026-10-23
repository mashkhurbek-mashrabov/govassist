import { Check, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { COMPARE_ROWS } from "./landingContent";

/**
 * "GovAssist vs an ordinary chatbot" (components.md → ComparisonTable): a real table with a hidden caption,
 * column and row headers. Below 768 px the CSS turns each row into a card, and the visible tags (hidden from
 * assistive tech, the header cells still label the cells) say which side each line is.
 *
 * @returns The table.
 */
export function Comparison() {
  const { t } = useTranslation();
  const bot = t("landing.compare_bot");
  return (
    <div className="lp-compare-wrap">
      <table className="lp-compare">
        <caption className="sr-only">{t("landing.compare_title")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("landing.compare_topic")}</th>
            <th scope="col" className="lp-compare__bot">
              {bot}
            </th>
            <th scope="col" className="lp-compare__us">
              GovAssist
            </th>
          </tr>
        </thead>
        <tbody>
          {COMPARE_ROWS.map((n) => (
            <tr key={n}>
              <th scope="row">{t(`landing.c${String(n)}_topic`)}</th>
              <td className="lp-compare__bot">
                <div className="lp-compare__cell">
                  <span className="lp-mark lp-mark--no">
                    <X className="icon" aria-hidden="true" />
                  </span>
                  <span>
                    <span className="lp-compare__tag" aria-hidden="true">
                      {bot}
                    </span>
                    {t(`landing.c${String(n)}_bot`)}
                  </span>
                </div>
              </td>
              <td className="lp-compare__us">
                <div className="lp-compare__cell">
                  <span className="lp-mark lp-mark--yes">
                    <Check className="icon" aria-hidden="true" />
                  </span>
                  <span>
                    <span className="lp-compare__tag" aria-hidden="true">
                      GovAssist
                    </span>
                    {t(`landing.c${String(n)}_us`)}
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
