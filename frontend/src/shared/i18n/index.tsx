/** Simple React hook & helper for typed bilingual i18n lookup. */

import React, { createContext, useContext, useState } from "react";
import en from "./en.json";
import mr from "./mr.json";

export type Language = "mr" | "en";

const translations = { mr, en };

interface I18nContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  lang: "mr",
  setLang: () => {},
  t: (key: string) => key,
});

export const I18nProvider = ({ children }: { children: React.ReactNode }): React.ReactElement => {
  const [lang, setLang] = useState<Language>("mr");

  const t = (key: string): string => {
    const keys = key.split(".");
    let current: any = translations[lang];
    for (const k of keys) {
      if (current && typeof current === "object" && k in current) {
        current = current[k];
      } else {
        return key;
      }
    }
    return typeof current === "string" ? current : key;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      <div lang={lang}>{children}</div>
    </I18nContext.Provider>
  );
};

export const useI18n = () => useContext(I18nContext);

