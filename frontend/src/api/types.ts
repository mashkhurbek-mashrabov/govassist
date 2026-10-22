/**
 * API types, built on the ones generated from `docs/schema/` (`npm run gen:types`), under the names the app
 * uses. Where the generated schema is looser or wrong compared with `docs/contract.md` (the source of truth),
 * the type is narrowed here and marked "Schema gap"; those are reported as contract change requests.
 * The SSE events (contract §4) are not in OpenAPI, so they are written here from the contract.
 */
import type { Answer as GeneratedAnswer } from "./generated/answer";
import type { components } from "./generated/openapi";

/** Generated OpenAPI schemas. */
type Schemas = components["schemas"];

/** UI and answer languages (contract §1). */
export type Lang = Schemas["LangCode"];

/** `user`: this user's daily limit; `global`: the service-wide daily token cap. */
export type QuotaScope = NonNullable<Schemas["Problem"]["scope"]>;

/**
 * RFC 9457 problem body returned by `/api/v1/` errors (contract §1).
 * Schema gap: `errors` is `{field: [messages]}` (generated as `Record<string, never>`), `detail` may be
 * missing, and `retry_after` is present only on `rate_limited` / `quota_exceeded`.
 */
export interface Problem extends Omit<Schemas["Problem"], "errors" | "detail" | "retry_after"> {
  detail?: string;
  errors?: Record<string, string[]> | null;
  retry_after?: number | null;
}

/** Cursor-paginated list (contract §1). */
export interface Page<T> {
  results: T[];
  next: string | null;
}

/** Region (SOATO code + localized name). */
export type Region = Schemas["Place"];

/** District (SOATO code + localized name). */
export type District = Schemas["Place"];

/** Per-user question quota (part of `Me`). Schema gap: generated as a free-form number map. */
export interface Quota {
  hour_limit: number;
  hour_used: number;
  day_limit: number;
  day_used: number;
}

/** The signed-in user (`GET /api/v1/me`). */
export interface Me extends Omit<Schemas["Me"], "quota" | "ui_language"> {
  ui_language: Lang;
  quota: Quota;
}

/** Body of `PATCH /api/v1/me`. */
export type MeUpdate = Schemas["PatchedMeUpdateRequest"];

/** One starter question (`GET /api/v1/suggestions`). */
export type Suggestion = Schemas["Suggestion"];

/** Item in the history list. Schema gap: `title` is always present (contract §3). */
export interface ConversationSummary extends Omit<Schemas["ConversationSummary"], "title"> {
  title: string;
}

/** A full conversation with its messages. Schema gap: `title` is always present. */
export interface Conversation extends Omit<Schemas["Conversation"], "title" | "messages"> {
  title: string;
  messages: Message[];
}

/** A user's question as stored (PII already scrubbed). Schema gap: `role` is generated as `"UserMessage"`. */
export interface UserMessage extends Omit<Schemas["UserMessage"], "role"> {
  role: "user";
}

/** Lifecycle of an assistant message. */
export type AssistantStatus = Schemas["StatusEnum"];

/** Why a stored assistant message failed (`"stopped"`: the user pressed Stop). */
export type AssistantErrorCode = "stopped" | StreamErrorCode;

/**
 * An assistant answer as stored.
 * Schema gap: `role` is generated as `"None"`; `answer` and `office` are nullable and `error_code` is an enum
 * (contract §3), but generated as non-null / a plain string.
 */
export interface AssistantMessage extends Omit<
  Schemas["AssistantMessage"],
  "role" | "error_code" | "answer" | "office" | "sources"
> {
  role: "assistant";
  /** Set when `status` is `"failed"`. */
  error_code: AssistantErrorCode | null;
  answer: Answer | null;
  sources: Source[];
  office: OfficeMatch | null;
}

/** Any message in a conversation. */
export type Message = UserMessage | AssistantMessage;

/** Thumbs up/down feedback on an assistant message. */
export type Feedback = Schemas["Feedback"];

/** Answer kinds (contract §5). */
export type AnswerType = Schemas["AnswerType"];

/** A cited text item. `source_ids` refer to `Source.id` (`S1`…). */
export type Item = Schemas["Item"];

/** A quoted legal clause with a plain-language explanation. */
export type LawPoint = Schemas["LawPoint"];

/** Structured answer (contract §5, `answer.schema.json`). Field order is fixed so the summary streams first. */
export type Answer = GeneratedAnswer;

/** A cited corpus document. */
export type Source = Schemas["Source"];

/** Office type code + localized label. */
export type OfficeType = Schemas["OfficeTypeRef"];

/** Weekday codes used in working hours. */
export type Weekday = Schemas["Day"];

/** One opening-hours rule. Times are `HH:MM` in Asia/Tashkent. */
export type WorkingHours = Schemas["WorkingHours"];

/** A government office from the directory (never model output). */
export type Office = Schemas["OfficeOut"];

/** Office lookup result for the user's district. */
export type OfficeMatch = Schemas["OfficeMatch"];

/** Body of `POST /api/v1/chat`. */
export type ChatRequest = Schemas["ChatRequest"];

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
  | "llm_unavailable"
  | "llm_timeout"
  | "invalid_answer"
  | "quota_exceeded"
  /** Contract v1.6: can be the first and only event (no `meta`) when another stream won the lock race. */
  | "stream_in_progress"
  | "internal_error";

/** `error` event data. */
export interface ErrorEventData {
  code: StreamErrorCode;
  message: string;
  /** Only for `quota_exceeded`. */
  scope?: QuotaScope;
}

/**
 * A corpus source listed on the About page (`GET /api/v1/sources` → `{items: SourceSummary[]}`).
 * Schema gap: the endpoint's response is generated as `Source[]` (its inline "SourceList" collides with the
 * messages' `SourceList`), so this type is written from the contract and `collector/api/serializers.py`.
 */
export interface SourceSummary {
  publisher: string;
  name: string;
  kind: "law" | "service_page" | "office" | "other";
  url: string;
  documents: number;
  /** Null until the source was crawled; the UI then hides the date (contract v1.4). */
  last_fetched_at: string | null;
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
