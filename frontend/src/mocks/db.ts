/**
 * In-memory backend state for MSW. In the browser it is mirrored to sessionStorage (mock mode only) so a
 * full reload, e.g. opening the logged verification link, keeps the mock session. Holds sample data only.
 */
import type { AssistantMessage, Conversation, Me } from "../api/types";
import {
  SAMPLE_OFFICE,
  SAMPLE_REGIONS,
  SAMPLE_DISTRICTS,
  SAMPLE_SERVICE_ANSWER,
  SAMPLE_SOURCES,
} from "./fixtures";

/** sessionStorage key of the mirrored mock state. */
const STORAGE_KEY = "govassist.mock-db";
/** Seeded, ready-to-use account (any password works except the sentinel below). */
export const SEED_EMAIL = "namuna@example.com";
/** Seeded Google-only account (`has_password: false`), for the set-password flow. */
export const GOOGLE_ONLY_EMAIL = "google-namuna@example.com";
/** Password the mock always rejects, to exercise error paths. */
export const WRONG_PASSWORD = "wrong-password";

/** Everything the mock backend remembers. */
export interface MockState {
  users: Record<string, Me>;
  sessionEmail: string | null;
  pendingEmail: string | null;
  verificationKeys: Record<string, string>;
  resetKeys: Record<string, string>;
  /** Epoch ms of the last verification resend, for the mock rate limit. */
  lastResendAt: number | null;
  conversations: Record<string, Conversation & { owner: string }>;
}

/** Fixed timestamp for seeded rows. */
const SEED_TIME = "2026-10-22T09:15:00Z";

/**
 * A fresh `Me` for an email.
 *
 * @param email Account email.
 * @param verified Whether the email is verified.
 * @returns The user.
 */
export function newUser(email: string, verified: boolean): Me {
  return {
    id: crypto.randomUUID(),
    email,
    email_verified: verified,
    has_password: true,
    display_name: null,
    ui_language: "uz-Latn",
    region: null,
    district: null,
    profile_complete: false,
    quota: { hour_limit: 20, hour_used: 0, day_limit: 100, day_used: 0 },
  };
}

/**
 * The sample assistant message from contract §6 with a given id.
 *
 * @param id Message id.
 * @returns A complete assistant message.
 */
export function sampleAssistantMessage(id: string): AssistantMessage {
  return {
    id,
    role: "assistant",
    created_at: SEED_TIME,
    status: "complete",
    error_code: null,
    refused: false,
    feedback: null,
    answer: SAMPLE_SERVICE_ANSWER,
    sources: SAMPLE_SOURCES,
    office: SAMPLE_OFFICE,
  };
}

/**
 * Initial state: a verified, onboarded user with one past conversation, plus a Google-only account.
 *
 * @returns The seed state.
 */
function seed(): MockState {
  const region = SAMPLE_REGIONS[0] ?? null;
  const district = SAMPLE_DISTRICTS[1726]?.[0] ?? null;
  const user: Me = { ...newUser(SEED_EMAIL, true), region, district, profile_complete: true };
  const conversationId = "c0000000-0000-4000-8000-000000000001";
  return {
    users: {
      [SEED_EMAIL]: user,
      [GOOGLE_ONLY_EMAIL]: {
        ...newUser(GOOGLE_ONLY_EMAIL, true),
        has_password: false,
        region,
        district,
        profile_complete: true,
      },
    },
    sessionEmail: null,
    pendingEmail: null,
    verificationKeys: {},
    resetKeys: {},
    lastResendAt: null,
    conversations: {
      [conversationId]: {
        id: conversationId,
        owner: SEED_EMAIL,
        title: "Pasportni almashtirish",
        created_at: SEED_TIME,
        updated_at: SEED_TIME,
        messages: [
          {
            id: "u0000000-0000-4000-8000-000000000001",
            role: "user",
            text: "Pasportimni qanday yangilayman?",
            created_at: SEED_TIME,
          },
          sampleAssistantMessage("a0000000-0000-4000-8000-000000000001"),
        ],
      },
    },
  };
}

/**
 * Whether to mirror state to sessionStorage (browser mock mode, never in tests).
 *
 * @returns `true` in the browser outside Vitest.
 */
function persists(): boolean {
  return import.meta.env.MODE !== "test" && typeof sessionStorage !== "undefined";
}

/**
 * Load the mirrored state, else the seed.
 *
 * @returns The state.
 */
function load(): MockState {
  if (!persists()) return seed();
  const stored = sessionStorage.getItem(STORAGE_KEY);
  return stored ? (JSON.parse(stored) as MockState) : seed();
}

/** The live mock state. */
export let db: MockState = load();

/**
 * Persist the state after a change.
 */
export function saveDb(): void {
  if (persists()) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}

/**
 * Back to the seed (tests call this before each case).
 */
export function resetMockDb(): void {
  db = seed();
  saveDb();
}

/**
 * The signed-in mock user.
 *
 * @returns The user, or `null` without a session.
 */
export function currentUser(): Me | null {
  return db.sessionEmail ? (db.users[db.sessionEmail] ?? null) : null;
}
