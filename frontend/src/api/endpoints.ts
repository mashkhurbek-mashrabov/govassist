/** App API calls (`/api/v1/`, contract §3). Components never call these directly: use `queries.ts`. */
import { request } from "./http";
import type {
  Conversation,
  ConversationSummary,
  District,
  Feedback,
  Lang,
  Me,
  MeUpdate,
  Page,
  Region,
  SourceSummary,
  Suggestion,
} from "./types";

/** App API prefix. */
export const API_BASE = "/api/v1";

/**
 * Ask Django to set the `csrftoken` cookie. Runs once on boot.
 */
export function fetchCsrf(): Promise<void> {
  return request<undefined>(`${API_BASE}/csrf`);
}

/**
 * Resend the verification email. Always 204 so it cannot reveal whether an account exists; 429 with
 * `retry_after` when asked too often.
 *
 * @param email Address used at signup.
 */
export function resendVerification(email: string): Promise<void> {
  return request<undefined>(`${API_BASE}/auth/resend-verification`, { method: "POST", body: { email } });
}

/**
 * Reviewed sources behind the answers (About page).
 *
 * @returns Source summaries.
 */
export async function getSources(): Promise<SourceSummary[]> {
  const body = await request<{ items: SourceSummary[] }>(`${API_BASE}/sources`);
  return body.items;
}

/**
 * The signed-in user.
 *
 * @returns The `Me` object.
 */
export function getMe(): Promise<Me> {
  return request<Me>(`${API_BASE}/me`);
}

/**
 * Update language, region/district or display name.
 *
 * @param update Fields to change.
 * @returns The updated user.
 */
export function updateMe(update: MeUpdate): Promise<Me> {
  return request<Me>(`${API_BASE}/me`, { method: "PATCH", body: update });
}

/**
 * Delete the account and all its conversations.
 */
export function deleteMe(): Promise<void> {
  return request<undefined>(`${API_BASE}/me`, { method: "DELETE", body: { confirm: true } });
}

/**
 * All regions, names in `lang`.
 *
 * @param lang Language of the names.
 * @returns Regions.
 */
export function getRegions(lang: Lang): Promise<Region[]> {
  return request<Region[]>(`${API_BASE}/geo/regions?lang=${lang}`);
}

/**
 * Districts of one region, names in `lang`.
 *
 * @param regionId Region SOATO code.
 * @param lang Language of the names.
 * @returns Districts.
 */
export function getDistricts(regionId: number, lang: Lang): Promise<District[]> {
  return request<District[]>(`${API_BASE}/geo/regions/${regionId}/districts?lang=${lang}`);
}

/**
 * Starter questions for an empty chat.
 *
 * @returns Up to 6 suggestions.
 */
export async function getSuggestions(): Promise<Suggestion[]> {
  const body = await request<{ items: Suggestion[] }>(`${API_BASE}/suggestions`);
  return body.items;
}

/**
 * One page of the history, newest first.
 *
 * @param cursor Cursor from the previous page, or `null` for the first page.
 * @returns The page.
 */
export function listConversations(cursor: string | null): Promise<Page<ConversationSummary>> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  return request<Page<ConversationSummary>>(`${API_BASE}/conversations${query}`);
}

/**
 * A conversation with its messages.
 *
 * @param id Conversation id.
 * @returns The conversation.
 */
export function getConversation(id: string): Promise<Conversation> {
  return request<Conversation>(`${API_BASE}/conversations/${id}`);
}

/**
 * Delete a conversation.
 *
 * @param id Conversation id.
 */
export function deleteConversation(id: string): Promise<void> {
  return request<undefined>(`${API_BASE}/conversations/${id}`, { method: "DELETE" });
}

/**
 * Create or update feedback on an assistant message.
 *
 * @param messageId Assistant message id.
 * @param feedback Rating and optional comment.
 * @returns The stored feedback.
 */
export function sendFeedback(messageId: string, feedback: Feedback): Promise<Feedback> {
  return request<Feedback>(`${API_BASE}/messages/${messageId}/feedback`, { method: "POST", body: feedback });
}
