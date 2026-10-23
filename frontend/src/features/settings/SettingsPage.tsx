import { Check, Lock, LogOut, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useDeleteAccount, useLogout, useUpdateMe } from "../../api/queries";
import type { Quota } from "../../api/types";
import { useMe } from "../../app/layout/meContext";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { isLang } from "../../i18n";
import { TextField } from "../../components/ui/TextField";
import { LanguageCards } from "../language/LanguageCards";
import { useSwitchLanguage } from "../language/switchLanguage";
import { PlaceFields, type Place } from "../onboarding/PlaceFields";
import { placeErrors, serverPlaceErrors } from "../onboarding/placeErrors";
import { ChangePasswordForm } from "./ChangePasswordForm";

/**
 * Settings (screen 14): app language (applied at once), area, usage, account (name, password, logout,
 * delete). After logout or deletion `AppShell` sends the user to the landing page.
 *
 * @returns The page.
 */
export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const me = useMe();
  const switchTo = useSwitchLanguage();
  // The cards follow the active language, so they change at once (the PATCH /me follows in the background).
  const current = isLang(i18n.language) ? i18n.language : me.ui_language;
  return (
    <main className="page" id="main">
      <h1>{t("settings.title")}</h1>
      <section className="card" aria-labelledby="settings-language">
        <h2 className="t-h3" id="settings-language">
          {t("settings.language")}
        </h2>
        <LanguageCards
          value={current}
          onChange={(lang) => void switchTo(lang)}
          legend={t("settings.language")}
        />
      </section>
      <PlaceCard initial={{ regionId: me.region?.id ?? null, districtId: me.district?.id ?? null }} />
      <UsageCard quota={me.quota} />
      <AccountCard />
      <p className="footer-note">{t("app.not_official_long")}</p>
    </main>
  );
}

/** Props of {@link PlaceCard}. */
interface PlaceCardProps {
  initial: Place;
}

/**
 * "Your area": region + district, saved together.
 *
 * @param props The current place.
 * @returns The card.
 */
function PlaceCard({ initial }: PlaceCardProps) {
  const { t } = useTranslation();
  const update = useUpdateMe();
  const [place, setPlace] = useState(initial);
  const [submitted, setSubmitted] = useState(false);
  const serverErrors = update.isError ? serverPlaceErrors(update.error) : null;
  const errors = { ...(submitted ? placeErrors(place) : {}), ...serverErrors };

  /** Validate and save region + district in one request. */
  const save = () => {
    setSubmitted(true);
    if (place.regionId === null || place.districtId === null) return;
    update.mutate({ region_id: place.regionId, district_id: place.districtId });
  };

  return (
    <section className="card" aria-labelledby="settings-place">
      <h2 className="t-h3" id="settings-place">
        {t("settings.place")}
      </h2>
      <p className="field__hint">{t("settings.place_hint")}</p>
      <PlaceFields
        value={place}
        onChange={(next) => {
          setPlace(next);
          update.reset();
        }}
        errors={{
          region: errors.region && t(errors.region),
          district: errors.district && t(errors.district),
        }}
      />
      {update.isError && serverErrors === null && <Alert tone="danger">{t("error.server")}</Alert>}
      <div className="row-actions">
        {update.isSuccess ? (
          <p className="feedback__saved" role="status">
            <Check className="icon" aria-hidden="true" />
            {t("common.saved")}
          </p>
        ) : (
          <Button variant="primary" busy={update.isPending} busyLabel={t("common.saving")} onClick={save}>
            {t("common.save")}
          </Button>
        )}
      </div>
    </section>
  );
}

/** Props of {@link UsageCard}. */
interface UsageCardProps {
  quota: Quota;
}

/**
 * Usage: hourly and daily question meters.
 *
 * @param props The quota.
 * @returns The card.
 */
function UsageCard({ quota }: UsageCardProps) {
  const { t } = useTranslation();
  const meters = [
    { key: "settings.usage_hour", used: quota.hour_used, limit: quota.hour_limit },
    { key: "settings.usage_day", used: quota.day_used, limit: quota.day_limit },
  ];
  return (
    <section className="card" aria-labelledby="settings-usage">
      <h2 className="t-h3" id="settings-usage">
        {t("settings.usage")}
      </h2>
      {meters.map(({ key, used, limit }) => {
        const label = t(key, { used, limit });
        return (
          <div key={key} className="meter-row">
            <div className="meter-row__label">
              <span>{label}</span>
            </div>
            <div
              className="meter"
              role="meter"
              aria-valuemin={0}
              aria-valuemax={limit}
              aria-valuenow={used}
              aria-label={label}
            >
              <span style={{ width: `${Math.min(100, (used / Math.max(limit, 1)) * 100)}%` }} />
            </div>
          </div>
        );
      })}
      <p className="field__hint">{t("settings.usage_hint")}</p>
    </section>
  );
}

/**
 * Account: email, optional name (saved on blur), change/set password, log out, delete account.
 *
 * @returns The card.
 */
function AccountCard() {
  const { t } = useTranslation();
  const me = useMe();
  const update = useUpdateMe();
  const logout = useLogout();
  const deleteAccount = useDeleteAccount();
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  return (
    <section className="card" aria-labelledby="settings-account">
      <h2 className="t-h3" id="settings-account">
        {t("settings.account")}
      </h2>
      <dl className="kv">
        <dt>{t("auth.email")}</dt>
        <dd>{me.email}</dd>
      </dl>
      <TextField
        label={t("settings.display_name")}
        autoComplete="name"
        defaultValue={me.display_name ?? ""}
        onBlur={(event) => {
          const value = event.target.value.trim();
          if (value !== (me.display_name ?? "")) update.mutate({ display_name: value });
        }}
      />
      {passwordSaved && <Alert tone="success">{t("password_change.saved")}</Alert>}
      {passwordOpen && (
        <ChangePasswordForm
          hasPassword={me.has_password}
          onCancel={() => setPasswordOpen(false)}
          onSaved={() => {
            setPasswordOpen(false);
            setPasswordSaved(true);
          }}
        />
      )}
      <div className="row-actions">
        {!passwordOpen && (
          <Button
            icon={<Lock className="icon" aria-hidden="true" />}
            onClick={() => {
              setPasswordSaved(false);
              setPasswordOpen(true);
            }}
          >
            {t(me.has_password ? "settings.change_password" : "password_change.set_title")}
          </Button>
        )}
        <Button
          icon={<LogOut className="icon" aria-hidden="true" />}
          busy={logout.isPending}
          onClick={() => logout.mutate()}
        >
          {t("settings.logout")}
        </Button>
      </div>
      {logout.isError && <Alert tone="danger">{t("error.server")}</Alert>}
      <hr className="divider" />
      <div>
        <Button
          variant="danger-ghost"
          icon={<Trash2 className="icon" aria-hidden="true" />}
          onClick={() => setConfirmingDelete(true)}
        >
          {t("settings.delete_account")}
        </Button>
      </div>
      {deleteAccount.isError && <Alert tone="danger">{t("error.server")}</Alert>}
      <ConfirmDialog
        open={confirmingDelete}
        title={t("settings.delete_title")}
        body={t("settings.delete_body")}
        confirmCheck={t("settings.delete_confirm_check")}
        confirmLabel={t("settings.delete_submit")}
        busy={deleteAccount.isPending}
        onConfirm={() => deleteAccount.mutate()}
        onCancel={() => setConfirmingDelete(false)}
      />
    </section>
  );
}
