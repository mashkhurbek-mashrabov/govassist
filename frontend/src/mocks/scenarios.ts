/**
 * Mock answers for the design journeys J1–J6 (docs/design/screens.md), picked by words in the question.
 * Everything beyond contract §6 is marked NAMUNA / SAMPLE: no real fees, addresses, phones or law text.
 */
import type { Answer, OfficeMatch, Source } from "../api/types";
import { SAMPLE_OFF_TOPIC_ANSWER, SAMPLE_OFFICE, SAMPLE_SERVICE_ANSWER, SAMPLE_SOURCES } from "./fixtures";

/** What the mock streams for one question. */
export interface Scenario {
  answer: Answer;
  sources: Source[];
  office: OfficeMatch | null;
  /** Early `office` event when it differs from the final one (contract v1.7: refused answers drop it). */
  earlyOffice?: OfficeMatch;
}

/**
 * A NAMUNA source.
 *
 * @param id `S` label.
 * @param kind Source kind.
 * @param title Title.
 * @param publisher Publisher domain.
 * @param section Section label or null.
 * @returns The source.
 */
function sampleSource(
  id: string,
  kind: Source["kind"],
  title: string,
  publisher: string,
  section: string | null,
): Source {
  return {
    id,
    kind,
    title,
    publisher,
    url: `https://${publisher}/`,
    section,
    published_at: kind === "law" ? "2024-01-01" : null,
    fetched_at: "2026-10-20T08:00:00Z",
  };
}

/** J1 second turn: short service answer, no office. */
const ONLINE_PASSPORT: Scenario = {
  answer: {
    ...SAMPLE_SERVICE_ANSWER,
    title: "NAMUNA: Pasportni onlayn almashtirish",
    summary: "NAMUNA: arizani onlayn topshirish mumkin, hujjatni markazdan olasiz.",
    steps: [
      { text: "NAMUNA: arizani onlayn portal orqali yuboring.", source_ids: ["S1"] },
      { text: "NAMUNA: tayyor hujjatni markazdan oling.", source_ids: ["S1"] },
    ],
    documents: [],
    follow_up_questions: [],
  },
  sources: [SAMPLE_SOURCES[0] as Source],
  office: null,
};

/** J2: legal answer in Uzbek Cyrillic (the question's script), two law points. */
const LEAVE_LEGAL: Scenario = {
  answer: {
    answer_type: "legal",
    language: "uz-Cyrl",
    title: "NAMUNA: Йиллик меҳнат таътили",
    summary: "NAMUNA: қисқа жавоб бу ерда туради.",
    steps: [
      { text: "NAMUNA: биринчи қилиш мумкин бўлган иш.", source_ids: ["S1"] },
      { text: "NAMUNA: иккинчи иш.", source_ids: [] },
    ],
    documents: [],
    fee: null,
    processing_time: null,
    law_points: [
      {
        quote: "NAMUNA: Меҳнат кодексидан аниқ иқтибос шу ерда туради.",
        explanation: "NAMUNA: шу қоиданинг оддий тилдаги изоҳи.",
        source_ids: ["S1"],
      },
      { quote: "NAMUNA: иккинчи иқтибос.", explanation: "NAMUNA: иккинчи изоҳ.", source_ids: ["S1", "S2"] },
    ],
    follow_up_questions: ["NAMUNA: Таътилни бўлиб олса бўладими?"],
  },
  sources: [
    sampleSource("S1", "law", "NAMUNA Mehnat kodeksi", "lex.uz", "NAMUNA-modda"),
    sampleSource("S2", "law", "NAMUNA nizom", "lex.uz", "12-band"),
  ],
  office: null,
};

/** J3: Russian service answer; the office is elsewhere in the region with unknown hours and phone. */
const RESIDENCE_RU: Scenario = {
  answer: {
    answer_type: "service",
    language: "ru",
    title: "NAMUNA: Регистрация по месту жительства",
    summary: "NAMUNA: краткий ответ на русском языке.",
    steps: [
      { text: "NAMUNA: подайте заявление.", source_ids: ["S1"] },
      { text: "NAMUNA: получите отметку о регистрации.", source_ids: ["S1"] },
    ],
    documents: [
      { text: "NAMUNA: паспорт", source_ids: ["S1"] },
      { text: "NAMUNA: заявление", source_ids: [] },
    ],
    fee: { text: "NAMUNA: размер пошлины", source_ids: ["S1"] },
    processing_time: null,
    law_points: [],
    follow_up_questions: ["NAMUNA: Можно ли сделать это онлайн?"],
  },
  sources: [sampleSource("S1", "service_page", "NAMUNA страница услуги", "my.gov.uz", null)],
  office: {
    match: "region",
    office_type: { code: "migration", label: "NAMUNA Migratsiya boʻlimi" },
    office: {
      id: "0d7e0000-0000-4000-8000-000000000002",
      name: "NAMUNA Toshkent shahri migratsiya boʻlimi",
      office_type: { code: "migration", label: "NAMUNA Migratsiya boʻlimi" },
      address: "NAMUNA koʻchasi, 2-uy",
      district: { id: 172690001, name: "NAMUNA tumani" },
      region: { id: 1726, name: "Toshkent shahri" },
      phone: null,
      working_hours: [],
      latitude: null,
      longitude: null,
      map_url: "https://www.google.com/maps/search/?api=1&query=NAMUNA",
      data_as_of: "2026-10-20",
      source_url: "https://example.org/offices",
    },
  },
};

