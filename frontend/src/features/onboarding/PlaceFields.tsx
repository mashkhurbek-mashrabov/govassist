import { useTranslation } from "react-i18next";
import { useDistricts, useRegions } from "../../api/queries";
import { Combobox } from "../../components/ui/Combobox";

/** Selected region and district (SOATO codes). */
export interface Place {
  regionId: number | null;
  districtId: number | null;
}

/** Props of {@link PlaceFields}. */
interface PlaceFieldsProps {
  value: Place;
  onChange: (place: Place) => void;
  errors?: { region?: string | undefined; district?: string | undefined };
}

/**
 * Region → district comboboxes (onboarding step 2, settings "Your area"). Changing the region clears
 * the district and loads its districts.
 *
 * @param props Current place, change callback and translated errors.
 * @returns The two fields.
 */
export function PlaceFields({ value, onChange, errors }: PlaceFieldsProps) {
  const { t } = useTranslation();
  const regions = useRegions();
  const districts = useDistricts(value.regionId);
  return (
    <>
      <Combobox
        label={t("onboarding.region")}
        options={(regions.data ?? []).map((region) => ({ value: region.id, label: region.name }))}
        value={value.regionId}
        loading={regions.isPending}
        onChange={(regionId) => {
          if (regionId !== value.regionId) onChange({ regionId, districtId: null });
        }}
        error={errors?.region}
      />
      <Combobox
        label={t("onboarding.district")}
        options={(districts.data ?? []).map((district) => ({ value: district.id, label: district.name }))}
        value={value.districtId}
        loading={districts.isFetching && !districts.data}
        loadingText={t("onboarding.loading_districts")}
        disabledReason={value.regionId === null ? t("onboarding.choose_region_first") : undefined}
        onChange={(districtId) => onChange({ ...value, districtId })}
        error={errors?.district}
      />
    </>
  );
}
