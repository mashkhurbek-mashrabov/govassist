import { act, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp } from "../../test/render";
import { LandingPreview } from "./LandingPreview";

/** Callback the stubbed IntersectionObserver was created with. */
let reportIntersection: ((entries: { isIntersecting: boolean }[]) => void) | null = null;

/** A minimal IntersectionObserver that the test drives by hand. */
class FakeIntersectionObserver {
  /**
   * @param callback Called with the visibility entries.
   */
  constructor(callback: (entries: { isIntersecting: boolean }[]) => void) {
    reportIntersection = callback;
  }

  /** Start observing (no-op). */
  observe(): void {}

  /** Stop observing (no-op). */
  disconnect(): void {}
}

/** The landing preview plays only while it is visible. */
describe("LandingPreview", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    reportIntersection = null;
  });

  it("plays only while on screen", () => {
    vi.stubGlobal("IntersectionObserver", FakeIntersectionObserver);
    render(<LandingPreview />);
    const figure = screen.getByRole("figure", { name: "Javob namunasi · NAMUNA" });
    expect(figure).not.toHaveAttribute("data-playing");
    act(() => reportIntersection?.([{ isIntersecting: true }]));
    expect(figure).toHaveAttribute("data-playing");
    act(() => reportIntersection?.([{ isIntersecting: false }]));
    expect(figure).not.toHaveAttribute("data-playing");
  });

  it("shows the sample answer as data with decorative citation badges", () => {
    render(<LandingPreview />);
    const figure = screen.getByRole("figure");
    expect(within(figure).getByText("Pasportimni qanday yangilayman?")).toHaveAttribute("lang", "uz-Latn");
    expect(within(figure).getAllByRole("listitem")).toHaveLength(3);
    expect(within(figure).queryAllByRole("link")).toHaveLength(0);
  });
});

/** The v1.2 landing structure (screens.md → 0. Landing). */
describe("WelcomePage", () => {
  it("has the hero, features, how it works, FAQ and CTA band", async () => {
    renderApp("/welcome");
    expect(
      await screen.findByRole("heading", { level: 1, name: "Qaysi hujjat, qaysi idora — aniq javob." }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Qanday ishlashini koʻrish" })).toHaveAttribute(
      "href",
      "#landing-how",
    );
    expect(screen.getByRole("region", { name: "Qanday ishlaydi" })).toHaveAttribute("id", "landing-how");
    const features = screen.getByRole("region", { name: "Nega GovAssist" });
    expect(within(features).getAllByRole("heading", { level: 3 })).toHaveLength(4);
    expect(
      within(features).getByText("Manzil, ish vaqti va xaritadagi joyi — har bir javobda."),
    ).toBeVisible();
    expect(within(features).getByText("lex.uz")).toBeInTheDocument();
    const faq = screen.getByRole("region", { name: "Koʻp soʻraladigan savollar" });
    expect(faq.querySelectorAll("details")).toHaveLength(4);
    expect(screen.getAllByRole("link", { name: "Roʻyxatdan oʻtish" })).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: /Tilni tanlash/ })).toHaveLength(2);
    expect(screen.getByText("Rasmiy davlat xizmati emas")).toBeInTheDocument();
  });
});
