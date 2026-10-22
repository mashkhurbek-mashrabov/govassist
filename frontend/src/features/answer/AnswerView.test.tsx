import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Answer } from "../../api/types";
import {
  SAMPLE_OFF_TOPIC_ANSWER,
  SAMPLE_OFFICE,
  SAMPLE_SERVICE_ANSWER,
  SAMPLE_SOURCES,
} from "../../mocks/fixtures";
import { AnswerView } from "./AnswerView";

/** A legal answer for ordering checks (sample values). */
const LEGAL: Answer = {
  ...SAMPLE_SERVICE_ANSWER,
  answer_type: "legal",
  documents: [],
  fee: null,
  processing_time: null,
  law_points: [{ quote: "NAMUNA band matni", explanation: "NAMUNA izoh", source_ids: ["S2"] }],
};

/** AnswerView renders schema order, citations and plain text. */
describe("AnswerView", () => {
  it("renders a service answer with numbered citations, office and sources", () => {
    render(
      <AnswerView
        answer={SAMPLE_SERVICE_ANSWER}
        sources={SAMPLE_SOURCES}
        office={SAMPLE_OFFICE}
        messageId="m"
        streaming={false}
        onAsk={() => undefined}
      />,
    );
    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    expect(headings).toEqual([
      "Pasportni almashtirish",
      "Qadamlar",
      "Kerakli hujjatlar",
      "NAMUNA Chilonzor tumani Davlat xizmatlari markazi",
      "Manbalar",
      "Yana soʻrashingiz mumkin",
    ]);
    const steps = within(
      screen.getByRole("heading", { name: "Qadamlar" }).closest("section") ?? document.body,
    );
    expect(steps.getAllByRole("link", { name: "1-manba" })).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: "2-manba" })[0]).toHaveAttribute("href", "#source-m-S2");
    expect(screen.getByRole("link", { name: "NAMUNA nizom" })).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("shows no badges while sources are unknown (streaming)", () => {
    render(
      <AnswerView
        answer={{ answer_type: "service", title: "T" }}
        sources={[]}
        office={null}
        messageId="m"
        streaming
      />,
    );
    expect(screen.queryByRole("link", { name: /manba/ })).not.toBeInTheDocument();
  });

  it("puts law points before steps for legal answers and has no office", () => {
    render(
      <AnswerView
        answer={LEGAL}
        sources={SAMPLE_SOURCES}
        office={SAMPLE_OFFICE}
        messageId="m"
        streaming={false}
      />,
    );
    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    expect(headings.slice(0, 3)).toEqual([
      "Pasportni almashtirish",
      "Qonunda nima deyilgan",
      "Nima qilishingiz mumkin",
    ]);
    expect(screen.queryByRole("region", { name: "Idora" })).not.toBeInTheDocument();
  });

  it("renders off-topic answers as summary + follow-ups only, as plain text", () => {
    const hostile = { ...SAMPLE_OFF_TOPIC_ANSWER, summary: "<img src=x onerror=alert(1)>" };
    render(
      <AnswerView
        answer={hostile}
        sources={[]}
        office={null}
        messageId="m"
        streaming={false}
        onAsk={() => undefined}
      />,
    );
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(screen.queryByText(/yuridik maslahat emas/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pasportimni qanday yangilayman?" })).toBeEnabled();
  });
});
