import { useTranslation } from "react-i18next";

export function Settings() {
  const { t } = useTranslation();
  return (
    <section>
      <h2>{t("settings.title", { defaultValue: "Settings" })}</h2>
      <label>{t("settings.language", { defaultValue: "Language" })}</label>
      <label>{t("settings.theme", { defaultValue: "Theme" })}</label>
      <label>{t("settings.notifications", { defaultValue: "Notifications" })}</label>
      <button>{t("settings.save", { defaultValue: "Save changes" })}</button>
      <button>{t("settings.cancel", { defaultValue: "Cancel" })}</button>
      {/** @i18n settings.signout_button */}
      <button title="Sign out of your account">{t("settings.signout", { defaultValue: "Sign out" })}</button>
    </section>
  );
}
