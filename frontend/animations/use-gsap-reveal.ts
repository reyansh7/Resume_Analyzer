"use client";

import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function useGsapReveal(selector: string) {
  useEffect(() => {
    const elements = gsap.utils.toArray<HTMLElement>(selector);

    elements.forEach((element, index) => {
      gsap.fromTo(
        element,
        { opacity: 0, y: 36 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          delay: index * 0.06,
          ease: "power3.out",
          scrollTrigger: {
            trigger: element,
            start: "top 82%"
          }
        }
      );
    });

    return () => {
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, [selector]);
}
