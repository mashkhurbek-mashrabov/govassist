/**
 * API types, built on the ones generated from `docs/schema/` (`npm run gen:types`), under the names the app
 * uses. Where the generated schema is looser than `docs/contract.md` (the source of truth), the type is
 * narrowed here and marked "Schema gap"; those are reported as contract change requests.
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

/** RFC 9457 problem body returned by `/api/v1/` errors (contract §1). */
export type Problem = Schemas["Problem"];

/** Cursor-paginated list (contract §1). */
export interface Page<T> {
  results: T[];
  next: string | null;
}

/** Region (SOATO code + localized name). */
export type Region = Schemas["Place"];

/** District (SOATO code + localized name). */
export type District = Schemas["Place"];

/** Per-user question quota (part of `Me`). */
export type Quota = Schemas["Quota"];

/** The signed-in user (`GET /api/v1/me`). */
export type Me = Schemas["Me"];

/** Body of `PATCH /api/v1/me`. */
export type MeUpdate = Schemas["PatchedMeUpdateRequest"];

/** One starter question (`GET /api/v1/suggestions`). */
export type Suggestion = Schemas["Suggestion"];

/** Item in the history list. */
export type ConversationSummary = Schemas["ConversationSummary"];

/** A full conversation with its messages. */
export type Conversation = Schemas["Conversation"];

/** A user's question as stored (PII already scrubbed). */
export type UserMessage = Schemas["UserMessage"];

/** Lifecycle of an assistant message. */
export type AssistantStatus = Schemas["StatusEnum"];

/** Why a stored assistant message failed (`"stopped"`: the user pressed Stop). */
export type AssistantErrorCode = Schemas["MessageErrorCodeEnum"];

/** An assistant answer as stored. */
export type AssistantMessage = Schemas["AssistantMessage"];

/** Any message in a conversation. */
export type Message = Schemas["Message"];

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
 * Schema gap: `kind` is generated as a plain string; the contract fixes it to these four values.
 */
export interface SourceSummary extends Omit<Schemas["SourceSummary"], "kind"> {
  kind: "law" | "service_page" | "office" | "other";
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
