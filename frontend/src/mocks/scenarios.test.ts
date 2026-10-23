import { describe, expect, it } from "vitest";
import { scenarioFor } from "./scenarios";

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
