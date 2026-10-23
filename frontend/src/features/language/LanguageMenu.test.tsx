import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { db, SEED_EMAIL } from "../../mocks/db";
import { renderApp, signInSeedUser } from "../../test/render";

/**
 * The header language button of the auth layout.
 *
 * @returns The menu button.
 */
async function menuButton(): Promise<HTMLElement> {
  return screen.findByRole("button", { name: /Tilni tanlash/ });
}

/** LanguageMenu: menu-button pattern, in-place switch, persistence. */
describe("LanguageMenu", () => {
  it("exposes the menu button and its checked items", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    const button = await menuButton();
    expect(button).toHaveAttribute("aria-haspopup", "menu");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).toHaveTextContent("UZ");
    await user.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    const menu = screen.getByRole("menu");
    const items = within(menu).getAllByRole("menuitemradio");
    expect(items.map((item) => item.textContent)).toEqual([
      "OʻzbekchaLotin yozuviUZ",
      "ЎзбекчаКирилл ёзувиЎЗ",
      "РусскийRU",
      "EnglishEN",
    ]);
    expect(items[0]).toHaveAttribute("aria-checked", "true");
    expect(items[0]).toHaveFocus();
  });

  it("works from the keyboard and returns focus to the button", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    const button = await menuButton();
    button.focus();
    await user.keyboard("{ArrowDown}");
    const items = within(screen.getByRole("menu")).getAllByRole("menuitemradio");
    expect(items[0]).toHaveFocus();
    await user.keyboard("{ArrowDown}");
    expect(items[1]).toHaveFocus();
    await user.keyboard("{End}");
    expect(items[3]).toHaveFocus();
    await user.keyboard("{ArrowDown}");
    expect(items[0]).toHaveFocus();
    await user.keyboard("{Home}{ArrowUp}");
    expect(items[3]).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).toHaveFocus();
  });

  it("switches the page in place, announces it and remembers it before login", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    const button = await menuButton();
    await user.click(button);
    await user.click(screen.getByRole("menuitemradio", { name: /Русский/ }));
    expect(await screen.findByRole("heading", { name: "Вход в аккаунт" })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("ru");
    expect(localStorage.getItem("govassist.lang")).toBe("ru");
    expect(await screen.findByText("Язык изменён")).toBeInTheDocument();
    const switched = screen.getByRole("button", { name: /Выбрать язык/ });
    expect(switched).toHaveTextContent("RU");
    expect(switched).toHaveFocus();
  });

  it("saves the choice with PATCH /me when signed in", async () => {
    signInSeedUser();
    const user = userEvent.setup();
    renderApp("/settings");
    const sidebar = await screen.findByRole("complementary");
    await user.click(within(sidebar).getByRole("button", { name: /Tilni tanlash/ }));
    await user.click(screen.getByRole("menuitemradio", { name: /English/ }));
    expect(await screen.findByRole("heading", { name: "Settings", level: 1 })).toBeInTheDocument();
    await waitFor(() => expect(db.users[SEED_EMAIL]?.ui_language).toBe("en"));
  });

  it("closes on an outside press without stealing focus", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    const button = await menuButton();
    await user.click(button);
    await user.click(screen.getByRole("heading", { level: 1 }));
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });
});
