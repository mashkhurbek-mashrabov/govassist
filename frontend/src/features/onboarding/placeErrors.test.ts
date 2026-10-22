import { describe, expect, it } from "vitest";
import { ApiError } from "../../api/http";
import type { Problem } from "../../api/types";
import { placeErrors, serverPlaceErrors } from "./placeErrors";

/**
 * A 400 problem with field errors.
 *
 * @param code Problem code.
 * @param errors Field errors.
 * @returns The error the API client throws.
 */
function problemError(code: string, errors: Problem["errors"]): ApiError {
  return new ApiError(400, { type: "about:blank", title: code, status: 400, code, errors });
}

/** Client-side checks: both fields are required. */
describe("placeErrors", () => {
  it("flags missing region and district", () => {
    expect(placeErrors({ regionId: null, districtId: null })).toEqual({
      region: "onboarding.error_region",
      district: "onboarding.error_district",
    });
    expect(placeErrors({ regionId: 1, districtId: 2 })).toEqual({});
  });
});

/** Server-side `validation_error` → field copy keys (contract §1), never raw messages. */
describe("serverPlaceErrors", () => {
  it("maps region_id and district_id to their fields", () => {
    const error = problemError("validation_error", { region_id: ["x"], district_id: ["y"] });
    expect(serverPlaceErrors(error)).toEqual({
      region: "onboarding.error_region",
      district: "onboarding.error_district",
    });
  });

  it("returns null for other fields, other codes and non-API errors", () => {
    expect(serverPlaceErrors(problemError("validation_error", { ui_language: ["x"] }))).toBeNull();
    expect(serverPlaceErrors(problemError("validation_error", null))).toBeNull();
    expect(serverPlaceErrors(problemError("internal_error", { district_id: ["x"] }))).toBeNull();
    expect(serverPlaceErrors(new Error("network"))).toBeNull();
  });
});
