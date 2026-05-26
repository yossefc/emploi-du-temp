import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import fr from "./fr.json";
import he from "./he.json";

i18n.use(initReactI18next).init({
  resources: {
    fr: { translation: fr },
    he: { translation: he },
  },
  lng: localStorage.getItem("lang") || "fr",
  fallbackLng: "fr",
  interpolation: { escapeValue: false },
});

// Appliquer la direction RTL pour l'hébreu
function applyDirection(lang: string) {
  document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
  document.documentElement.lang = lang;
}
applyDirection(i18n.language);
i18n.on("languageChanged", (lng) => {
  applyDirection(lng);
  localStorage.setItem("lang", lng);
});

export default i18n;
