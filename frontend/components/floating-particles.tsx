"use client";

import { useMemo } from "react";

export function FloatingParticles() {
  const particles = useMemo(
    () =>
      Array.from({ length: 16 }).map((_, index) => ({
        id: index,
        left: `${(index * 6.3 + 7) % 96}%`,
        delay: `${(index % 6) * 0.8}s`,
        duration: `${9 + (index % 5)}s`,
      })),
    []
  );

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {particles.map((particle) => (
        <span
          key={particle.id}
          className="particle"
          style={{ left: particle.left, animationDelay: particle.delay, animationDuration: particle.duration }}
        />
      ))}
    </div>
  );
}
