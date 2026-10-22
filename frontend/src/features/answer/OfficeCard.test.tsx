import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { OfficeMatch } from "../../api/types";
import { SAMPLE_OFFICE } from "../../mocks/fixtures";
import { OfficeCard } from "./OfficeCard";

/** Thursday 10:15 in Tashkent. */
const THURSDAY_MORNING = new Date("2026-10-22T10:15:00+05:00");

/** OfficeCard variants and links. */
describe("OfficeCard", () => {
  it("shows the district office with hours, phone and safe external links", () => {
    render(<OfficeCard match={SAMPLE_OFFICE} now={THURSDAY_MORNING} />);
    expect(screen.getByText("Hozir ochiq · tushlik 13:00 da")).toBeInTheDocument();
    expect(screen.getByText(/Du–Ju 09:00–18:00/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "+998 71 000 00 00" })).toHaveAttribute(
      "href",
      "tel:+998710000000",
    );
    const map = screen.getByRole("link", { name: "Google Xaritada ochish" });
    expect(map).toHaveAttribute("target", "_blank");
    expect(map).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.queryByText(/boshqa idora/)).not.toBeInTheDocument();
  });

  it("explains a region fallback", () => {
    render(<OfficeCard match={{ ...SAMPLE_OFFICE, match: "region" }} now={THURSDAY_MORNING} />);
    expect(screen.getByText(/Toshkent shahri dagi shu turdagi boshqa idora/)).toBeInTheDocument();
  });

  it("says when no office is known", () => {
    const none: OfficeMatch = { match: "none", office_type: SAMPLE_OFFICE.office_type, office: null };
    render(<OfficeCard match={none} />);
    expect(screen.getByText(/Davlat xizmatlari markazi manzili hali bizda yoʻq/)).toBeInTheDocument();
  });
});
