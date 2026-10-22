import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useDeleteAccount, useLogout } from "../../api/queries";
import { useMe } from "../../app/layout/meContext";
import { Alert } from "../../components/ui/Alert";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { ProfileForm } from "../onboarding/ProfileForm";
import { ChangePasswordForm } from "./ChangePasswordForm";

/**
 * Profile (language, region, district), quota, password, logout and account deletion.
 * After logout or deletion `AppShell` sends the user to the login page.
 *
 * @returns The page.
 */
export function SettingsPage() {
  const { t } = useTranslation();
  const me = useMe();
  const logout = useLogout();
  const deleteAccount = useDeleteAccount();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  return (
    <div className="mx-auto flex w-full max-w-xl flex-col gap-8">
      <h1 className="font-bold">{t("settings.title")}</h1>
      <p>{me.email}</p>

      <section className="flex flex-col gap-3">
        <h2 className="font-bold">{t("settings.profile")}</h2>
        <ProfileForm me={me} submitLabel={t("common.save")} />
      </section>

      <section className="flex flex-col gap-1">
        <h2 className="font-bold">{t("settings.quota.title")}</h2>
        <p>{t("settings.quota.hour", { used: me.quota.hour_used, limit: me.quota.hour_limit })}</p>
        <p>{t("settings.quota.day", { used: me.quota.day_used, limit: me.quota.day_limit })}</p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-bold">{t("settings.password.title")}</h2>
        <ChangePasswordForm />
      </section>

      <section className="flex flex-col gap-3">
        <button
          type="button"
          className="min-h-11 border"
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          {t("settings.logout")}
        </button>
        {logout.isError && <Alert tone="error">{t("common.error")}</Alert>}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-bold">{t("settings.deleteAccount.title")}</h2>
        <p>{t("settings.deleteAccount.body")}</p>
        <button type="button" className="min-h-11 border" onClick={() => setConfirmingDelete(true)}>
          {t("settings.deleteAccount.button")}
        </button>
        {deleteAccount.isError && <Alert tone="error">{t("common.error")}</Alert>}
        <ConfirmDialog
          open={confirmingDelete}
          title={t("settings.deleteAccount.title")}
          body={t("settings.deleteAccount.confirm")}
          confirmLabel={t("settings.deleteAccount.button")}
          pending={deleteAccount.isPending}
          onConfirm={() => deleteAccount.mutate()}
          onCancel={() => setConfirmingDelete(false)}
        />
      </section>
    </div>
  );
}
