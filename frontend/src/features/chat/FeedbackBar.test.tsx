import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { db } from "../../mocks/db";
import { signInSeedUser, testQueryClient } from "../../test/render";
import { FeedbackBar } from "./FeedbackBar";

const CONVERSATION_ID = "c0000000-0000-4000-8000-000000000001";

/**
 * The seeded assistant message.
 *
 * @returns The message.
 */
function seededAnswer() {
  const message = db.conversations[CONVERSATION_ID]?.messages[1];
  if (message?.role !== "assistant") throw new Error("seed changed");
  return message;
}

/** Feedback upsert and saved state. */
describe("FeedbackBar", () => {
  beforeEach(signInSeedUser);

  it("saves a rating, then a comment, and shows the saved state", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={testQueryClient()}>
        <FeedbackBar conversationId={CONVERSATION_ID} message={seededAnswer()} />
      </QueryClientProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Foydali emas" }));
    expect(await screen.findByText("Rahmat, fikringiz saqlandi.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Foydali emas" })).toHaveAttribute("aria-pressed", "true");
    expect(seededAnswer().feedback).toEqual({ rating: -1, comment: "" });

    await user.type(screen.getByLabelText("Izoh (ixtiyoriy)"), "NAMUNA izoh");
    await user.click(screen.getByRole("button", { name: "Izohni yuborish" }));
    await screen.findByText("Rahmat, fikringiz saqlandi.");
    expect(seededAnswer().feedback).toEqual({ rating: -1, comment: "NAMUNA izoh" });
  });
});
