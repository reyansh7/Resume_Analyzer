"use client";

import { ReactNode } from "react";
import { RouteTransition } from "@/animations/route-transition";

export default function Template({ children }: { children: ReactNode }) {
  return <RouteTransition>{children}</RouteTransition>;
}
