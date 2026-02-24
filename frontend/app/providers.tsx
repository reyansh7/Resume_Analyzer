"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect, useState } from "react";
import Lenis from "lenis";
import { queryClient } from "@/lib/query-client";
import { ThemeProvider } from "@/components/theme-provider";

export function Providers({ children }: { children: ReactNode }) {
  const [lenis, setLenis] = useState<Lenis | null>(null);

  useEffect(() => {
    const instance = new Lenis({
      duration: 1.1,
      smoothWheel: true
    });

    let frame = 0;
    const raf = (time: number) => {
      instance.raf(time);
      frame = requestAnimationFrame(raf);
    };

    frame = requestAnimationFrame(raf);
    setLenis(instance);

    return () => {
      cancelAnimationFrame(frame);
      instance.destroy();
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>{children}</ThemeProvider>
      <span className="hidden" aria-hidden>
        {lenis ? "lenis-ready" : "lenis-init"}
      </span>
    </QueryClientProvider>
  );
}
