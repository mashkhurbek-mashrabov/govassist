import { describe, expect, it } from "vitest";
import type { Message } from "../../api/types";
import { sampleAssistantMessage } from "../../mocks/db";
import { turnReducer, type LiveTurn } from "./useChatStream";
import { visibleMessages } from "./visibleMessages";

const user: Message = { id: "u1", role: "user", text: "Q", created_at: "2026-10-22T09:00:00Z" };
const assistant = sampleAssistantMessage("a1");

/**
 * A live turn that got its ids.
 *
 * @param overrides Fields to change.
 * @returns The turn.
 */
function turn(overrides: Partial<LiveTurn> = {}): LiveTurn {
  const started = turnReducer(null, { type: "start", text: "Q", conversationId: null });
  const withMeta = turnReducer(started, {
    type: "meta",
    data: { conversation_id: "c", user_message_id: "u1", assistant_message_id: "a1" },
  });
  if (!withMeta) throw new Error("turn missing");
  return { ...withMeta, ...overrides };
}

/** Stored messages and the live turn never show the same exchange twice. */
describe("visibleMessages", () => {
  it("shows stored messages only without a turn", () => {
    expect(visibleMessages([user, assistant], null)).toEqual({
      messages: [user, assistant],
      showTurn: false,
    });
  });

  it("hides stored copies while the turn is live", () => {
    expect(visibleMessages([user, assistant], turn())).toEqual({ messages: [], showTurn: true });
  });

  it("yields to the stored copy once a clean turn is fetched", () => {
    const done = turn({ isStreaming: false, finalMessage: assistant });
    expect(visibleMessages([user, assistant], done)).toEqual({
      messages: [user, assistant],
      showTurn: false,
    });
  });

  it("keeps a failed turn (with Retry) over the stored copy", () => {
    const failed = turn({ isStreaming: false, failure: { kind: "stopped" } });
    expect(visibleMessages([user, assistant], failed).showTurn).toBe(true);
  });

  it("keeps a finished turn until the refetch includes it", () => {
    const done = turn({ isStreaming: false, finalMessage: assistant });
    expect(visibleMessages([], done)).toEqual({ messages: [], showTurn: true });
  });
});
