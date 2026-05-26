import { useTranslation, Trans } from "react-i18next";

export function Inbox() {
  const { t } = useTranslation();
  const count = 3;
  return (
    <section>
      <h2>{t("inbox.title", { defaultValue: "Inbox" })}</h2>
      <p>{t("inbox.empty", { defaultValue: "Your inbox is empty" })}</p>
      <p>{t("inbox.unread_count", { defaultValue: "{count, plural, one {You have 1 unread message} other {You have # unread messages}}", count })}</p>
      <Trans i18nKey="inbox.greeting">Hello, friend</Trans>
      <button>{t("inbox.compose", { defaultValue: "Compose" })}</button>
      <button>{t("inbox.archive", { defaultValue: "Archive" })}</button>
      <button>{t("inbox.delete", { defaultValue: "Delete" })}</button>
      <button>{t("inbox.mark_read", { defaultValue: "Mark as read" })}</button>
      <button>{t("inbox.mark_unread", { defaultValue: "Mark as unread" })}</button>
      <a href="#">{t("inbox.see_all", { defaultValue: "See all messages" })}</a>
      <span>{t("inbox.last_sync", { defaultValue: "Last synced just now" })}</span>
      <p>{t("inbox.help_hint", { defaultValue: "Need help? Visit the help center." })}</p>
    </section>
  );
}
