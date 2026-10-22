import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useWatch, type UseFormSetError } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { ApiError } from "../../api/http";
import { useDistricts, useRegions, useUpdateMe } from "../../api/queries";
import type { Me } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { SelectField } from "../../components/ui/SelectField";
import { LANGUAGE_OPTIONS, LANGUAGES } from "../../i18n";

/** Language + region + district. Empty selects become NaN, which fails `z.number()`. */
const profileSchema = z.object({
  ui_language: z.enum(LANGUAGES),
  region_id: z.number({ error: "profile.required" }),
  district_id: z.number({ error: "profile.required" }),
});

type ProfileValues = z.infer<typeof profileSchema>;

/**
 * Copy `validation_error` field messages from the backend onto the form.
 *
 * @param error What the PATCH threw.
 * @param setError react-hook-form setter.
 * @returns Whether the error was a field validation error.
 */
function applyFieldErrors(error: unknown, setError: UseFormSetError<ProfileValues>): boolean {
  if (!(error instanceof ApiError) || error.code !== "validation_error") return false;
  for (const [field, messages] of Object.entries(error.problem?.errors ?? {})) {
    if (field in profileSchema.shape) setError(field as keyof ProfileValues, { message: messages.join(" ") });
  }
  return true;
}

/** Props of {@link ProfileForm}. */
interface ProfileFormProps {
  me: Me;
  submitLabel: string;
  onSaved?: (me: Me) => void;
}

/**
 * UI language, region and district, saved with `PATCH /me`. Used by onboarding and settings.
 *
 * @param props Current user, button label and success callback.
 * @returns The form.
 */
export function ProfileForm({ me, submitLabel, onSaved }: ProfileFormProps) {
  const { t } = useTranslation();
  const update = useUpdateMe();
  const {
    register,
    handleSubmit,
    control,
    setValue,
    setError,
    formState: { errors, isSubmitSuccessful },
  } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      ui_language: me.ui_language,
      region_id: me.region?.id ?? Number.NaN,
      district_id: me.district?.id ?? Number.NaN,
    },
  });
  const regionId = useWatch({ control, name: "region_id" });
  const regions = useRegions();
  const districts = useDistricts(Number.isNaN(regionId) ? null : regionId);
  const regionField = register("region_id", { valueAsNumber: true });

  /** Translate a client-side key or show a backend message as-is. */
  const fieldError = (message: string | undefined) => message && t(message);

  const onSubmit = handleSubmit((values) =>
    update.mutate(values, {
      onSuccess: (saved) => onSaved?.(saved),
      onError: (error) => applyFieldErrors(error, setError),
    }),
  );
  const generalError =
    update.error && !(update.error instanceof ApiError && update.error.code === "validation_error");

  return (
    <form noValidate onSubmit={(event) => void onSubmit(event)} className="flex flex-col gap-3">
      <SelectField label={t("profile.language")} options={LANGUAGE_OPTIONS} {...register("ui_language")} />
      <SelectField
        label={t("profile.region")}
        placeholder={t("profile.chooseRegion")}
        options={(regions.data ?? []).map((region) => ({ value: String(region.id), label: region.name }))}
        error={fieldError(errors.region_id?.message)}
        {...regionField}
        onChange={(event) => {
          setValue("district_id", Number.NaN);
          void regionField.onChange(event);
        }}
      />
      <SelectField
        label={t("profile.district")}
        placeholder={t("profile.chooseDistrict")}
        options={(districts.data ?? []).map((district) => ({
          value: String(district.id),
          label: district.name,
        }))}
        disabled={!districts.data}
        error={fieldError(errors.district_id?.message)}
        {...register("district_id", { valueAsNumber: true })}
      />
      {(regions.isError || districts.isError || generalError) && (
        <Alert tone="error">{t("common.error")}</Alert>
      )}
      {isSubmitSuccessful && update.isSuccess && <Alert>{t("common.saved")}</Alert>}
      <button type="submit" className="min-h-11 border" disabled={update.isPending}>
        {submitLabel}
      </button>
    </form>
  );
}
