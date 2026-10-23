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

/**
 * Contract v1.10 smalltalk: a greeting answered in the question's language with example questions.
 *
 * @param language Language of the greeting.
 * @param title NAMUNA title.
 * @param summary NAMUNA friendly summary.
 * @param questions Example service questions.
 * @returns The scenario (no sources, no office).
 */
function smalltalk(
  language: Answer["language"],
  title: string,
  summary: string,
  questions: string[],
): Scenario {
  return {
    answer: {
      ...SAMPLE_OFF_TOPIC_ANSWER,
      answer_type: "smalltalk",
      language,
      title,
      summary,
      follow_up_questions: questions,
    },
    sources: [],
    office: null,
  };
}

/** Greetings per language (contract v1.10). */
const SMALLTALK_UZ = smalltalk(
  "uz-Latn",
  "NAMUNA: Salom!",
  "NAMUNA: Men GovAssist — davlat xizmatlari va qonunlar boʻyicha yordamchiman. Savolingizni oddiy soʻzlar bilan yozing.",
  ["Pasportimni qanday yangilayman?", "NAMUNA savol: tugʻilganlik haqida guvohnoma"],
);
const SMALLTALK_RU = smalltalk(
  "ru",
  "NAMUNA: Здравствуйте!",
  "NAMUNA: Я GovAssist — помощник по государственным услугам и законам. Задайте вопрос простыми словами.",
  ["NAMUNA: Как зарегистрироваться по месту жительства?", "Pasportimni qanday yangilayman?"],
);
const SMALLTALK_EN = smalltalk(
  "en",
  "NAMUNA: Hello!",
  "NAMUNA: I'm GovAssist, an assistant for public services and laws in Uzbekistan. Ask in plain words.",
  ["Pasportimni qanday yangilayman?", "NAMUNA savol: haydovchilik guvohnomasini almashtirish"],
);

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
  [/^(salom|assalomu alaykum)\b/u, SMALLTALK_UZ],
  [/^(привет|здравствуйте)/u, SMALLTALK_RU],
  [/^(hello|hi)\b/u, SMALLTALK_EN],
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

/** "List the sources" requests per question language (contract v1.11). */
const SOURCES_REQUESTS: [RegExp, Answer["language"]][] = [
  [/manbalar(ni|i)?\b/u, "uz-Latn"],
  [/источник/u, "ru"],
  [/\bsources\b/u, "en"],
];

/** NAMUNA title and summaries of a `sources` answer per language: with and without earlier citations. */
const SOURCES_TEXT: Record<Answer["language"], { title: string; some: string; none: string }> = {
  "uz-Latn": {
    title: "NAMUNA: Ushbu suhbat manbalari",
    some: "NAMUNA: Bu suhbatdagi javoblar quyidagi manbalarga asoslangan.",
    none: "NAMUNA: Bu suhbatda hali hech qanday manbaga tayanilmagan.",
  },
  "uz-Cyrl": {
    title: "NAMUNA: Ушбу суҳбат манбалари",
    some: "NAMUNA: Бу суҳбатдаги жавоблар қуйидаги манбаларга асосланган.",
    none: "NAMUNA: Бу суҳбатда ҳали ҳеч қандай манбага таянилмаган.",
  },
  ru: {
    title: "NAMUNA: Источники этого разговора",
    some: "NAMUNA: Ответы в этом разговоре основаны на этих источниках.",
    none: "NAMUNA: В этом разговоре пока не было ссылок на источники.",
  },
  en: {
    title: "NAMUNA: Sources of this conversation",
    some: "NAMUNA: The answers in this conversation are based on these sources.",
    none: "NAMUNA: Nothing has been cited in this conversation yet.",
  },
};

/**
 * Whether a question asks for the conversation's sources, and in which language.
 *
 * @param text The question.
 * @returns The answer language, or `null` for any other question.
 */
export function sourcesRequestLanguage(text: string): Answer["language"] | null {
  const lower = text.trim().toLowerCase();
  return SOURCES_REQUESTS.find(([pattern]) => pattern.test(lower))?.[1] ?? null;
}

/**
 * The `sources` answer (contract v1.11): title and one sentence, every other field empty.
 *
 * @param language Question language.
 * @param cited How many earlier sources the conversation has.
 * @returns The answer.
 */
export function sourcesAnswer(language: Answer["language"], cited: number): Answer {
  const text = SOURCES_TEXT[language];
  return {
    ...SAMPLE_OFF_TOPIC_ANSWER,
    answer_type: "sources",
    language,
    title: text.title,
    summary: cited > 0 ? text.some : text.none,
    follow_up_questions: [],
  };
}

/**
 * The documents a conversation's earlier answers cited: deduplicated by URL, in order of first citation,
 * relabelled `S1..Sn` (contract v1.11).
 *
 * @param messages The conversation so far.
 * @returns The sources.
 */
export function earlierSources(messages: readonly { role: string; sources?: Source[] }[]): Source[] {
  const seen = new Set<string>();
  const out: Source[] = [];
  for (const message of messages) {
    if (message.role !== "assistant") continue;
    for (const source of message.sources ?? []) {
      if (seen.has(source.url)) continue;
      seen.add(source.url);
      out.push({ ...source, id: `S${String(out.length + 1)}` });
    }
  }
  return out;
}
