"use client";

import { useState, useEffect, useCallback } from "react";

type Theme = "dark" | "light";

export function useTheme() {
  // initialize from localStorage via lazy initializer — avoids setState in effect
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("wp_theme") as Theme) || "dark";
    }
    return "dark";
  });

  // apply data-theme attribute whenever theme changes
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("wp_theme", next);
      return next;
    });
  }, []);

  return { theme, toggleTheme };
}
