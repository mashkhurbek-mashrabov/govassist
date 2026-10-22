/** Validation for the region/district picker. */
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
