"use client";

import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function useParallax(selector: string, y = 80) {
  useEffect(() => {
    const targets = gsap.utils.toArray<HTMLElement>(selector);

    targets.forEach((target) => {
      gsap.to(target, {
        y,
        ease: "none",
        scrollTrigger: {
          trigger: target,
          scrub: true,
          start: "top bottom",
          end: "bottom top"
        }
      });
    });
  }, [selector, y]);
}
