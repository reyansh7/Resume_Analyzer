"use client";

import { ReactNode, useEffect, useState } from "react";

const STORAGE_KEY = "resume-analyzer-theme";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    const stored = localStorage.getItem(STORAGE_KEY);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored ? stored === "dark" : prefersDark;

    root.classList.toggle("dark", isDark);
    setReady(true);
  }, []);

  if (!ready) {
    return <div className="min-h-screen opacity-0">{children}</div>;
  }

  return <>{children}</>;
}
