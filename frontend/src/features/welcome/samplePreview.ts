/**
 * Landing preview content (contract §6 sample, NAMUNA), translated into each UI language like the design's
 * `PREVIEW` sample. The office name and address stay as stored (contract v1.5), in uz-Latn. Layout
 * placeholders only, never real facts.
 */
import type { Lang } from "../../api/types";

/** One language's preview text. */
export interface PreviewText {
  kind: string;
  question: string;
  title: string;
  summary: string;
  /** The three steps with their citation numbers. */
  steps: { text: string; cite: number }[];
  officeType: string;
  badge: string;
}

/** Citation numbers of the three steps (the same in every language). */
const CITES = [1, 1, 2] as const;

/**
 * Pair step texts with their citation numbers.
 *
 * @param texts The three step texts.
 * @returns The steps.
 */
function steps(texts: readonly string[]): PreviewText["steps"] {
  return texts.map((text, index) => ({ text, cite: CITES[index] ?? 1 }));
}

/** The office as stored in the directory: shown untranslated. */
export const PREVIEW_OFFICE = {
  lang: "uz-Latn",
  name: "NAMUNA Chilonzor tumani Davlat xizmatlari markazi",
  address: "NAMUNA koʻchasi, 1-uy, Chilonzor tumani",
} as const;

/** The preview in each UI language. */
export const PREVIEW: Record<Lang, PreviewText> = {
  "uz-Latn": {
    kind: "Davlat xizmati",
    question: "Pasportimni qanday yangilayman?",
    title: "Pasportni almashtirish",
    summary: "Pasportni almashtirish uchun ariza topshirasiz va tayyor hujjatni olasiz.",
    steps: steps([
      "Arizani onlayn yoki Davlat xizmatlari markazida topshiring.",
      "Davlat bojini toʻlang.",
      "Tayyor hujjatni markazdan oling.",
    ]),
    officeType: "Davlat xizmatlari markazi",
    badge: "Hozir ochiq · 18:00 gacha",
  },
  "uz-Cyrl": {
    kind: "Давлат хизмати",
    question: "Паспортимни қандай янгилайман?",
    title: "Паспортни алмаштириш",
    summary: "Паспортни алмаштириш учун ариза топширасиз ва тайёр ҳужжатни оласиз.",
    steps: steps([
      "Аризани онлайн ёки Давлат хизматлари марказида топширинг.",
      "Давлат божини тўланг.",
      "Тайёр ҳужжатни марказдан олинг.",
    ]),
    officeType: "Давлат хизматлари маркази",
    badge: "Ҳозир очиқ · 18:00 гача",
  },
  ru: {
    kind: "Госуслуга",
    question: "Как заменить паспорт?",
    title: "Замена паспорта",
    summary: "Чтобы заменить паспорт, подайте заявление и получите готовый документ.",
    steps: steps([
      "Подайте заявление онлайн или в Центре государственных услуг.",
      "Оплатите госпошлину.",
      "Получите готовый документ в центре.",
    ]),
    officeType: "Центр государственных услуг",
    badge: "Сейчас открыто · до 18:00",
  },
  en: {
    kind: "Public service",
    question: "How do I renew my passport?",
    title: "Replacing a passport",
    summary: "To replace your passport, you submit an application and collect the finished document.",
    steps: steps([
      "Submit the application online or at a Public Services Centre.",
      "Pay the state fee.",
      "Collect the finished document at the centre.",
    ]),
    officeType: "Public Services Centre",
    badge: "Open now · until 18:00",
  },
};
