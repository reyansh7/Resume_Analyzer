"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useGsapReveal } from "@/animations/use-gsap-reveal";
import { useParallax } from "@/animations/use-parallax";
import { StatCounter } from "@/components/stat-counter";
import { Boxes } from "@/components/ui/background-boxes";
import { BrainCircuit, UserPlus, FileText, Target, ArrowRight } from "lucide-react";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const features = [
  "AI resume parsing with JSONB persistence",
  "Skill gap scoring with embeddings",
  "Personalized roadmap and certifications",
  "Production-ready microservice architecture"
];

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const leftColRef = useRef<HTMLDivElement>(null);
  const mockupRef = useRef<HTMLDivElement>(null);

  useGsapReveal(".reveal");
  useParallax(".parallax", 70);

  useEffect(() => {
    if (!heroRef.current || !leftColRef.current || !mockupRef.current) return;

    const timeline = gsap.timeline();
    timeline
      .fromTo(
        leftColRef.current.querySelectorAll(".hero-animate"),
        { y: 32, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, stagger: 0.15, ease: "power3.out" }
      )
      .fromTo(
        mockupRef.current,
        {
          x: 80,
          opacity: 0,
          rotationY: -5,
          rotationX: 2,
          transformPerspective: 1200
        },
        {
          x: 0,
          opacity: 1,
          rotationY: -18,
          rotationX: 6,
          duration: 1.2,
          ease: "power3.out"
        },
        "-=0.6"
      )
      .fromTo(
        ".mockup-float-card",
        {
          x: 60,
          opacity: 0,
          rotationY: -5,
          rotationX: 2,
          z: 0
        },
        {
          x: 0,
          opacity: 1,
          rotationY: -12,
          rotationX: 4,
          z: 40,
          duration: 1.2,
          ease: "power3.out"
        },
        "-=0.9"
      )
      .to(".animate-circle", { strokeDashoffset: 45.2, duration: 2, ease: "power3.out" }, "-=0.8")
      .to(".animate-bar", {
        width: (_i: number, el: Element) => `${el.getAttribute("data-width")}%`,
        duration: 1.5,
        ease: "power3.out",
        stagger: 0.1
      }, "-=1.5")
      .to(".animate-number", {
        textContent: (_i: number, el: Element) => el.getAttribute("data-target"),
        duration: 1.5,
        snap: { textContent: 1 },
        ease: "power3.out",
        stagger: 0.1
      }, "-=1.5");

    // Mouse movement parallax for 3D realism
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      const x = (e.clientX / innerWidth - 0.5) * 10;
      const y = (e.clientY / innerHeight - 0.5) * 6;

      gsap.to(mockupRef.current, {
        rotationY: -18 + x,
        rotationX: 6 - y,
        duration: 0.5,
        ease: "power2.out"
      });
      gsap.to(".mockup-float-card", {
        rotationY: -12 + (x * 1.5),
        rotationX: 4 - (y * 1.5),
        duration: 0.6,
        ease: "power2.out"
      });
    };

    window.addEventListener("mousemove", handleMouseMove);

    // Subtle floating animation for the mockup
    const float1 = gsap.to(mockupRef.current, {
      y: -10,
      duration: 3,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });

    const float2 = gsap.to(".mockup-float-card", {
      y: -15,
      duration: 3.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
      delay: 0.5
    });

    // 3D Scroll Animations for the new sections
    const stepCards = gsap.utils.toArray<HTMLElement>(".step-3d-card");
    stepCards.forEach((card, i) => {
      gsap.fromTo(
        card,
        {
          opacity: 0,
          y: 200,
          rotationX: -30,
          rotationY: i % 2 === 0 ? 20 : -20,
          scale: 0.85,
          transformPerspective: 1200,
        },
        {
          opacity: 1,
          y: 0,
          rotationX: 0,
          rotationY: 0,
          scale: 1,
          duration: 1.8,
          ease: "expo.out",
          scrollTrigger: {
            trigger: card,
            start: "top 90%",
            end: "center 55%",
            scrub: 1.2,
          },
        }
      );
    });

    ScrollTrigger.create({
      trigger: ".skill-gap-container",
      start: "top 80%",
      onEnter: () => {
        gsap.to(".skill-gap-bar", {
          width: (_i: number, el: Element) => `${el.getAttribute("data-width")}%`,
          duration: 1.5,
          ease: "power3.out",
          stagger: 0.15
        });
        gsap.to(".skill-gap-number", {
          textContent: (_i: number, el: Element) => el.getAttribute("data-target"),
          duration: 1.5,
          snap: { textContent: 1 },
          ease: "power3.out",
          stagger: 0.15
        });
      },
      once: true
    });

    gsap.fromTo(
      ".roadmap-item",
      { opacity: 0, x: -30 },
      {
        opacity: 1, x: 0, duration: 0.8, stagger: 0.2, ease: "power3.out",
        scrollTrigger: {
          trigger: ".roadmap-container",
          start: "top 80%",
          once: true
        }
      }
    );

    gsap.to(".roadmap-line", {
      height: "calc(100% - 32px)",
      ease: "none",
      scrollTrigger: {
        trigger: ".roadmap-container",
        start: "top 60%",
        end: "bottom 60%",
        scrub: true
      }
    });

    gsap.utils.toArray<HTMLElement>(".roadmap-node").forEach((node) => {
      gsap.to(node, {
        borderColor: "#14b8a6",
        color: "#14b8a6",
        scrollTrigger: {
          trigger: node,
          start: "top 60%",
          end: "top 60%",
          scrub: true
        }
      });
    });

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      float1.kill();
      float2.kill();
    };
  }, []);

  return (
    <main className="relative overflow-hidden bg-background text-foreground transition-colors duration-300">
      {/* Animated background boxes */}
      <div className="fixed inset-0 z-0 overflow-hidden opacity-30 dark:opacity-20 pointer-events-none">

      </div>

      {/* Page content above background */}
      <div className="relative z-20">
        <div className="pointer-events-auto">
          <Navbar />
        </div>

        {/* NEW HERO SECTION - 2 COLUMN LAYOUT */}
        <section ref={heroRef} className="mx-auto max-w-7xl px-4 pt-4 pb-10 md:pt-6 md:pb-12 lg:pt-8 lg:pb-16">
          <div className="grid grid-cols-1 gap-10 md:gap-12 lg:grid-cols-[1fr_500px] xl:grid-cols-[1fr_600px] lg:gap-12 items-center">

            {/* LEFT SIDE: Content */}
            <div ref={leftColRef} className="space-y-8 flex flex-col items-center text-center lg:items-start lg:text-left relative z-10 w-full">
              {/* Subtle radial glow */}
              <div className="absolute -left-16 top-0 h-[280px] w-[280px] sm:h-[360px] sm:w-[360px] rounded-full bg-white/40 dark:bg-teal-500/5 blur-[80px] sm:blur-[100px] -z-10 pointer-events-none" />

              <h1 className="hero-animate text-balance text-4xl font-bold leading-[1.1] tracking-tight text-slate-900 dark:text-slate-50 sm:text-5xl md:text-6xl lg:text-7xl">
                See your career the <br className="hidden lg:block" />
                <span className="text-primary font-serif italic font-normal tracking-normal text-[1.1em] leading-none block mt-2">
                  way recruiters do.
                </span>
              </h1>

              <p className="hero-animate max-w-xl text-base text-slate-600 dark:text-slate-300 leading-relaxed font-medium sm:text-lg">
                Uncover skill gaps, match to your dream jobs, and build a step-by-step roadmap, all with powerful AI insights.
              </p>

              <div className="hero-animate flex flex-col sm:flex-row items-center gap-4 pt-4 w-full sm:w-auto">
                <Link href="/login" className="w-full sm:w-auto">
                  <Button className="w-full sm:w-auto rounded-full px-8 py-6 text-base font-semibold shadow-[0_8px_20px_-6px_rgba(13,148,136,0.4)] hover:shadow-[0_12px_24px_-8px_rgba(13,148,136,0.6)] hover:-translate-y-0.5 transition-all bg-primary hover:bg-[#0F766E] text-white border-0">
                    Start Free Analysis
                  </Button>
                </Link>
                <Link href="/dashboard" className="w-full sm:w-auto">
                  <Button variant="ghost" className="w-full sm:w-auto rounded-full px-8 py-6 text-base font-semibold border-slate-300/60 dark:border-slate-700/60 hover:bg-white/50 dark:hover:bg-slate-800/50 hover:-translate-y-0.5 transition-all bg-white/20 dark:bg-slate-900/20 text-slate-700 dark:text-slate-200 backdrop-blur-sm shadow-sm">
                    View Demo
                  </Button>
                </Link>
              </div>
            </div>

            {/* RIGHT SIDE: Floating Dashboard Mockup */}
            <div className="perspective-1200 pointer-events-none relative w-full max-w-[500px] mx-auto lg:max-w-none lg:mx-0 min-h-[360px] sm:min-h-[420px] lg:min-h-[450px]">
              {/* Decorative Elements around Mockup */}
              <div className="absolute -z-10 top-1/2 -right-12 h-64 w-64 rounded-full bg-teal-500/10 dark:bg-teal-500/20 blur-[80px]" />
              <div className="absolute -z-10 -bottom-12 -left-12 h-48 w-48 rounded-full bg-blue-500/5 dark:bg-blue-500/10 blur-[60px]" />

              {/* CARD 1: Main Browser Window */}
              <div
                ref={mockupRef}
                className="absolute left-0 top-0 w-full max-w-[420px] sm:max-w-[460px] overflow-hidden rounded-2xl bg-[#FDFCFB] dark:bg-[#0F1629] p-2 flex flex-col will-change-transform"
                style={{
                  transform: "rotateY(-18deg) rotateX(6deg)",
                  transformStyle: "preserve-3d",
                  boxShadow: "0 40px 80px rgba(15, 23, 42, 0.12), 0 15px 30px rgba(15, 23, 42, 0.08)"
                }}
              >
                {/* Mock Browser Header */}
                <div className="flex items-center justify-between px-4 pt-3 pb-4">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-400 tracking-wide">Resume Analyzer AI</span>
                  <div className="flex items-center gap-3 opacity-40">
                    <span className="text-[10px] font-medium text-slate-500">Overview</span>
                    <div className="flex flex-col gap-1">
                      <div className="h-0.5 w-4 bg-slate-400 rounded-full" />
                      <div className="h-0.5 w-4 bg-slate-400 rounded-full" />
                      <div className="h-0.5 w-4 bg-slate-400 rounded-full" />
                    </div>
                  </div>
                </div>

                {/* Inner Content Area */}
                <div className="bg-white/50 dark:bg-[#0B1120]/50 rounded-xl p-6 flex flex-col gap-6 m-1 border border-slate-100/50 dark:border-slate-800/30">

                  {/* Improve Resume Section */}
                  <div className="space-y-4 pr-16">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="h-5 w-5 rounded bg-teal-100 dark:bg-teal-900 flex items-center justify-center">
                        <FileText className="h-3 w-3 text-teal-600 dark:text-teal-400" />
                      </div>
                      <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">Resume Review</span>
                    </div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 tracking-tight">Improve Resume</h3>

                    {/* Fake text skeleton */}
                    <div className="space-y-2 pb-2">
                      <div className="h-1.5 w-full bg-slate-200/60 dark:bg-slate-800 rounded-full" />
                      <div className="h-1.5 w-3/4 bg-slate-200/60 dark:bg-slate-800 rounded-full" />
                      <div className="h-1.5 w-5/6 bg-slate-200/60 dark:bg-slate-800 rounded-full" />
                    </div>

                    <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800/50">
                      <div className="flex items-center justify-between">
                        <div className="h-2 w-1/2 bg-teal-600/80 dark:bg-teal-500/80 rounded-full" />
                        <span className="text-xs font-bold text-slate-700 dark:text-slate-300">82%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="h-2 w-1/3 bg-teal-600/40 dark:bg-teal-500/40 rounded-full" />
                        <span className="text-[10px] font-medium text-slate-400">Score</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="h-2 w-1/4 bg-teal-600/40 dark:bg-teal-500/40 rounded-full" />
                        <span className="text-[10px] font-medium text-slate-400">Format</span>
                      </div>
                    </div>
                  </div>

                  {/* Suggested Roadmap */}
                  <div className="pt-4 border-t border-slate-100 dark:border-slate-800/50 pr-12">
                    <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 tracking-tight mb-4">Suggested Roadmap</h3>

                    <div className="relative pl-4 space-y-5">
                      {/* Line connecting nodes */}
                      <div className="absolute left-[7px] top-2 bottom-2 w-px bg-slate-200 dark:bg-slate-700" />

                      {/* Node 1 */}
                      <div className="relative">
                        <div className="absolute -left-[18px] top-1.5 h-2.5 w-2.5 rounded-full bg-white border-2 border-teal-500" />
                        <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300">Learn Advanced React Patterns</h4>
                        <div className="flex items-center gap-2 mt-1 opacity-60">
                          <div className="h-2 w-2 rounded-sm border border-slate-400" />
                          <span className="text-[9px] text-slate-500">Immediate course - SystemDesign - Arjube</span>
                        </div>
                      </div>

                      {/* Node 2 */}
                      <div className="relative">
                        <div className="absolute -left-[18px] top-1.5 h-2.5 w-2.5 rounded-full bg-white border-2 border-teal-500" />
                        <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300">Master Redux for State Management</h4>
                        <div className="flex items-center gap-2 mt-1 opacity-60">
                          <div className="h-2 w-2 rounded-sm border border-slate-400" />
                          <span className="text-[9px] text-slate-500">Online course - Estimated time 6 hours</span>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>
              </div>

              {/* CARD 2: Floating Stats Overlap */}
              <div
                className="mockup-float-card absolute top-6 right-0 sm:top-10 sm:-right-6 lg:-right-12 w-[220px] sm:w-[260px] lg:w-[280px] bg-white dark:bg-[#151E32] rounded-2xl p-3 sm:p-4 lg:p-5 border border-slate-100 dark:border-slate-700 shadow-[0_30px_60px_-15px_rgba(15,23,42,0.15)] dark:shadow-[0_30px_60px_-15px_rgba(0,0,0,0.6)] transform-style-3d backdrop-blur-md"
                style={{ transform: "rotateY(-8deg) rotateX(2deg) translateZ(30px)" }}
              >
                {/* Analytics Top Section */}
                <div className="flex items-center gap-4 mb-6">
                  {/* Score Widget */}
                  <div className="relative flex flex-col items-center justify-center shrink-0">
                    <svg className="h-[72px] w-[72px] transform -rotate-90">
                      <circle cx="36" cy="36" r="30" stroke="currentColor" strokeWidth="5" fill="transparent" className="text-teal-50 dark:text-slate-800" />
                      <circle
                        cx="36" cy="36" r="30" stroke="currentColor" strokeWidth="5" fill="transparent"
                        strokeDasharray="188.4" strokeDashoffset="188.4"
                        className="text-primary animate-circle drop-shadow-md"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <div className="h-6 w-6 rounded-full bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center">
                        <Target className="h-3 w-3 text-teal-600 dark:text-teal-400" />
                      </div>
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="flex items-baseline gap-1 mb-1">
                      <span className="animate-number text-3xl font-bold tracking-tighter text-slate-900 dark:text-white leading-none" data-target="82">0</span>
                      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600 dark:text-slate-400">Match</span>
                    </div>

                    {/* Confidence */}
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 tracking-wide">Confidence</span>
                      <div className="h-1.5 flex-1 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div className="h-full bg-teal-500 rounded-full animate-bar w-0" data-width="86" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300"><span className="animate-number" data-target="86">0</span>%</span>
                    </div>
                  </div>
                </div>

                {/* Skill Bars */}
                <div className="space-y-4 border-t border-slate-100 dark:border-slate-800/50 pt-4">
                  {[
                    { label: "Technical Skills", val: 84 },
                    { label: "Experience Match", val: 77 },
                    { label: "Soft Skills Match", val: 68 },
                    { label: "Education Match", val: 90 }
                  ].map((skill, idx) => (
                    <div key={idx} className="space-y-1.5 group">
                      <div className="flex justify-between items-center text-xs px-0.5">
                        <span className="font-semibold text-slate-700 dark:text-slate-300 tracking-tight">{skill.label}</span>
                        <span className="font-bold text-slate-900 dark:text-slate-100"><span className="animate-number" data-target={skill.val}>0</span>%</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div className="h-full bg-teal-600 dark:bg-teal-500 rounded-full animate-bar w-0" data-width={skill.val} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Roadmaps snippet */}
                <div className="pt-5 mt-1 border-t border-slate-100 dark:border-slate-800/50">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">30 Day Plan</span>
                      <ArrowRight className="h-3 w-3 text-slate-400" />
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden mb-4">
                      <div className="h-full bg-teal-600/80 dark:bg-teal-500/80 rounded-full animate-bar w-0" data-width="60" />
                    </div>

                    <div className="flex items-center justify-between text-xs opacity-60">
                      <span className="font-semibold text-slate-600 dark:text-slate-400">60 Day Plan</span>
                      <div className="h-2 w-2 rounded-full border border-slate-400" />
                    </div>

                    <div className="flex items-center justify-between text-xs opacity-60">
                      <span className="font-semibold text-slate-600 dark:text-slate-400">90 Day Plan</span>
                      <div className="h-2 w-2 rounded-full border border-slate-400" />
                    </div>
                  </div>
                </div>

              </div>
            </div>

          </div>

          {/* Stats Section below Hero Grid */}
          <div className="grid max-w-4xl grid-cols-1 sm:grid-cols-3 gap-8 pt-14 mx-auto text-center mt-32 sm:mt-24 lg:mt-20 relative z-10">
            <div className="reveal space-y-3">
              <p className="text-4xl lg:text-5xl font-semibold text-slate-800 dark:text-slate-200 tracking-tight"><StatCounter target={98} suffix="%" /></p>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 tracking-wide uppercase">Highly Accurate</p>
            </div>
            <div className="reveal space-y-3">
              <p className="text-4xl lg:text-5xl font-semibold text-slate-800 dark:text-slate-200 tracking-tight"><StatCounter target={12000} suffix="+" /></p>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 tracking-wide uppercase">Resumes Analyzed</p>
            </div>
            <div className="reveal space-y-3">
              <p className="text-4xl lg:text-5xl font-semibold text-slate-800 dark:text-slate-200 tracking-tight"><StatCounter target={4} suffix="x" /></p>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 tracking-wide uppercase">Faster Upskilling</p>
            </div>
          </div>
        </section>

        {/* 4 New Sections with 3D Reveal */}
        <section className="relative mx-auto max-w-6xl space-y-40 px-4 py-32">
          {/* Section 1: Three steps */}
          <div className="step-3d-card flex flex-col items-center text-center w-full">
            <span className="text-xs font-bold uppercase tracking-widest text-[#5EEAD4] mb-4">How it works</span>
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-6">
              Three steps to your <br />
              <span className="font-serif italic font-normal tracking-normal text-[1.05em] text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-teal-400 dark:from-teal-400 dark:to-teal-200 inline-block mt-1">dream offer.</span>
            </h2>
            <p className="max-w-2xl text-lg text-slate-600 dark:text-slate-400 mb-16">
              Not another checklist tool. A true AI advisor that understands what the market wants—and builds you a path to get there.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
              {/* Card 1 */}
              <div className="relative group overflow-hidden rounded-2xl bg-slate-50 dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 p-8 text-left h-full transition-all hover:border-teal-500/50">
                <div className="absolute top-4 right-4 text-7xl font-black text-slate-200 dark:text-slate-800/50 group-hover:text-teal-500/10 transition-colors">01</div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400">
                    <FileText className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Upload</span>
                </div>
                <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4">Let's see how recruiters see you.</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                  Drop your resume and tell us where you're headed. Our NLP engine parses every detail—experience, impact, keywords—in under three seconds.
                </p>
                <div className="flex items-center gap-2 text-xs font-medium text-teal-600 dark:text-teal-500">
                  <span>⚡</span> 3s parse time
                </div>
              </div>

              {/* Card 2 */}
              <div className="relative group overflow-hidden rounded-2xl bg-slate-50 dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 p-8 text-left h-full transition-all hover:border-teal-500/50">
                <div className="absolute top-4 right-4 text-7xl font-black text-slate-200 dark:text-slate-800/50 group-hover:text-teal-500/10 transition-colors">02</div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400">
                    <Target className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Analyze</span>
                </div>
                <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4">Understand what's holding you back.</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                  AI scores your alignment with your target role. Identifies missing skills, quantifies your strengths, and compares you to top candidates in the field.
                </p>
                <div className="flex items-center gap-2 text-xs font-medium text-teal-600 dark:text-teal-500">
                  <span>⚡</span> 127 scoring signals
                </div>
              </div>

              {/* Card 3 */}
              <div className="relative group overflow-hidden rounded-2xl bg-slate-50 dark:bg-[#0F172A] border border-slate-200 dark:border-slate-800 p-8 text-left h-full transition-all hover:border-teal-500/50">
                <div className="absolute top-4 right-4 text-7xl font-black text-slate-200 dark:text-slate-800/50 group-hover:text-teal-500/10 transition-colors">03</div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400">
                    <BrainCircuit className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Accelerate</span>
                </div>
                <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4">A week-by-week plan built just for you.</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                  Not generic tips. A specific, prioritized roadmap—courses, projects, and skills—calculated to close your gap as fast as possible.
                </p>
                <div className="flex items-center gap-2 text-xs font-medium text-teal-600 dark:text-teal-500">
                  <span>⚡</span> Avg. 4x faster placement
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Exact gap */}
          <div className="step-3d-card flex flex-col gap-16 md:flex-row items-center justify-between w-full">
            <div className="flex-1 space-y-6">
              <span className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400">Skill Intelligence</span>
              <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.1]">
                Understand your <br />
                <span className="font-serif italic font-normal tracking-normal text-[1.05em] text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-teal-400 dark:from-teal-400 dark:to-teal-200 inline-block mt-1">exact gap.</span>
              </h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                We don't just list missing skills. We quantify how far away you are from what top companies actually hire for—and rank what matters most.
              </p>
              <div className="flex gap-6 pt-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800/50 px-4 py-2 rounded-full border border-slate-200 dark:border-slate-700">
                  <BrainCircuit className="w-4 h-4 text-teal-600 dark:text-teal-400" /> 127 signals analyzed
                </div>
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800/50 px-4 py-2 rounded-full border border-slate-200 dark:border-slate-700">
                  <Target className="w-4 h-4 text-teal-600 dark:text-teal-400" /> Real-time job data
                </div>
              </div>
            </div>
            <div className="flex-1 w-full perspective-1000 skill-gap-container">
              <div className="bg-white dark:bg-[#0B1120] rounded-2xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl dark:shadow-[0_0_50px_-12px_rgba(20,184,166,0.15)]" style={{ transform: "rotateY(-5deg) rotateX(2deg)" }}>
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white">Skill Gap Analysis</h3>
                  <span className="text-xs font-semibold px-3 py-1 bg-teal-100 dark:bg-teal-500/20 text-teal-700 dark:text-teal-400 rounded-full border border-teal-200 dark:border-teal-500/30">Target: L5 SWE</span>
                </div>
                <div className="space-y-6">
                  {[
                    { name: 'System Design', gap: -36, you: 42, market: 78 },
                    { name: 'Kubernetes', gap: -47, you: 18, market: 65 },
                    { name: 'TypeScript', gap: -5, you: 85, market: 90 },
                    { name: 'ML Pipelines', gap: -42, you: 30, market: 72 },
                    { name: 'API Design', gap: -12, you: 71, market: 83 }
                  ].map((skill, i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-bold text-slate-700 dark:text-slate-200">{skill.name}</span>
                        <span className="font-mono text-xs text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-500/10 px-2 py-0.5 rounded border border-teal-200 dark:border-teal-500/20">{skill.gap}</span>
                      </div>
                      <div className="relative h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div className="absolute top-0 left-0 h-full bg-slate-200 dark:bg-slate-700 rounded-full" style={{ width: `${skill.market}%` }} />
                        <div className="skill-gap-bar absolute top-0 left-0 h-full bg-gradient-to-r from-teal-500 to-emerald-400 dark:from-teal-600 dark:to-emerald-400 rounded-full shadow-[0_0_10px_rgba(20,184,166,0.4)] dark:shadow-[0_0_10px_rgba(20,184,166,0.8)]" data-width={skill.you} style={{ width: "0%" }} />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                        <span>You: <span className="skill-gap-number" data-target={skill.you}>0</span>%</span>
                        <span>Market avg: {skill.market}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Roadmap */}
          <div className="step-3d-card flex flex-col gap-16 md:flex-row items-center justify-between w-full">
            <div className="flex-1 space-y-6">
              <span className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400">Roadmap</span>
              <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.1]">
                Your week-by-week <br />
                <span className="font-serif italic font-normal tracking-normal text-[1.05em] text-teal-600 dark:text-teal-400 inline-block mt-1">master plan.</span>
              </h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Not a vague "learn Python" suggestion. A precise, sequenced plan of courses, projects, and milestones—ranked by impact on your score.
              </p>
              <div className="pt-4">
              
              </div>
            </div>
            <div className="flex-1 w-full pl-0 md:pl-12 roadmap-container">
              <div className="relative space-y-6">
                {/* Vertical Line Background */}
                <div className="absolute left-[20px] top-4 bottom-4 w-px bg-slate-200 dark:bg-slate-800" />
                {/* Animated Vertical Line Foreground */}
                <div className="roadmap-line absolute left-[20px] top-4 w-px bg-teal-500 shadow-[0_0_10px_rgba(20,184,166,0.8)] z-0" style={{ height: "0%" }} />

                {[
                  { week: 'W1', title: 'System Design Fundamentals', tag: 'CRITICAL' },
                  { week: 'W2', title: 'Kubernetes & Container Orchestration', tag: 'HIGH' },
                  { week: 'W3-4', title: 'ML Pipeline Architecture', tag: 'HIGH' },
                  { week: 'W5-6', title: 'Advanced API Design Patterns', tag: 'MEDIUM' },
                  { week: 'W7-8', title: 'Portfolio Project: Full-Stack ML App', tag: 'ACTION' }
                ].map((item, i) => (
                  <div key={i} className="roadmap-item relative flex items-center gap-6 group">
                    <div className="roadmap-node flex items-center justify-center w-10 h-10 rounded-full bg-white dark:bg-[#0F172A] border border-slate-300 dark:border-slate-700 text-xs font-bold text-slate-600 dark:text-slate-300 z-10 shadow-sm transition-colors">
                      {item.week}
                    </div>
                    <div className="flex-1 bg-white dark:bg-[#0B1120] border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex items-center justify-between transition-all hover:border-teal-500/50 dark:hover:border-teal-400/50 shadow-sm relative overflow-hidden group-hover:shadow-[0_4px_20px_-4px_rgba(20,184,166,0.1)]">
                      <div className="absolute inset-0 bg-gradient-to-r from-teal-500/0 via-teal-500/0 to-teal-500/5 dark:to-teal-400/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                      <span className="font-semibold text-slate-800 dark:text-slate-200 text-sm relative z-10">{item.title}</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border text-teal-700 bg-teal-50 border-teal-200 dark:text-teal-400 dark:bg-teal-500/10 dark:border-teal-500/20 relative z-10">
                        {item.tag}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 4: ATS Optimizer */}
          <div className="step-3d-card flex flex-col gap-16 md:flex-row-reverse items-center justify-between w-full">
            <div className="flex-1 space-y-6">
              <span className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400">ATS Optimizer</span>
              <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.1]">
                Beat the bots. <br />
                <span className="font-serif italic font-normal tracking-normal text-[1.05em] text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-emerald-500 dark:from-teal-400 dark:to-emerald-400 inline-block mt-1">Impress the humans.</span>
              </h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Over 75% of resumes are filtered before a human ever sees them. We show you exactly which keywords you're missing and where to add them naturally.
              </p>
              <div className="flex items-center gap-3 text-sm font-semibold text-slate-700 dark:text-slate-300 pt-2">
                <Target className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                Trained on 2M+ real job descriptions
              </div>
            </div>
            <div className="flex-1 w-full perspective-1000">
              <div className="bg-white dark:bg-[#0B1120] rounded-2xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl dark:shadow-[0_0_50px_-12px_rgba(20,184,166,0.15)]" style={{ transform: "rotateY(5deg) rotateX(2deg)" }}>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white">ATS Keyword Report</h3>
                  <span className="text-xs font-bold px-3 py-1 bg-teal-100 dark:bg-teal-500/20 text-teal-700 dark:text-teal-400 rounded-full border border-teal-200 dark:border-teal-500/30">44% match</span>
                </div>

                <div className="flex flex-wrap gap-2.5 mb-8">
                  {[
                    { word: 'distributed systems', has: false },
                    { word: 'microservices', has: true },
                    { word: 'kubernetes', has: false },
                    { word: 'REST APIs', has: true },
                    { word: 'CI/CD pipelines', has: true },
                    { word: 'system design', has: false },
                    { word: 'data modeling', has: false },
                    { word: 'cloud architecture', has: true }
                  ].map((kw, i) => (
                    <div key={i} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${kw.has ? 'bg-teal-50 dark:bg-teal-500/10 text-teal-700 dark:text-teal-400 border-teal-200 dark:border-teal-500/20' : 'bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700'}`}>
                      {kw.has ? <span className="text-[10px]">✓</span> : <span className="text-[10px]">✕</span>}
                      {kw.word}
                    </div>
                  ))}
                </div>

                <div className="bg-slate-50 dark:bg-[#0F172A] rounded-xl p-5 border border-slate-200 dark:border-slate-800 border-dashed">
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400 mb-3">AI Suggestion</h4>
                  <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                    Add <span className="text-slate-900 dark:text-white font-semibold">"distributed systems"</span> to your second bullet under <span className="text-slate-900 dark:text-white font-semibold">Staff Engineer @ Acme</span> — this keyword appears in <span className="text-teal-600 dark:text-teal-400 font-bold">83% of target JDs.</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer padding */}
        <div className="h-32" />
      </div>
    </main>
  );
}
