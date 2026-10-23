import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LogoMark } from "./LogoMark";

/**
 * The id of an SVG's own gradient.
 *
 * @param svg A rendered mark.
 * @returns The gradient id ("" when missing).
 */
function gradientOf(svg: Element | undefined): string {
  return svg?.querySelector("linearGradient")?.id ?? "";
}

/** LogoMark: decorative next to the wordmark, labelled alone, unique ids per instance. */
describe("LogoMark", () => {
  it("is hidden from assistive tech without a label", () => {
    const { container } = render(<LogoMark />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).not.toHaveAttribute("role");
  });

  it("is a named image with a label", () => {
    const { getByRole } = render(<LogoMark label="GovAssist" />);
    expect(getByRole("img", { name: "GovAssist" })).toBeInTheDocument();
  });

  it("gives every instance its own gradient and mask, and takes the stops from the tokens", () => {
    const { container } = render(
      <>
        <LogoMark />
        <LogoMark />
      </>,
    );
    const ids = [...container.querySelectorAll("linearGradient, mask")].map((node) => node.id);
    expect(new Set(ids).size).toBe(4);
    const [first, second] = [...container.querySelectorAll("svg")];
    expect(first?.querySelector("g")).toHaveAttribute("stroke", `url(#${gradientOf(first)})`);
    expect(second?.querySelector("g")).toHaveAttribute("stroke", `url(#${gradientOf(second)})`);
    expect(container.querySelectorAll(".logo-mark__start, .logo-mark__end")).toHaveLength(4);
  });
});
