/**
 * Mock localization (contract v1.5): office type labels and region/district names follow the language;
 * office names and addresses never change. uz-Cyrl is transliterated; ru/en use this sample table.
 */
import type { Lang, Me, OfficeMatch } from "../api/types";
import { latnToCyrl } from "../lib/translit";

/** Sample translations of the names the mocks use. */
const NAMES: Record<string, { ru: string; en: string }> = {
  "Toshkent shahri": { ru: "город Ташкент", en: "Tashkent city" },
  "Chilonzor tumani": { ru: "Чиланзарский район", en: "Chilonzor district" },
  "Davlat xizmatlari markazi": { ru: "Центр государственных услуг", en: "Public Services Centre" },
  "NAMUNA viloyati": { ru: "NAMUNA область", en: "NAMUNA region" },
  "NAMUNA tumani": { ru: "NAMUNA район", en: "NAMUNA district" },
  "NAMUNA-2 tumani": { ru: "NAMUNA-2 район", en: "NAMUNA-2 district" },
  "NAMUNA Migratsiya boʻlimi": { ru: "NAMUNA Отдел миграции", en: "NAMUNA Migration office" },
  "NAMUNA FHDYo boʻlimi": { ru: "NAMUNA Отдел ЗАГС", en: "NAMUNA Civil registry office" },
};

/**
 * A stored uz-Latn name in another language.
 *
 * @param name uz-Latn name.
 * @param lang Target language.
 * @returns The localized name (unchanged when unknown).
 */
export function localizeName(name: string, lang: Lang): string {
  if (lang === "uz-Latn") return name;
  if (lang === "uz-Cyrl") return latnToCyrl(name);
  return NAMES[name]?.[lang] ?? name;
}

/**
 * Localize a `{id, name}` place.
 *
 * @param place Region or district.
 * @param lang Target language.
 * @returns A copy with the localized name.
 */
export function localizePlace<T extends { name: string }>(place: T, lang: Lang): T {
  return { ...place, name: localizeName(place.name, lang) };
}

/**
 * `Me` as the API returns it: region and district names in the user's UI language.
 *
 * @param me Stored user.
 * @returns The response body.
 */
export function localizeMe(me: Me): Me {
  const lang = me.ui_language;
  return {
    ...me,
    region: me.region && localizePlace(me.region, lang),
    district: me.district && localizePlace(me.district, lang),
  };
}

/**
 * An office match with type label and place names localized; name and address as stored.
 *
 * @param match Stored match.
 * @param lang Target language.
 * @returns The localized copy.
 */
export function localizeOffice(match: OfficeMatch, lang: Lang): OfficeMatch {
  const officeType = { ...match.office_type, label: localizeName(match.office_type.label, lang) };
  const { office } = match;
  return {
    ...match,
    office_type: officeType,
    office: office && {
      ...office,
      office_type: officeType,
      district: localizePlace(office.district, lang),
      region: localizePlace(office.region, lang),
    },
  };
}
