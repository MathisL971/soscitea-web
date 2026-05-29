import { useCallback, useEffect, useState } from "react";
import {
  applyTheme,
  getInitialTheme,
  persistTheme,
  THEME_STORAGE_KEY,
  type Theme,
} from "../theme";

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => getInitialTheme());

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function handleChange() {
      setThemeState((current) => {
        if (localStorage.getItem(THEME_STORAGE_KEY)) {
          return current;
        }
        const next = media.matches ? "dark" : "light";
        applyTheme(next);
        return next;
      });
    }

    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  const setTheme = useCallback((next: Theme) => {
    persistTheme(next);
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === "light" ? "dark" : "light");
  }, [setTheme, theme]);

  return { theme, setTheme, toggleTheme };
}