/** J4: the topic chips offered by the off-topic and not-found answers. */
const TOPICS = ["NAMUNA savol: tugʻilganlik haqida guvohnoma", "Pasportimni qanday yangilayman?"];

/** J4 step 1: off topic. */
const OFF_TOPIC: Scenario = {
  answer: {
    ...SAMPLE_OFF_TOPIC_ANSWER,
    title: "NAMUNA: bu mavzuda yordam bera olmayman",
    follow_up_questions: TOPICS,
  },
  sources: [],
  office: null,
};

/** Contract v1.7: off topic, but retrieval matched an office first; `final` drops it. */
const OFF_TOPIC_EARLY_OFFICE: Scenario = { ...OFF_TOPIC, earlyOffice: SAMPLE_OFFICE };

/** J4 step 2: not found. */
const NOT_FOUND: Scenario = {
  answer: {
    ...SAMPLE_OFF_TOPIC_ANSWER,
    answer_type: "not_found",
    title: "NAMUNA: aniq javob topilmadi",
    summary: "NAMUNA: bu savol boʻyicha bazada ishonchli maʼlumot yoʻq.",
    follow_up_questions: [],
  },
  sources: [],
  office: null,
};

/** J4 step 3: birth certificate with the civil-registry office (weekday lunch break 13:00–14:00). */
const BIRTH_CERTIFICATE: Scenario = {
  answer: {
    ...SAMPLE_SERVICE_ANSWER,
    title: "NAMUNA: Tugʻilganlik haqida guvohnoma olish",
    summary: "NAMUNA: guvohnoma FHDYo boʻlimida beriladi.",
    steps: [
      { text: "NAMUNA: FHDYo boʻlimiga murojaat qiling.", source_ids: ["S1"] },
      { text: "NAMUNA: guvohnomani oling.", source_ids: ["S1"] },
    ],
    documents: [{ text: "NAMUNA: tibbiy maʼlumotnoma", source_ids: ["S1"] }],
    follow_up_questions: ["NAMUNA: Guvohnomani onlayn olsa boʻladimi?"],
  },
  sources: [SAMPLE_SOURCES[0] as Source],
  office: {
    match: "district",
    office_type: { code: "civil_registry", label: "NAMUNA FHDYo boʻlimi" },
    office: {
      ...(SAMPLE_OFFICE.office as NonNullable<OfficeMatch["office"]>),
      id: "0d7e0000-0000-4000-8000-000000000003",
      name: "NAMUNA Chilonzor tumani FHDYo boʻlimi",
      office_type: { code: "civil_registry", label: "NAMUNA FHDYo boʻlimi" },
    },
  },
};

/** J5: driving licence (streams long enough to press Stop). */
const DRIVING_LICENCE: Scenario = {
  answer: {
    ...SAMPLE_SERVICE_ANSWER,
    title: "NAMUNA: Haydovchilik guvohnomasini almashtirish",
    summary: "NAMUNA: guvohnomani almashtirish uchun ariza topshirasiz.",
    follow_up_questions: [],
  },
  sources: SAMPLE_SOURCES,
  office: SAMPLE_OFFICE,
};

/** Default: contract §6 passport answer (J1, J6). */
const PASSPORT: Scenario = { answer: SAMPLE_SERVICE_ANSWER, sources: SAMPLE_SOURCES, office: SAMPLE_OFFICE };

/** Question words → scenario, checked in order (lowercase). */
const RULES: [RegExp, Scenario][] = [
  [/onlayn almashtir/, ONLINE_PASSPORT],
  [/таътил/, LEAVE_LEGAL],
  [/регистр|прописк/, RESIDENCE_RU],
  [/idora.*ob-havo|#provisional/, OFF_TOPIC_EARLY_OFFICE],
  [/ob-havo|#offtopic/, OFF_TOPIC],
  [/^namuna savol: tugʻilganlik haqida guvohnoma$/, NOT_FOUND],
  [/tugʻilganlik/, BIRTH_CERTIFICATE],
  [/haydovchilik/, DRIVING_LICENCE],
];

/**
 * Pick the scenario for a question.
 *
 * @param text The question.
 * @returns The scenario (passport by default).
 */
export function scenarioFor(text: string): Scenario {
  const lower = text.trim().toLowerCase();
  return RULES.find(([pattern]) => pattern.test(lower))?.[1] ?? PASSPORT;
}
