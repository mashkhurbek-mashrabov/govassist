import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { OfficeMatch } from "../../api/types";
import { SAMPLE_OFFICE } from "../../mocks/fixtures";
import { OfficeCard } from "./OfficeCard";

/**
 * A Tashkent wall-clock moment (UTC+5, no DST).
 *
 * @param date `2026-10-22` is a Thursday.
 * @param time `HH:MM`.
 * @returns The instant.
 */
function tashkent(date: string, time: string): Date {
  return new Date(`${date}T${time}:00+05:00`);
}

/** OfficeCard variants, badge rules and links (components.md → OfficeCard). */
describe("OfficeCard", () => {
  it("shows the district office: badge, address, hours table, phone and map", async () => {
    const user = userEvent.setup();
    render(<OfficeCard match={SAMPLE_OFFICE} now={tashkent("2026-10-22", "10:15")} />);
    expect(screen.getByRole("heading", { name: "Qayerga borish kerak" })).toBeInTheDocument();
    expect(screen.getByText("Hozir ochiq · 18:00 gacha")).toBeInTheDocument();
    expect(screen.getByText("NAMUNA koʻchasi, 1-uy, Chilonzor tumani, Toshkent shahri")).toBeInTheDocument();
    await user.click(screen.getByText("Ish vaqti", { selector: "summary span" }));
    expect(screen.getByRole("rowheader", { name: "Dushanba – Juma" }).closest("tr")).toHaveClass("is-today");
    expect(screen.getByText("Tushlik tanaffusi: 13:00 – 14:00")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: "Yakshanba Dam olish kuni" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /\+998 71 000 00 00/ })).toHaveAttribute(
      "href",
      "tel:+998710000000",
    );
    const map = screen.getByRole("link", { name: /Google Xaritada ochish/ });
    expect(map).toHaveAttribute("rel", "noopener noreferrer");
    expect(map).toHaveAccessibleName(/yangi oynada ochiladi/);
    expect(screen.getByText("Maʼlumot 20.10.2026 holatiga")).toBeInTheDocument();
  });

  it.each([
    ["13:30", "Tushlik tanaffusi · 14:00 da ochiladi"],
    ["07:30", "Yopiq · 09:00 da ochiladi"],
  ])("badge at %s → %s", (time, badge) => {
    render(<OfficeCard match={SAMPLE_OFFICE} now={tashkent("2026-10-22", time)} />);
    expect(screen.getByText(badge)).toBeInTheDocument();
  });

  it("names the next opening day after closing", () => {
    render(<OfficeCard match={SAMPLE_OFFICE} now={tashkent("2026-10-24", "15:00")} />);
    expect(screen.getByText("Yopiq · Dushanba 09:00 da ochiladi")).toBeInTheDocument();
  });

  it("warns about a region fallback", () => {
    render(
      <OfficeCard match={{ ...SAMPLE_OFFICE, match: "region" }} now={tashkent("2026-10-22", "10:00")} />,
    );
    expect(screen.getByText(/hududingizdagi boshqa idora koʻrsatildi/)).toBeInTheDocument();
  });

  it("handles unknown hours and phone", () => {
    const office = {
      ...(SAMPLE_OFFICE.office as NonNullable<OfficeMatch["office"]>),
      working_hours: [],
      phone: null,
    };
    render(<OfficeCard match={{ ...SAMPLE_OFFICE, office }} />);
    expect(screen.getByText("Ish vaqti nomaʼlum")).toBeInTheDocument();
    expect(screen.getByText("Telefon raqami nomaʼlum")).toBeInTheDocument();
    expect(screen.queryByText("Ish vaqti", { selector: "summary span" })).not.toBeInTheDocument();
  });

  it("says when no office is known for the type", () => {
    const none: OfficeMatch = { match: "none", office_type: SAMPLE_OFFICE.office_type, office: null };
    render(<OfficeCard match={none} />);
    expect(screen.getByText("Bu idora manzili hozircha bazamizda yoʻq.")).toBeInTheDocument();
    expect(screen.getByText("Kerakli idora: Davlat xizmatlari markazi.")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
