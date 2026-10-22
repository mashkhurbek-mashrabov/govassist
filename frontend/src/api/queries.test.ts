import { describe, expect, it } from "vitest";
import { sampleAssistantMessage } from "../mocks/db";
import { testQueryClient } from "../test/render";
import { queryKeys, storeFinalAnswer } from "./queries";
import type { Conversation, Message } from "./types";

/** Conversation id used by the cache tests. */
const ID = "c-1";
/** The question that was asked. */
const QUESTION = { id: "u-1", text: "NAMUNA savol" };

/**
 * A cached conversation.
 *
 * @param messages Its messages.
 * @returns The conversation.
 */
function conversation(messages: Message[]): Conversation {
  return {
    id: ID,
    title: "NAMUNA",
    created_at: "2026-10-22T09:00:00Z",
    updated_at: "2026-10-22T09:00:00Z",
    messages,
  };
}

/** storeFinalAnswer(): the finished answer lands in the cache before the refetch. */
describe("storeFinalAnswer", () => {
  const answer = sampleAssistantMessage("a-1");

  it("replaces the copy fetched mid-stream", () => {
    const client = testQueryClient();
    const midStream = { ...answer, status: "streaming" as const, answer: null };
    const asked = {
      id: QUESTION.id,
      role: "user" as const,
      text: QUESTION.text,
      created_at: answer.created_at,
    };
    client.setQueryData(queryKeys.conversation(ID), conversation([asked, midStream]));
    storeFinalAnswer(client, ID, QUESTION, answer);
    expect(client.getQueryData<Conversation>(queryKeys.conversation(ID))?.messages).toEqual([asked, answer]);
  });

  it("appends the question and the answer when the cache predates them", () => {
    const client = testQueryClient();
    client.setQueryData(queryKeys.conversation(ID), conversation([]));
    storeFinalAnswer(client, ID, QUESTION, answer);
    expect(client.getQueryData<Conversation>(queryKeys.conversation(ID))?.messages).toEqual([
      { id: QUESTION.id, role: "user", text: QUESTION.text, created_at: answer.created_at },
      answer,
    ]);
  });

  it("leaves an uncached conversation alone", () => {
    const client = testQueryClient();
    storeFinalAnswer(client, ID, QUESTION, answer);
    expect(client.getQueryData(queryKeys.conversation(ID))).toBeUndefined();
  });
});
