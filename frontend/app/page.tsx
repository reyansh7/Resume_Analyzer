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
        <Boxes />
      </div>

      {/* Page content above background */}
      <div className="relative z-20">
        <div className="pointer-events-auto">
          <Navbar />
        </div>

        {/* NEW HERO SECTION - 2 COLUMN LAYOUT */}
        <section ref={heroRef} className="mx-auto max-w-7xl px-4 pt-4 pb-10 lg:pt-8 lg:pb-16">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-[1fr_500px] xl:grid-cols-[1fr_600px] lg:gap-12 items-center">

            {/* LEFT SIDE: Content */}
            <div ref={leftColRef} className="space-y-8 flex flex-col items-center text-center lg:items-start lg:text-left relative z-10 w-full">
              {/* Subtle radial glow */}
              <div className="absolute -left-20 top-0 h-[400px] w-[400px] rounded-full bg-white/40 dark:bg-teal-500/5 blur-[100px] -z-10 pointer-events-none" />

              <h1 className="hero-animate text-balance text-5xl font-bold leading-[1.1] tracking-tight text-slate-900 dark:text-slate-50 md:text-6xl lg:text-7xl">
                See your career the <br className="hidden lg:block" />
                <span className="text-primary font-serif italic font-normal tracking-normal text-[1.1em] leading-none block mt-2">
                  way recruiters do.
                </span>
              </h1>

              <p className="hero-animate max-w-xl text-lg text-slate-600 dark:text-slate-300 leading-relaxed font-medium">
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
            <div className="perspective-1200 pointer-events-none relative w-full max-w-[500px] mx-auto lg:max-w-none lg:mx-0 min-h-[450px]">
              {/* Decorative Elements around Mockup */}
              <div className="absolute -z-10 top-1/2 -right-12 h-64 w-64 rounded-full bg-teal-500/10 dark:bg-teal-500/20 blur-[80px]" />
              <div className="absolute -z-10 -bottom-12 -left-12 h-48 w-48 rounded-full bg-blue-500/5 dark:bg-blue-500/10 blur-[60px]" />

              {/* CARD 1: Main Browser Window */}
              <div
                ref={mockupRef}
                className="absolute left-0 top-0 w-full max-w-[460px] overflow-hidden rounded-2xl bg-[#FDFCFB] dark:bg-[#0F1629] p-2 flex flex-col will-change-transform"
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
                className="mockup-float-card absolute top-10 -right-6 lg:-right-12 w-[280px] bg-white dark:bg-[#151E32] rounded-2xl p-5 border border-slate-100 dark:border-slate-700 shadow-[0_30px_60px_-15px_rgba(15,23,42,0.15)] dark:shadow-[0_30px_60px_-15px_rgba(0,0,0,0.6)] transform-style-3d backdrop-blur-md"
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
          <div className="grid max-w-4xl grid-cols-1 sm:grid-cols-3 gap-8 pt-10 mx-auto text-center border-t border-slate-200/60 dark:border-slate-800/60 mt-12 relative z-10">
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
        <section className="relative mx-auto max-w-5xl space-y-32 px-4 py-24">

          {/* Section 1: What does my app do? */}
          <div className="step-3d-card flex flex-col items-center gap-12 md:flex-row pointer-events-auto">
            <div className="flex-1 space-y-6">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-100 text-teal-600 dark:bg-teal-500/10 dark:text-teal-400">
                <BrainCircuit className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Intelligent Career<br />Acceleration</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Our application isn't just a parser—it's your AI career coach. By analyzing millions of data points across global job descriptions, we understand exactly what the market demands for your dream role.
              </p>
            </div>
            <div className="flex-1">
              <Card className="relative overflow-hidden border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/50 p-8 backdrop-blur-xl">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-teal-500/10 blur-3xl" />
                <h3 className="mb-4 text-xl font-semibold text-slate-800 dark:text-slate-200">Our Core Capabilities</h3>
                <ul className="space-y-4">
                  {features.map((feature, idx) => (
                    <li key={idx} className="flex items-center text-slate-600 dark:text-slate-400">
                      <ArrowRight className="mr-3 h-4 w-4 text-teal-500 dark:text-teal-400" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </Card>
            </div>
          </div>

          {/* Section 2: Signup and answer questions */}
          <div className="step-3d-card flex flex-col items-center gap-12 md:flex-row-reverse pointer-events-auto">
            <div className="flex-1 space-y-6">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-100 text-teal-600 dark:bg-teal-500/10 dark:text-teal-400">
                <UserPlus className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Start With Your<br />Ambitions</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Sign up in seconds and tell us where you're headed. Answer a few targeted questions about your current stack, your dream company, and your ideal role to set the foundation.
              </p>
            </div>
            <div className="flex-1">
              <Card className="relative overflow-hidden border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/50 p-8 backdrop-blur-xl">
                <div className="absolute -left-20 -top-20 h-64 w-64 rounded-full bg-teal-500/10 blur-3xl" />
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="h-2 w-1/3 rounded-full bg-slate-300 dark:bg-slate-800" />
                    <div className="h-10 w-full rounded-lg border border-slate-200 bg-slate-100/50 dark:border-slate-800 dark:bg-slate-950/50" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-2 w-1/4 rounded-full bg-slate-300 dark:bg-slate-800" />
                    <div className="h-10 w-full rounded-lg border border-slate-200 bg-slate-100/50 dark:border-slate-800 dark:bg-slate-950/50" />
                  </div>
                  <Button className="w-full bg-teal-100 text-teal-600 hover:bg-teal-200 dark:bg-teal-500/20 dark:text-teal-400 dark:hover:bg-teal-500/30">Continue to Upload</Button>
                </div>
              </Card>
            </div>
          </div>

          {/* Section 3: Put your resume */}
          <div className="step-3d-card flex flex-col items-center gap-12 md:flex-row pointer-events-auto">
            <div className="flex-1 space-y-6">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-100 text-teal-600 dark:bg-teal-500/10 dark:text-teal-400">
                <FileText className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Drop Your Resume<br />In The Vault</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Upload your current resume (PDF or DOCX). Our proprietary NLP engine will instantly extract your experience, quantify your impact, and map your existing skills against industry standards.
              </p>
            </div>
            <div className="flex-1 pointer-events-auto">
              <Card className="relative overflow-hidden border-slate-300 dark:border-slate-800 border-dashed bg-slate-100/50 dark:bg-slate-900/20 p-12 text-center backdrop-blur-xl">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="h-48 w-48 rounded-full bg-teal-500/5 blur-3xl" />
                </div>
                <div className="relative z-10 flex flex-col items-center space-y-4">
                  <div className="rounded-full bg-slate-200 dark:bg-slate-800 p-4">
                    <FileText className="h-8 w-8 text-slate-600 dark:text-slate-400" />
                  </div>
                  <p className="text-slate-700 dark:text-slate-300">Drag & drop your resume here</p>
                  <p className="text-sm text-slate-500">Supports PDF, DOCX up to 10MB</p>
                  <Button variant="secondary" className="mt-4 border-slate-300 bg-white hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-50">Browse Files</Button>
                </div>
              </Card>
            </div>
          </div>

          {/* Section 4: Highlights & Roadmap */}
          <div className="step-3d-card flex flex-col items-center gap-12 md:flex-row-reverse pointer-events-auto">
            <div className="flex-1 space-y-6">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-100 text-teal-600 dark:bg-teal-500/10 dark:text-teal-400">
                <Target className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Your Personalized<br />Master Plan</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                We'll highlight your strongest assets, flag critical missing skills, and generate a week-by-week upskilling roadmap. Know exactly what courses to take and what projects to build next.
              </p>
            </div>
            <div className="flex-1">
              <Card className="relative overflow-hidden border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/50 p-8 backdrop-blur-xl">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-teal-500/10 blur-3xl" />
                <div className="space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Match Score</span>
                    <span className="rounded-full bg-teal-100 px-3 py-1 text-sm text-teal-600 dark:bg-teal-500/20 dark:text-teal-400">Needs Work (62%)</span>
                  </div>
                  <div>
                    <h4 className="mb-3 text-sm font-medium text-slate-600 dark:text-slate-400">Recommended Roadmap</h4>
                    <div className="space-y-3">
                      <div className="flex items-center gap-4 rounded-lg bg-slate-50/50 dark:bg-slate-950/50 p-3 shadow-inner">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300">W1</div>
                        <p className="text-sm text-slate-800 dark:text-slate-300">Master System Design Basics</p>
                      </div>
                      <div className="flex items-center gap-4 rounded-lg bg-slate-50/50 dark:bg-slate-950/50 p-3 shadow-inner">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300">W2</div>
                        <p className="text-sm text-slate-800 dark:text-slate-300">Learn Kubernetes Concepts</p>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>

        </section>

        {/* Footer padding */}
        <div className="h-32" />
      </div>
    </main>
  );
}
