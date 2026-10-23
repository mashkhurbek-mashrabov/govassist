import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { db, SEED_EMAIL } from "../../mocks/db";
import { renderApp, signInSeedUser } from "../../test/render";

/**
 * The account menu's avatar button.
 *
 * @returns The button.
 */
async function avatar(): Promise<HTMLElement> {
  return screen.findByRole("button", { name: "Hisob menyusi" });
}

/** AccountMenu: avatar initials, menu-button keyboard pattern, Settings and Log out. */
describe("AccountMenu", () => {
  it("shows the email's first letter without a name, and two initials with one", async () => {
    signInSeedUser();
    const seed = db.users[SEED_EMAIL];
    if (seed) seed.display_name = null;
    const { unmount } = renderApp("/");
    expect(await avatar()).toHaveTextContent("N");
    unmount();
    if (seed) seed.display_name = "Aziza Karimova";
    renderApp("/");
    expect(await avatar()).toHaveTextContent("AK");
  });

  it("opens from the keyboard, moves with arrows, closes on Esc with focus back", async () => {
    signInSeedUser();
    const user = userEvent.setup();
    renderApp("/");
    const button = await avatar();
    expect(button).toHaveAttribute("aria-haspopup", "menu");
    expect(button).toHaveAttribute("aria-expanded", "false");
    button.focus();
    await user.keyboard("{ArrowDown}");
    expect(button).toHaveAttribute("aria-expanded", "true");
    const menu = screen.getByRole("menu");
    expect(within(menu).getByText(SEED_EMAIL)).toHaveAttribute("title", SEED_EMAIL);
    const [settings, logout] = within(menu).getAllByRole("menuitem");
    expect(settings).toHaveFocus();
    await user.keyboard("{ArrowDown}");
    expect(logout).toHaveFocus();
    await user.keyboard("{ArrowDown}");
    expect(settings).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).toHaveFocus();
  });

  it("goes to Settings", async () => {
    signInSeedUser();
    const user = userEvent.setup();
    const { router } = renderApp("/");
    await user.click(await avatar());
    await user.click(screen.getByRole("menuitem", { name: "Sozlamalar" }));
    await screen.findByRole("heading", { level: 1, name: "Sozlamalar" });
    expect(router.state.location.pathname).toBe("/settings");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("logs out through the same flow as Settings, to the landing page", async () => {
    signInSeedUser();
    const user = userEvent.setup();
    const { router } = renderApp("/");
    await user.click(await avatar());
    await user.click(screen.getByRole("menuitem", { name: "Chiqish" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/welcome"));
    expect(db.sessionEmail).toBeNull();
  });
});
