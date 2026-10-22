/**
 * Contract v1.1 types, hand-written from `docs/contract.md` §1, §3–§5.
 * F3 replaces them with types generated from `docs/schema/`.
 */

/** UI and answer languages (contract §1). */
export type Lang = "uz-Latn" | "uz-Cyrl" | "ru" | "en";

/** RFC 9457 problem body returned by `/api/v1/` errors (contract §1). */
export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  /** One of the contract §1 codes (`rate_limited`, `validation_error`, …). */
  code: string;
  retry_after?: number | null;
  errors?: Record<string, string[]> | null;
  /** Only on `quota_exceeded`: whose daily limit was hit. */
  scope?: QuotaScope;
}

/** `user`: this user's daily limit; `global`: the service-wide daily token cap. */
export type QuotaScope = "user" | "global";

/** Cursor-paginated list (contract §1). */
export interface Page<T> {
  results: T[];
  next: string | null;
}

/** Region (SOATO code + localized name). */
export interface Region {
  id: number;
  name: string;
}

/** District (SOATO code + localized name). */
export interface District {
  id: number;
  name: string;
}

/** Per-user question quota (part of `Me`). */
export interface Quota {
  hour_limit: number;
  hour_used: number;
  day_limit: number;
  day_used: number;
}

/** The signed-in user (`GET /api/v1/me`). */
export interface Me {
  id: string;
  email: string;
  email_verified: boolean;
  /** False for Google-only accounts: changing the password then needs no current password. */
  has_password: boolean;
  display_name: string | null;
  ui_language: Lang;
  region: Region | null;
  district: District | null;
  profile_complete: boolean;
  quota: Quota;
}

/** Body of `PATCH /api/v1/me`. */
export interface MeUpdate {
  ui_language?: Lang;
  region_id?: number;
  district_id?: number;
  display_name?: string;
}

/** One starter question (`GET /api/v1/suggestions`). */
export interface Suggestion {
  text: string;
  category: string;
}

/** Item in the history list. */
export interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
  last_message_preview: string;
}

/** A full conversation with its messages. */
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

/** A user's question as stored (PII already scrubbed). */
export interface UserMessage {
  id: string;
  role: "user";
  text: string;
  created_at: string;
}

/** Lifecycle of an assistant message. */
export type AssistantStatus = "streaming" | "complete" | "failed";

/** Why a stored assistant message failed (`"stopped"`: the user pressed Stop). */
export type AssistantErrorCode = "stopped" | StreamErrorCode;

/** An assistant answer as stored. */
export interface AssistantMessage {
  id: string;
  role: "assistant";
  created_at: string;
  status: AssistantStatus;
  /** Set when `status` is `"failed"`. */
  error_code: AssistantErrorCode | null;
  answer: Answer | null;
  sources: Source[];
  office: OfficeMatch | null;
  refused: boolean;
  feedback: Feedback | null;
}

/** Any message in a conversation. */
export type Message = UserMessage | AssistantMessage;

/** Thumbs up/down feedback on an assistant message. */
export interface Feedback {
  rating: 1 | -1;
  comment: string;
}

/** Answer kinds (contract §5). */
export type AnswerType = "service" | "legal" | "not_found" | "off_topic";

/** A cited text item. `source_ids` refer to `Source.id` (`S1`…). */
export interface Item {
  text: string;
  source_ids: string[];
}

/** A quoted legal clause with a plain-language explanation. */
export interface LawPoint {
  quote: string;
  explanation: string;
  source_ids: string[];
}

/** Structured answer (contract §5). Field order is fixed so the summary streams first. */
export interface Answer {
  answer_type: AnswerType;
  language: Lang;
  title: string;
  summary: string;
  steps: Item[];
  documents: Item[];
  fee: Item | null;
  processing_time: Item | null;
  law_points: LawPoint[];
  follow_up_questions: string[];
}

/** A cited corpus document. */
export interface Source {
  id: string;
  kind: "law" | "service_page" | "other";
  title: string;
  publisher: string;
  url: string;
  section: string | null;
  published_at: string | null;
  fetched_at: string;
}

/** Office type code + localized label. */
export interface OfficeType {
  code: string;
  label: string;
}

/** Weekday codes used in working hours. */
export type Weekday = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

/** One opening-hours rule. Times are `HH:MM` in Asia/Tashkent. */
export interface WorkingHours {
  days: Weekday[];
  open: string;
  close: string;
  break: { start: string; end: string } | null;
}

/** A government office from the directory (never model output). */
export interface Office {
  id: string;
  name: string;
  office_type: OfficeType;
  address: string;
  district: District;
  region: Region;
  phone: string | null;
  working_hours: WorkingHours[];
  latitude: number | null;
  longitude: number | null;
  map_url: string;
  data_as_of: string;
  source_url: string;
}

/** Office lookup result for the user's district. */
export interface OfficeMatch {
  match: "district" | "region" | "none";
  office_type: OfficeType;
  office: Office | null;
}

/** Body of `POST /api/v1/chat`. */
export interface ChatRequest {
  conversation_id: string | null;
  text: string;
}

/** `meta` event data (contract §4). */
export interface MetaEventData {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
}

/** Progress stages of `status` events. */
export type Stage = "searching" | "found" | "writing";

/** `status` event data. */
export interface StatusEventData {
  stage: Stage;
  source_count?: number;
}

/** `delta` event data: a raw fragment of the Answer JSON. */
export interface DeltaEventData {
  text: string;
}

/** `final` event data. */
export interface FinalEventData {
  message: AssistantMessage;
}

/** Codes of in-stream `error` events. */
export type StreamErrorCode =
  "llm_unavailable" | "llm_timeout" | "invalid_answer" | "quota_exceeded" | "internal_error";

/** `error` event data. */
export interface ErrorEventData {
  code: StreamErrorCode;
  message: string;
  /** Only for `quota_exceeded`. */
  scope?: QuotaScope;
}

/** A corpus source listed on the About page (`GET /api/v1/sources`). */
export interface SourceSummary {
  publisher: string;
  name: string;
  kind: "law" | "service_page" | "office" | "other";
  url: string;
  documents: number;
  last_fetched_at: string;
}

/** A typed SSE event from the chat stream. */
export type ChatEvent =
  | { event: "meta"; data: MetaEventData }
  | { event: "status"; data: StatusEventData }
  | { event: "office"; data: OfficeMatch }
  | { event: "delta"; data: DeltaEventData }
  | { event: "final"; data: FinalEventData }
  | { event: "error"; data: ErrorEventData }
  | { event: "done"; data: Record<string, never> };

/** Name of a chat stream event. */
export type ChatEventName = ChatEvent["event"];
