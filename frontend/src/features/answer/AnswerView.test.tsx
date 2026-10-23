import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Answer, OfficeMatch } from "../../api/types";
import {
  SAMPLE_OFF_TOPIC_ANSWER,
  SAMPLE_OFFICE,
  SAMPLE_SERVICE_ANSWER,
  SAMPLE_SOURCES,
} from "../../mocks/fixtures";
import { AnswerView } from "./AnswerView";
import { queryWrapper, testQueryClient } from "../../test/render";
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

/**
 * An answer still streaming, with or without its early office.
 *
 * @param answer The partial answer so far.
 * @param office The early office, or `null` once withdrawn.
 * @returns The element to render.
 */
function streamingView(answer: PartialAnswer, office: OfficeMatch | null) {
  return <AnswerView answer={answer} sources={[]} office={office} messageId="m" streaming complete={false} />;
}

/** AnswerView: schema order per type, citations, streaming skeletons, plain text. */
describe("AnswerView", () => {
  afterEach(() => vi.unstubAllGlobals());

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

  it("animates a withdrawn early office card out when the answer turns out refused (contract v1.7)", () => {
    const { rerender } = render(streamingView({}, SAMPLE_OFFICE), {
      wrapper: queryWrapper(testQueryClient()),
    });
    expect(screen.getByRole("heading", { name: "Qayerga borish kerak" })).toBeInTheDocument();
    rerender(streamingView({ answer_type: "off_topic" }, SAMPLE_OFFICE));
    const leaving = screen.getByText("Qayerga borish kerak", { selector: "h3" }).closest(".office-leave");
    expect(leaving).toHaveAttribute("inert");
    // jsdom has no AnimationEvent, so React listens for the prefixed event there (browsers use `animationend`).
    fireEvent(leaving as Element, new Event("webkitAnimationEnd", { bubbles: true }));
    expect(screen.queryByText("Qayerga borish kerak")).not.toBeInTheDocument();
  });

  it("removes a withdrawn office card at once under reduced motion", () => {
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: query.includes("reduce") }));
    const { rerender } = render(streamingView({}, SAMPLE_OFFICE));
    rerender(streamingView({}, null));
    expect(screen.queryByText("Qayerga borish kerak")).not.toBeInTheDocument();
  });

  it("never shows an office on a stored refused answer", () => {
    render(
      <AnswerView
        answer={SAMPLE_OFF_TOPIC_ANSWER}
        sources={[]}
        office={SAMPLE_OFFICE}
        messageId="m"
        streaming={false}
        complete
      />,
      { wrapper: queryWrapper(testQueryClient()) },
    );
    expect(screen.queryByText("Qayerga borish kerak")).not.toBeInTheDocument();
  });

  it("renders smalltalk as a friendly card: chips, no hint, sources or disclaimer (contract v1.10)", () => {
    const onAsk = vi.fn();
    const smalltalk: Answer = {
      ...SAMPLE_OFF_TOPIC_ANSWER,
      answer_type: "smalltalk",
      title: "NAMUNA: Salom!",
      summary: "NAMUNA: Men GovAssist.",
      follow_up_questions: ["Pasportimni qanday yangilayman?", "NAMUNA savol"],
    };
    render(
      <AnswerView
        answer={smalltalk}
        sources={[]}
        office={null}
        messageId="m"
        streaming={false}
        complete
        onAsk={onAsk}
      />,
      { wrapper: queryWrapper(testQueryClient()) },
    );
    expect(screen.getByRole("heading", { level: 2, name: "NAMUNA: Salom!" })).toBeInTheDocument();
    expect(screen.getByText("NAMUNA: Men GovAssist.")).toBeInTheDocument();
    expect(screen.queryByText(/boshqa soʻzlar bilan/)).not.toBeInTheDocument();
    expect(screen.queryByText(/davlat xizmatlari va Oʻzbekiston qonunlari/)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Manbalar" })).not.toBeInTheDocument();
    expect(screen.queryByText(/yuridik maslahat emas/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Pasportimni qanday yangilayman?" }));
    expect(onAsk).toHaveBeenCalledWith("Pasportimni qanday yangilayman?");
  });

  it("withdraws the early office when the answer turns out to be smalltalk", () => {
    const { rerender } = render(streamingView({}, SAMPLE_OFFICE), {
      wrapper: queryWrapper(testQueryClient()),
    });
    expect(screen.getByRole("heading", { name: "Qayerga borish kerak" })).toBeInTheDocument();
    rerender(streamingView({ answer_type: "smalltalk" }, SAMPLE_OFFICE));
    expect(
      screen.getByText("Qayerga borish kerak", { selector: "h3" }).closest(".office-leave"),
    ).toHaveAttribute("inert");
  });

  it("renders a sources answer: badge, title, summary and the earlier citations (contract v1.11)", () => {
    const answer: Answer = {
      ...SAMPLE_OFF_TOPIC_ANSWER,
      answer_type: "sources",
      title: "NAMUNA: Ushbu suhbat manbalari",
      summary: "NAMUNA: manbalar quyida.",
      follow_up_questions: [],
    };
    render(
      <AnswerView
        answer={answer}
        sources={SAMPLE_SOURCES}
        office={null}
        messageId="m"
        streaming={false}
        complete
      />,
      { wrapper: queryWrapper(testQueryClient()) },
    );
    expect(document.querySelector(".answer-head__kind")).toHaveTextContent("Manbalar");
    expect(
      screen.getByRole("heading", { level: 2, name: "NAMUNA: Ushbu suhbat manbalari" }),
    ).toBeInTheDocument();
    expect(screen.getByText("NAMUNA: manbalar quyida.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /NAMUNA xizmat sahifasi/ })).toHaveAttribute(
      "href",
      "https://my.gov.uz/",
    );
    expect(screen.getByRole("link", { name: /NAMUNA nizom/ })).toBeInTheDocument();
    expect(screen.queryByText(/yuridik maslahat emas/)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Qayerga borish kerak" })).not.toBeInTheDocument();
  });

  it("shows only the summary when nothing was cited yet", () => {
    const answer: Answer = {
      ...SAMPLE_OFF_TOPIC_ANSWER,
      answer_type: "sources",
      title: "NAMUNA: Ushbu suhbat manbalari",
      summary: "NAMUNA: hali manba yoʻq.",
      follow_up_questions: [],
    };
    render(
      <AnswerView answer={answer} sources={[]} office={null} messageId="m" streaming={false} complete />,
      {
        wrapper: queryWrapper(testQueryClient()),
      },
    );
    expect(screen.getByText("NAMUNA: hali manba yoʻq.")).toBeInTheDocument();
    expect(screen.queryAllByRole("link")).toHaveLength(0);
    expect(screen.getAllByRole("heading").map((heading) => heading.textContent)).toEqual([
      "NAMUNA: Ushbu suhbat manbalari",
    ]);
  });

  it("withdraws the early office when the answer turns out to be a sources list", () => {
    const { rerender } = render(streamingView({}, SAMPLE_OFFICE), {
      wrapper: queryWrapper(testQueryClient()),
    });
    rerender(streamingView({ answer_type: "sources" }, SAMPLE_OFFICE));
    expect(
      screen.getByText("Qayerga borish kerak", { selector: "h3" }).closest(".office-leave"),
    ).toHaveAttribute("inert");
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
