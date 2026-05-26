import { useTranslation, Trans } from "react-i18next";
import { Nav } from "./components/Nav";
import { Settings } from "./components/Settings";
import { Inbox } from "./components/Inbox";

export function App() {
  const { t } = useTranslation();
  return (
    <div className="app">
      <h1>{t("app.title")}</h1>
      <p>{t("app.tagline", { defaultValue: "Translate your React app" })}</p>
      <Trans i18nKey="app.welcome">Welcome to LocaleBridge</Trans>
      <Nav />
      <Inbox />
      <Settings />
      <footer>{t("app.footer")}</footer>
    </div>
  );
}
