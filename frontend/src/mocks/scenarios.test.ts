import { describe, expect, it } from "vitest";
import { SAMPLE_SOURCES } from "./fixtures";
import { earlierSources, scenarioFor, sourcesAnswer, sourcesRequestLanguage } from "./scenarios";

/** Mock routing: greetings in each language get a smalltalk answer (contract v1.10). */
describe("scenarioFor", () => {
  it.each([
    ["Salom", "uz-Latn"],
    ["Привет!", "ru"],
    ["Hello", "en"],
  ])("answers %s with smalltalk in %s", (text, language) => {
    const scenario = scenarioFor(text);
    expect(scenario.answer).toMatchObject({ answer_type: "smalltalk", language });
    expect(scenario.answer.follow_up_questions.length).toBeGreaterThanOrEqual(2);
    expect(scenario.sources).toEqual([]);
    expect(scenario.office).toBeNull();
  });

  it("does not take a service question for a greeting", () => {
    expect(scenarioFor("Pasportimni qanday yangilayman?").answer.answer_type).toBe("service");
    expect(scenarioFor("history of passports").answer.answer_type).toBe("service");
  });
});

/** "List the sources" (contract v1.11): detection, the answer, and the earlier citations. */
describe("sources requests", () => {
  it.each([
    ["Manbalarni koʻrsating", "uz-Latn"],
    ["Покажи источники", "ru"],
    ["List the sources", "en"],
  ])("recognises %s as %s", (text, language) => {
    expect(sourcesRequestLanguage(text)).toBe(language);
  });

  it("ignores ordinary questions", () => {
    expect(sourcesRequestLanguage("Pasportimni qanday yangilayman?")).toBeNull();
  });

  it("builds a sources answer with every other field empty", () => {
    expect(sourcesAnswer("en", 0)).toMatchObject({
      answer_type: "sources",
      language: "en",
      steps: [],
      documents: [],
      fee: null,
      processing_time: null,
      law_points: [],
      follow_up_questions: [],
      summary: "NAMUNA: Nothing has been cited in this conversation yet.",
    });
  });

  it("dedupes earlier citations by URL, in order of first citation, relabelled S1..Sn", () => {
    const [first, second] = SAMPLE_SOURCES;
    if (!first || !second) throw new Error("SAMPLE_SOURCES needs two sources");
    const messages = [
      { role: "user" },
      { role: "assistant", sources: [{ ...second, id: "S1" }] },
      {
        role: "assistant",
        sources: [
          { ...first, id: "S1" },
          { ...second, id: "S2" },
        ],
      },
    ];
    expect(earlierSources(messages).map(({ id, url }) => `${id} ${url}`)).toEqual([
      `S1 ${second.url}`,
      `S2 ${first.url}`,
    ]);
  });
});
