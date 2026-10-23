/**
 * The question carried from the landing to the first chat (screens.md → Landing → Carrying the question).
 * It lives in sessionStorage only, never in the URL, because it can contain personal data; the backend scrubs
 * it like any question once it is sent.
 */

/** sessionStorage key (screens.md). */
const PENDING_QUESTION_KEY = "govassist.pendingQuestion";
/** Longest question kept; the composer refuses more than this anyway. */
const MAX_QUESTION_LENGTH = 1000;

/**
 * Keep a question for after sign-up.
 *
 * @param text The question as typed or chosen.
 */
export function savePendingQuestion(text: string): void {
  const question = text.trim().slice(0, MAX_QUESTION_LENGTH);
  if (!question) return;
  try {
    sessionStorage.setItem(PENDING_QUESTION_KEY, question);
  } catch {
    // Storage can be blocked (private mode); the user then simply asks again after signing up.
  }
}

/**
 * The question waiting to be asked, if any.
 *
 * @returns The question, or `null`.
 */
export function readPendingQuestion(): string | null {
  try {
    return sessionStorage.getItem(PENDING_QUESTION_KEY);
  } catch {
    return null;
  }
}

/**
 * Take the waiting question out of storage (so it is asked once).
 *
 * @returns The question, or `null` when none was waiting.
 */
export function takePendingQuestion(): string | null {
  const question = readPendingQuestion();
  try {
    sessionStorage.removeItem(PENDING_QUESTION_KEY);
  } catch {
    // Nothing to clear when storage is blocked.
  }
  return question;
}
