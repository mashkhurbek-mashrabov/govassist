/** Landing v1.3 structure: anchored sections, popular questions and service tiles (screens.md → 0. Landing). */
import {
  Baby,
  BriefcaseBusiness,
  Car,
  HandCoins,
  HeartHandshake,
  House,
  IdCard,
  Zap,
  type LucideIcon,
} from "lucide-react";

/** Anchored sections in nav order: element id and nav copy key. */
export const SECTIONS = [
  { id: "how", navKey: "nav.how" },
  { id: "why", navKey: "nav.why" },
  { id: "services", navKey: "nav.services" },
  { id: "faq", navKey: "nav.faq" },
] as const;

/** One popular-service tile: copy key under `service.*` and its icon. */
export interface ServiceTile {
  key: string;
  Icon: LucideIcon;
}

/** The eight popular services (components.md → ServiceTiles). */
export const SERVICES: readonly ServiceTile[] = [
  { key: "passport", Icon: IdCard },
  { key: "birth", Icon: Baby },
  { key: "marriage", Icon: HeartHandshake },
  { key: "driving", Icon: Car },
  { key: "property", Icon: House },
  { key: "business", Icon: BriefcaseBusiness },
  { key: "pension", Icon: HandCoins },
  { key: "utilities", Icon: Zap },
];

/** Services whose example questions are the hero's popular chips. */
export const POPULAR_SERVICES = ["passport", "driving", "pension"] as const;

/** Rows of the "GovAssist vs ordinary chatbot" table (`landing.c{n}_*`). */
export const COMPARE_ROWS = [1, 2, 3, 4, 5] as const;

/** Problem cards (`landing.p{n}`). */
export const PROBLEMS = [1, 2, 3] as const;

/** "How it works" steps (`landing.step_{n}`). */
export const STEPS = [1, 2, 3] as const;

/** FAQ entries (`landing.q{n}` / `landing.a{n}`). */
export const FAQ = [1, 2, 3, 4] as const;
