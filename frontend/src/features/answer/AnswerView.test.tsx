import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Answer } from "../../api/types";
import {
  SAMPLE_OFF_TOPIC_ANSWER,
  SAMPLE_OFFICE,
  SAMPLE_SERVICE_ANSWER,
  SAMPLE_SOURCES,
} from "../../mocks/fixtures";
import { AnswerView } from "./AnswerView";
import { testQueryClient } from "../../test/render";
import type { PartialAnswer } from "./answerTypes";
import { nextSkeleton } from "./skeleton";

/** A legal answer (sample values). */
const LEGAL: Answer = {
  ...SAMPLE_SERVICE_ANSWER,
  answer_type: "legal",
  documents: [],
  fee: null,
  processing_time: null,
  law_points: [
    { quote: "NAMUNA band", explanation: "NAMUNA izoh", source_ids: ["S2"] },
    { quote: "NAMUNA band 2", explanation: "NAMUNA izoh 2", source_ids: [] },
  ],
};

/**
 * Headings in document order.
 *
 * @returns Their text.
 */
function headings(): (string | null)[] {
  return screen.getAllByRole("heading").map((heading) => heading.textContent);
}

/** AnswerView: schema order per type, citations, streaming skeletons, plain text. */
describe("AnswerView", () => {
  it("renders a complete service answer in schema order with numbered citations", () => {
    render(
      <AnswerView
        answer={SAMPLE_SERVICE_ANSWER}
        sources={SAMPLE_SOURCES}
        office={SAMPLE_OFFICE}
        messageId="m"
        streaming={false}
        complete
        onAsk={() => undefined}
      />,
    );
    expect(headings()).toEqual([
      "Pasportni almashtirish",
      "Nima qilish kerak",
      "Oʻzingiz bilan oling",
      "Toʻlov",
      "Muddat",
      "Qayerga borish kerak",
      "Manbalar",
      "Yana soʻrashingiz mumkin",
    ]);
    expect(screen.getAllByRole("link", { name: "2-manba" })[0]).toHaveAttribute("href", "#source-m-S2");
    expect(screen.getByRole("button", { name: "Pasportni onlayn almashtirsa boʻladimi?" })).toBeEnabled();
  });

  it("puts law points before 'what you can do' for legal answers and shows no office", () => {
    render(
      <AnswerView
        answer={LEGAL}
        sources={SAMPLE_SOURCES}
        office={SAMPLE_OFFICE}
        messageId="m"
        streaming={false}
        complete
      />,
    );
    expect(headings().slice(0, 3)).toEqual([
      "Pasportni almashtirish",
      "Qonunda nima deyilgan",
      "Nima qilishingiz mumkin",
    ]);
    expect(screen.getByText("Huquqiy savol")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Qayerga borish kerak" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "2-manba" })).toHaveLength(2);
  });

  it("while streaming: no badges, one skeleton block ahead, no final-only parts", () => {
    const partial = { answer_type: "service" as const, title: "T", summary: "S", steps: [{ text: "Bir" }] };
    const { container } = render(
      <AnswerView
        answer={partial}
        sources={[]}
        office={SAMPLE_OFFICE}
        messageId="m"
        streaming
        complete={false}
      />,
    );
    expect(screen.queryByRole("link", { name: /manba/ })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Oʻzingiz bilan oling" })).toBeInTheDocument();
    expect(container.querySelectorAll(".skeleton").length).toBeGreaterThan(0);
    expect(screen.queryByText(/yuridik maslahat emas/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Qayerga borish kerak" })).toBeInTheDocument();
  });

  it("keeps a stopped answer's cards without skeletons or extras", () => {
    const partial = { answer_type: "service" as const, title: "T", summary: "S", steps: [{ text: "Bir" }] };
    const { container } = render(
      <AnswerView
        answer={partial}
        sources={[]}
        office={null}
        messageId="m"
        streaming={false}
        complete={false}
      />,
    );
    expect(container.querySelectorAll(".skeleton")).toHaveLength(0);
    expect(screen.queryByText(/yuridik maslahat emas/)).not.toBeInTheDocument();
  });

  it("renders not-found/off-topic as one card, as plain text", () => {
    const hostile = { ...SAMPLE_OFF_TOPIC_ANSWER, summary: "<img src=x onerror=alert(1)>" };
    render(
      <QueryClientProvider client={testQueryClient()}>
        <AnswerView
          answer={hostile}
          sources={[]}
          office={null}
          messageId="m"
          streaming={false}
          complete
          onAsk={() => undefined}
        />
      </QueryClientProvider>,
    );
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(screen.getByText(/davlat xizmatlari va Oʻzbekiston qonunlari/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pasportimni qanday yangilayman?" })).toBeEnabled();
  });
});

/** nextSkeleton(): at most one block ahead of the text. */
describe("nextSkeleton", () => {
  it.each([
    [{ title: "T" }, true, null],
    [{ title: "T", summary: "S" }, true, "steps"],
    [{ summary: "S", steps: [] }, true, "documents"],
    [{ summary: "S", steps: [], documents: [] }, true, "facts"],
    [{ summary: "S", steps: [], documents: [], fee: null }, true, null],
    [{ summary: "S" }, false, null],
  ] as [PartialAnswer, boolean, string | null][])("%o streaming=%s → %s", (answer, streaming, expected) => {
    expect(nextSkeleton(answer, streaming)).toBe(expected);
  });
});
