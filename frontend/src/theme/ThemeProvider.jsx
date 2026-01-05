import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { DEFAULT_THEME_ID, getThemeById, THEMES } from "./themes";

const STORAGE_KEY = "llm_theme_id";

const ThemeContext = createContext({
  themeId: DEFAULT_THEME_ID,
  theme: getThemeById(DEFAULT_THEME_ID),
  themes: THEMES,
  setThemeId: () => {},
});

export function ThemeProvider({ children }) {
  const [themeId, setThemeId] = useState(() => {
    if (typeof window === "undefined") return DEFAULT_THEME_ID;
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return saved || DEFAULT_THEME_ID;
  });

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, themeId);
    document.documentElement.dataset.theme = themeId;
  }, [themeId]);

  const value = useMemo(() => {
    const theme = getThemeById(themeId);
    return {
      themeId,
      theme,
      themes: THEMES,
      setThemeId,
    };
  }, [themeId]);

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
