/**
 * Landing preview content: the contract §6 sample answer, shown as data in its own language (uz-Latn),
 * like an answer whose `language` differs from the UI. Layout placeholders only, never real facts.
 */
export const SAMPLE_PREVIEW = {
  lang: "uz-Latn",
  kind: "Davlat xizmati",
  title: "Pasportni almashtirish",
  steps: [
    { text: "Arizani onlayn yoki Davlat xizmatlari markazida topshiring.", cite: 1 },
    { text: "Davlat bojini toʻlang.", cite: 1 },
    { text: "Tayyor hujjatni markazdan oling.", cite: 2 },
  ],
  officeType: "Davlat xizmatlari markazi",
  badge: "Hozir ochiq · 18:00 gacha",
  address: "NAMUNA koʻchasi, 1-uy, Chilonzor tumani",
} as const;
