"use client";

import { Moon, Sun } from "lucide-react";

const STORAGE_KEY = "resume-analyzer-theme";

export function ThemeToggle() {
  const handleToggle = () => {
    const root = window.document.documentElement;
    const isDark = root.classList.contains("dark");

    root.classList.toggle("dark", !isDark);
    localStorage.setItem(STORAGE_KEY, isDark ? "light" : "dark");
  };

  return (
    <button
      onClick={handleToggle}
      className="group relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-white/70 shadow-soft transition-all duration-300 hover:scale-105 hover:shadow-lg dark:bg-white/10"
      aria-label="Toggle dark mode"
    >
      <Sun className="h-4 w-4 text-amber-500 transition-all group-hover:rotate-12 dark:scale-0" />
      <Moon className="absolute h-4 w-4 scale-0 text-indigo-300 transition-all dark:scale-100 dark:group-hover:-rotate-12" />
    </button>
  );
}
