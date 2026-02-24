"use client";

import { useEffect, useState } from "react";
import gsap from "gsap";

export function StatCounter({ target, suffix = "" }: { target: number; suffix?: string }) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const obj = { value: 0 };
    gsap.to(obj, {
      value: target,
      duration: 1.2,
      ease: "power2.out",
      onUpdate: () => setValue(Math.round(obj.value))
    });
  }, [target]);

  return <span>{value}{suffix}</span>;
}
