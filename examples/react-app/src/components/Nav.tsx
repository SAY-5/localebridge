import { useTranslation } from "react-i18next";

export function Nav() {
  const { t } = useTranslation();
  return (
    <nav>
      {/** @i18n nav.home */}
      <a href="/" aria-label="Home">{t("nav.home", { defaultValue: "Home" })}</a>
      <a href="/inbox">{t("nav.inbox", { defaultValue: "Inbox" })}</a>
      <a href="/settings">{t("nav.settings", { defaultValue: "Settings" })}</a>
      <a href="/profile">{t("nav.profile", { defaultValue: "Profile" })}</a>
      <a href="/signout">{t("nav.signout", { defaultValue: "Sign out" })}</a>
    </nav>
  );
}
