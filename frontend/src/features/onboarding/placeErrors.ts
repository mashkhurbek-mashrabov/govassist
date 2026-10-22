/** Validation for the region/district picker. */
import { ApiError } from "../../api/http";
import type { Place } from "./PlaceFields";

/** Missing-field errors as copy keys. */
export interface PlaceErrors {
  region?: string;
  district?: string;
}

/**
 * Check that both region and district are chosen.
 *
 * @param place The selection.
 * @returns Copy keys for the missing fields (empty when valid).
 */
export function placeErrors(place: Place): PlaceErrors {
  return {
    ...(place.regionId === null && { region: "onboarding.error_region" }),
    ...(place.districtId === null && { district: "onboarding.error_district" }),
  };
}

/** `PATCH /me` fields of a `validation_error` → the picker field and its copy key (never the raw message). */
const SERVER_FIELDS: Record<string, [keyof PlaceErrors, string]> = {
  region_id: ["region", "onboarding.error_region"],
  district_id: ["district", "onboarding.error_district"],
};

/**
 * Field errors from a failed `PATCH /me` (400 `validation_error`, contract §1: `errors: {field: [messages]}`).
 *
 * @param error What the save threw.
 * @returns Copy keys for the region/district fields, or `null` when nothing maps to them (show the
 *   generic server error instead).
 */
export function serverPlaceErrors(error: unknown): PlaceErrors | null {
  if (!(error instanceof ApiError) || error.code !== "validation_error") return null;
  const mapped: PlaceErrors = {};
  for (const field of Object.keys(error.problem?.errors ?? {})) {
    const target = SERVER_FIELDS[field];
    if (target) mapped[target[0]] = target[1];
  }
  return Object.keys(mapped).length > 0 ? mapped : null;
}
