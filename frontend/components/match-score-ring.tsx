"use client";

import { useEffect, useMemo, useState } from "react";
import gsap from "gsap";

export function MatchScoreRing({ score }: { score: number }) {
  const [displayScore, setDisplayScore] = useState(0);
  const normalized = Math.max(0, Math.min(100, score));
  const { circumference, offset } = useMemo(() => {
    const radius = 70;
    const c = 2 * Math.PI * radius;
    return { circumference: c, offset: c - (normalized / 100) * c };
  }, [normalized]);

  useEffect(() => {
    const obj = { value: 0 };
    gsap.to(obj, {
      value: normalized,
      duration: 1.4,
      ease: "power3.out",
      onUpdate: () => setDisplayScore(Math.round(obj.value))
    });
  }, [normalized]);

  return (
    <div className="relative flex h-48 w-48 items-center justify-center">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 180 180">
        <circle cx="90" cy="90" r="70" stroke="currentColor" strokeWidth="12" className="text-secondary" fill="none" />
        <circle
          cx="90"
          cy="90"
          r="70"
          stroke="url(#gradient)"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          fill="none"
          className="transition-all duration-1000"
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <p className="text-4xl font-semibold">{displayScore}%</p>
        <p className="text-xs text-muted-foreground">Match Score</p>
      </div>
    </div>
  );
}
