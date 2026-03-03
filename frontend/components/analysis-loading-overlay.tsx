"use client";

import React, { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { CheckCircle2, Loader2, FileCheck, Database, ListChecks, Target } from "lucide-react";

type AnalysisLoadingOverlayProps = {
  visible: boolean;
  requestInFlight: boolean;
  onFinished: () => void;
};

const STEPS = [
  { label: "Upload Resume", Icon: FileCheck },
  { label: "Parsing & Scoring", Icon: Database },
  { label: "Analyzing Skills Match", Icon: ListChecks },
  { label: "Generating Roadmap", Icon: Target }
];

function runTween(setup: () => gsap.core.Tween | gsap.core.Timeline) {
  return new Promise<void>((resolve) => {
    const tween = setup();
    tween.eventCallback("onComplete", () => resolve());
  });
}

export function AnalysisLoadingOverlay({ visible, requestInFlight, onFinished }: AnalysisLoadingOverlayProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [sequenceDone, setSequenceDone] = useState(false);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const titleRef = useRef<HTMLDivElement | null>(null);
  const roadsRef = useRef<SVGPathElement[]>([]);
  const cardRefs = useRef<Array<HTMLDivElement | null>>([]);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [isMobileView, setIsMobileView] = useState(false);

  const setRoadRef = (index: number, element: SVGPathElement | null) => {
    if (!element) return;
    roadsRef.current[index] = element;
  };

  const setCardRef = (index: number, element: HTMLDivElement | null) => {
    cardRefs.current[index] = element;
  };

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      setIsMobileView(false);
      return;
    }

    const media = window.matchMedia("(max-width: 767px)");
    const apply = (matches: boolean) => setIsMobileView(matches);
    apply(media.matches);

    const handler = (event: MediaQueryListEvent) => apply(event.matches);
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", handler);
      return () => media.removeEventListener("change", handler);
    }

    media.addListener(handler);

    return () => media.removeListener(handler);
  }, []);

  useEffect(() => {
    if (!visible) {
      setActiveStep(0);
      setCompletedSteps([]);
      setSequenceDone(false);
      return;
    }

    const overlay = overlayRef.current;
    const title = titleRef.current;
    const cards = cardRefs.current.filter((item): item is HTMLDivElement => Boolean(item));
    const roads = roadsRef.current.filter((item): item is SVGPathElement => Boolean(item));
    const svg = svgRef.current;

    let cancelled = false;
    let pulseTween: gsap.core.Tween | null = null;

    const runSequence = async () => {
      if (!overlay || !title || cards.length !== STEPS.length) return;

      gsap.set(overlay, { opacity: 0 });
      gsap.set(title, { opacity: 0, y: 20 });
      if (svg) {
        gsap.set(svg, { opacity: 0, scale: 0.95 });
      }

      gsap.set(cards, { opacity: 0, scale: 0.8, y: 30 });

      for (const road of roads) {
        if (typeof road.getTotalLength === "function") {
          const length = road.getTotalLength();
          road.style.strokeDasharray = `${length}`;
          road.style.strokeDashoffset = `${length}`;
        }
      }

      await runTween(() => {
        const timeline = gsap
          .timeline()
          .to(overlay, { opacity: 1, duration: 0.3, ease: "power2.out" })
          .to(title, { opacity: 1, y: 0, duration: 0.4, ease: "back.out(1.2)" }, "+=0.1");

        if (svg) {
          timeline.to(svg, { opacity: 1, scale: 1, duration: 0.5, ease: "power2.out" }, "-=0.2");
        }

        return timeline;
      });

      if (cancelled) return;

      for (let step = 0; step < STEPS.length; step += 1) {
        setActiveStep(step);
        await runTween(() => gsap.to(cards[step], { opacity: 1, scale: 1, y: 0, duration: 0.6, ease: "back.out(1.6)" }));
        if (cancelled) return;

        await runTween(() => gsap.to({}, { duration: 0.4 }));
        if (cancelled) return;

        setCompletedSteps((prev) => (prev.includes(step) ? prev : [...prev, step]));

        if (step < roads.length) {
          await runTween(() => gsap.to(roads[step], { strokeDashoffset: 0, duration: 0.8, ease: "power1.inOut" }));
          if (cancelled) return;
        }
      }

      setSequenceDone(true);
      pulseTween = gsap.to(cards[cards.length - 1], {
        scale: 1.03,
        boxShadow: "0px 15px 35px -5px rgba(20, 184, 166, 0.4)",
        duration: 0.85,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    };

    runSequence();

    return () => {
      cancelled = true;
      pulseTween?.kill();
    };
  }, [visible]);

  useEffect(() => {
    if (!visible || requestInFlight || !sequenceDone) return;
    const timeoutId = window.setTimeout(() => onFinished(), 360);
    return () => window.clearTimeout(timeoutId);
  }, [onFinished, requestInFlight, sequenceDone, visible]);

  if (!visible) return null;

  const cardPositions = [
    { left: "20%", top: "26%" },
    { left: "79%", top: "42%" },
    { left: "19%", top: "64%" },
    { left: "73%", top: "83%" }
  ];

  return (
    <div ref={overlayRef} className="fixed inset-0 z-[100] flex flex-col justify-center items-center bg-[#FDFCFB]/95 dark:bg-[#0B1120]/95 backdrop-blur-xl overflow-hidden">
      <div ref={titleRef} className="absolute top-[4%] md:top-[8%] text-center z-10 px-4">
        <h2 className="text-2xl sm:text-3xl md:text-5xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 mb-3 sm:mb-4">
          Analyzing your resume...
        </h2>
        <p className="text-xs sm:text-sm md:text-lg text-slate-500 dark:text-slate-400 font-medium">
          Please wait while we generate insights and recommendations using AI.
        </p>
      </div>

      <div className={`relative w-full pointer-events-none ${isMobileView ? "mt-20 px-4" : "max-w-5xl aspect-[10/7.5] mt-16 md:mt-24"}`}>
        {!isMobileView && (
        <svg ref={svgRef} className="absolute inset-0 h-full w-full overflow-visible" viewBox="0 0 1000 650" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
          <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id="road-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#2dd4bf" />
              <stop offset="100%" stopColor="#0ea5e9" />
            </linearGradient>
          </defs>

          {/* Thick transparent backgrounds */}
          <path d="M 255 175 C 460 120, 630 180, 710 300" className="stroke-teal-100/80 dark:stroke-teal-900/40 stroke-[16] fill-none" strokeLinecap="round" />
          <path d="M 710 300 C 580 360, 420 420, 255 450" className="stroke-teal-100/80 dark:stroke-teal-900/40 stroke-[16] fill-none" strokeLinecap="round" />
          <path d="M 255 450 C 430 505, 560 550, 660 575" className="stroke-teal-100/80 dark:stroke-teal-900/40 stroke-[16] fill-none" strokeLinecap="round" />

          {/* Dotted paths connecting logic visually */}
          <path d="M 255 175 C 460 120, 630 180, 710 300" className="stroke-white/80 dark:stroke-[#0B1120] stroke-[3] fill-none" strokeDasharray="7 8" strokeLinecap="round" />
          <path d="M 710 300 C 580 360, 420 420, 255 450" className="stroke-white/80 dark:stroke-[#0B1120] stroke-[3] fill-none" strokeDasharray="7 8" strokeLinecap="round" />
          <path d="M 255 450 C 430 505, 560 550, 660 575" className="stroke-white/80 dark:stroke-[#0B1120] stroke-[3] fill-none" strokeDasharray="7 8" strokeLinecap="round" />

          {/* Animated Paths */}
          <path ref={(el) => setRoadRef(0, el)} d="M 255 175 C 460 120, 630 180, 710 300" stroke="url(#road-grad)" className="stroke-[6] fill-none" strokeLinecap="round" filter="url(#glow)" />
          <path ref={(el) => setRoadRef(1, el)} d="M 710 300 C 580 360, 420 420, 255 450" stroke="url(#road-grad)" className="stroke-[6] fill-none" strokeLinecap="round" filter="url(#glow)" />
          <path ref={(el) => setRoadRef(2, el)} d="M 255 450 C 430 505, 560 550, 660 575" stroke="url(#road-grad)" className="stroke-[6] fill-none" strokeLinecap="round" filter="url(#glow)" />
        </svg>
        )}

        <div className={isMobileView ? "mx-auto flex w-full max-w-md flex-col gap-3" : "contents"}>
        {STEPS.map((step, index) => {
          const done = completedSteps.includes(index);
          const active = activeStep === index && !done;
          const { Icon } = step;

          return (
            <div
              key={step.label}
              ref={(el) => setCardRef(index, el)}
              className={`${isMobileView
                ? "relative w-full transition-colors bg-white/90 dark:bg-[#151E32]/90 backdrop-blur-xl rounded-2xl p-3.5 flex items-center gap-3 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.08)] dark:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] border border-slate-100/80 dark:border-slate-700/60"
                : "absolute -translate-x-1/2 -translate-y-1/2 w-[220px] sm:w-[260px] lg:w-[300px] transition-colors bg-white/90 dark:bg-[#151E32]/90 backdrop-blur-xl rounded-2xl p-4 sm:p-5 flex items-center gap-4 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.08)] dark:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] border border-slate-100/80 dark:border-slate-700/60"}`}
              style={isMobileView ? undefined : { left: cardPositions[index].left, top: cardPositions[index].top }}
            >
              <div className={`w-12 h-12 flex items-center justify-center rounded-xl shrink-0 transition-colors duration-500 ${done ? "bg-teal-500 text-white shadow-lg shadow-teal-500/30" : active ? "bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400" : "bg-slate-50 dark:bg-slate-800/50 text-slate-300 dark:text-slate-600"}`}>
                <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div className="flex-1">
                <h3 className={`font-semibold sm:font-bold text-sm sm:text-base transition-colors duration-500 ${done || active ? "text-slate-800 dark:text-slate-100" : "text-slate-400 dark:text-slate-500"}`}>
                  {step.label}
                </h3>
              </div>

              {active && (
                <div className="shrink-0 text-teal-500">
                  <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                </div>
              )}

              {done && (
                <div className="absolute right-2 top-2 bg-teal-500 dark:bg-teal-400 text-white dark:text-emerald-950 shadow-[0_0_15px_rgba(20,184,166,0.3)] text-[9px] sm:text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-full flex items-center gap-1 transform transition-all duration-300">
                  <CheckCircle2 className="w-3 h-3 sm:w-3.5 sm:h-3.5" /> Done
                </div>
              )}
            </div>
          );
        })}
        </div>
      </div>

      {sequenceDone && requestInFlight && (
        <div className="absolute bottom-[6%] px-4">
          <p className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-500/10 px-4 py-2 rounded-full border border-teal-100 dark:border-teal-500/20 shadow-sm animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin" /> Finalizing insights...
          </p>
        </div>
      )}
    </div>
  );
}

