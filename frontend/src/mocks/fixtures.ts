/**
 * Mock data built from docs/contract.md §3 and §6. Every value is a layout placeholder (NAMUNA / SAMPLE),
 * never real information: no real fees, addresses, phone numbers or SOATO codes.
 */
import type { Answer, District, OfficeMatch, Region, Source, Suggestion } from "../api/types";

/** Contract §6 sample service answer (illustrative values). */
export const SAMPLE_SERVICE_ANSWER: Answer = {
  answer_type: "service",
  language: "uz-Latn",
  title: "Pasportni almashtirish",
  summary: "Pasportni almashtirish uchun ariza topshirasiz va tayyor hujjatni olasiz.",
  steps: [
    { text: "Arizani onlayn yoki Davlat xizmatlari markazida topshiring.", source_ids: ["S1"] },
    { text: "Davlat bojini toʻlang.", source_ids: ["S1"] },
    { text: "Tayyor hujjatni markazdan oling.", source_ids: ["S2"] },
  ],
  documents: [
    { text: "Eski pasport", source_ids: ["S1"] },
    { text: "Toʻlov kvitansiyasi", source_ids: ["S1"] },
  ],
  fee: { text: "NAMUNA: bazaviy hisoblash miqdorining X foizi", source_ids: ["S1"] },
  processing_time: { text: "NAMUNA: N ish kuni", source_ids: ["S2"] },
  law_points: [],
  follow_up_questions: ["Pasportni onlayn almashtirsa boʻladimi?"],
};

/** Contract §6 sample sources. */
export const SAMPLE_SOURCES: Source[] = [
  {
    id: "S1",
    kind: "service_page",
    title: "NAMUNA xizmat sahifasi",
    publisher: "my.gov.uz",
    url: "https://my.gov.uz/",
    section: null,
    published_at: null,
    fetched_at: "2026-10-20T08:00:00Z",
  },
  {
    id: "S2",
    kind: "law",
    title: "NAMUNA nizom",
    publisher: "lex.uz",
    url: "https://lex.uz/",
    section: "12-band",
    published_at: "2024-01-01",
    fetched_at: "2026-10-20T08:00:00Z",
  },
];

/** Contract §6 sample office match. */
export const SAMPLE_OFFICE: OfficeMatch = {
  match: "district",
  office_type: { code: "public_service_center", label: "Davlat xizmatlari markazi" },
  office: {
    id: "0d7e0000-0000-4000-8000-000000000001",
    name: "NAMUNA Chilonzor tumani Davlat xizmatlari markazi",
    office_type: { code: "public_service_center", label: "Davlat xizmatlari markazi" },
    address: "NAMUNA koʻchasi, 1-uy",
    district: { id: 1726269, name: "Chilonzor tumani" },
    region: { id: 1726, name: "Toshkent shahri" },
    phone: "+998 71 000 00 00",
    working_hours: [
      {
        days: ["mon", "tue", "wed", "thu", "fri"],
        open: "09:00",
        close: "18:00",
        break: { start: "13:00", end: "14:00" },
      },
      { days: ["sat"], open: "09:00", close: "13:00", break: null },
    ],
    latitude: null,
    longitude: null,
    map_url: "https://www.google.com/maps/search/?api=1&query=NAMUNA",
    data_as_of: "2026-10-20",
    source_url: "https://example.org/offices",
  },
};

/** Off-topic sample: only title, summary and follow-ups (contract §5 rules). */
export const SAMPLE_OFF_TOPIC_ANSWER: Answer = {
  answer_type: "off_topic",
  language: "uz-Latn",
  title: "NAMUNA: mavzudan tashqari savol",
  summary: "NAMUNA: GovAssist faqat davlat xizmatlari va qonunlar haqidagi savollarga javob beradi.",
  steps: [],
  documents: [],
  fee: null,
  processing_time: null,
  law_points: [],
  follow_up_questions: ["Pasportimni qanday yangilayman?"],
};

/** Regions: the contract's illustrative Tashkent id plus one obviously fake region. */
export const SAMPLE_REGIONS: Region[] = [
  { id: 1726, name: "Toshkent shahri" },
  { id: 90001, name: "NAMUNA viloyati" },
];

/** Districts per region (contract example + fake ids). */
export const SAMPLE_DISTRICTS: Record<number, District[]> = {
  1726: [
    { id: 1726269, name: "Chilonzor tumani" },
    { id: 172690001, name: "NAMUNA tumani" },
  ],
  90001: [{ id: 9000101, name: "NAMUNA-2 tumani" }],
};

/** Starter questions. */
export const SAMPLE_SUGGESTIONS: Suggestion[] = [
  { text: "Pasportimni qanday yangilayman?", category: "documents" },
  { text: "Tugʻilganlik haqidagi guvohnomani qanday olaman?", category: "civil_registry" },
  { text: "Ishdan boʻshatilganda qanday huquqlarim bor?", category: "legal" },
];
