import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import i18n from "../../i18n";
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

  it("shows the sample answer in the UI language, office as stored, badges decorative", async () => {
    render(<LandingPreview />);
    const figure = screen.getByRole("figure");
    expect(within(figure).getByText("Pasportimni qanday yangilayman?")).toBeInTheDocument();
    expect(within(figure).getAllByRole("listitem")).toHaveLength(3);
    expect(within(figure).queryAllByRole("link")).toHaveLength(0);
    await act(() => i18n.changeLanguage("ru"));
    expect(within(figure).getByText("Как заменить паспорт?")).toBeInTheDocument();
    expect(within(figure).getByText("Центр государственных услуг")).toBeInTheDocument();
    expect(within(figure).getByText("NAMUNA Chilonzor tumani Davlat xizmatlari markazi")).toHaveAttribute(
      "lang",
      "uz-Latn",
    );
  });
});

/** The v1.3 landing (screens.md → 0. Landing). */
describe("WelcomePage", () => {
  it("has the hero ask box, problem, comparison, services, how it works, FAQ and footer", async () => {
    renderApp("/welcome");
    expect(
      await screen.findByRole("heading", { level: 1, name: "Qaysi hujjat, qaysi idora — aniq javob." }),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /Savolingizni yozing/ })).toBeRequired();
    expect(screen.getByRole("link", { name: "ID kartani qanday olaman?" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Notoʻgʻri idora — yoʻqotilgan kun" })).toBeInTheDocument();
    const table = screen.getByRole("table", { name: "GovAssist va oddiy chatbot" });
    expect(
      within(table)
        .getAllByRole("columnheader")
        .map((cell) => cell.textContent),
    ).toEqual(["Nima", "Oddiy chatbot", "GovAssist"]);
    expect(within(table).getAllByRole("rowheader")).toHaveLength(5);
    const services = screen.getByRole("region", { name: "Ommabop xizmatlar" });
    expect(within(services).getAllByRole("link")).toHaveLength(8);
    expect(services).toHaveAttribute("id", "services");
    for (const id of ["how", "why", "faq"]) expect(document.getElementById(id)).not.toBeNull();
    const faq = screen.getByRole("region", { name: "Koʻp soʻraladigan savollar" });
    expect(faq.querySelectorAll("details")).toHaveLength(4);
    expect(screen.getByText("© 2026 GovAssist")).toBeInTheDocument();
    expect(screen.getByText("Rasmiy davlat xizmati emas")).toBeInTheDocument();
    expect(screen.queryByText(/dissertatsiyasi/)).not.toBeInTheDocument();
  });

  it("opens the hamburger panel, closes it on Esc with focus back, and on choosing a link", async () => {
    const user = userEvent.setup();
    renderApp("/welcome");
    const toggle = await screen.findByRole("button", { name: "Menyuni ochish" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const panel = document.getElementById(toggle.getAttribute("aria-controls") ?? "");
    expect(panel).not.toHaveAttribute("hidden");
    await user.keyboard("{Escape}");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveFocus();
    await user.click(toggle);
    await user.click(within(panel as HTMLElement).getByRole("link", { name: "Xizmatlar" }));
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  it("carries a typed question to sign-up in sessionStorage, never in the URL", async () => {
    const user = userEvent.setup();
    const { router } = renderApp("/welcome");
    await user.type(
      await screen.findByRole("textbox", { name: /Savolingizni yozing/ }),
      "NAMUNA savol matni",
    );
    await user.click(screen.getByRole("button", { name: "Soʻrash" }));
    await screen.findByRole("heading", { name: "Roʻyxatdan oʻting" });
    expect(router.state.location.pathname).toBe("/signup");
    expect(router.state.location.search).toBe("");
    expect(sessionStorage.getItem("govassist.pendingQuestion")).toBe("NAMUNA savol matni");
    expect(screen.getByText("Savolingiz saqlandi")).toBeInTheDocument();
    expect(screen.getByText("NAMUNA savol matni")).toBeInTheDocument();
  });

  it("carries a service tile's question", async () => {
    const user = userEvent.setup();
    renderApp("/welcome");
    const services = await screen.findByRole("region", { name: "Ommabop xizmatlar" });
    await user.click(within(services).getByRole("link", { name: /Pensiya/ }));
    await screen.findByRole("heading", { name: "Roʻyxatdan oʻting" });
    expect(sessionStorage.getItem("govassist.pendingQuestion")).toBe(
      "Pensiya tayinlash uchun qanday hujjatlar kerak?",
    );
  });
});
