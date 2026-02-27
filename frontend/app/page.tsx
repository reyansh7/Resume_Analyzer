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
  useGsapReveal(".reveal");
  useParallax(".parallax", 70);

  useEffect(() => {
    if (!heroRef.current) return;

    const timeline = gsap.timeline();
    timeline
      .fromTo(".headline", { y: 32, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "power3.out" })
      .fromTo(".subhead", { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, "-=0.35")
      .fromTo(".hero-cta", { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 }, "-=0.3");

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
          }
        }
      );
    });
  }, []);

  return (
    <main className="relative overflow-hidden bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-50">
      {/* Animated background boxes */}
      <div className="fixed inset-0 z-0 overflow-hidden">
        <Boxes />
        <div className="pointer-events-none absolute inset-0 z-10 bg-slate-50 dark:bg-slate-950 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />
      </div>

      {/* Page content above background — pointer-events-none lets hover pass through to boxes */}
      <div className="pointer-events-none relative z-20">
        <div className="pointer-events-auto"><Navbar /></div>
        <section ref={heroRef} className="mx-auto grid min-h-[88vh] max-w-6xl place-items-center px-4 py-20 text-center">
          <div className="space-y-8">
            <p className="subhead inline-flex rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary">
              Premium AI Career Intelligence
            </p>
            <h1 className="headline text-balance text-4xl font-semibold leading-tight md:text-7xl">
              Analyze your resume. Reveal skill gaps.<br />
              <span className="bg-gradient-to-r from-blue-600 to-emerald-500 dark:from-blue-400 dark:to-emerald-400 bg-clip-text text-transparent">Build a roadmap.</span>
            </h1>
            <p className="subhead mx-auto max-w-2xl text-lg text-slate-600 dark:text-slate-400">
              Resume Analyzer delivers deep AI-powered matching, strengths detection, and actionable upskilling plans with a modern enterprise-grade experience.
            </p>
            <div className="hero-cta pointer-events-auto flex flex-wrap items-center justify-center gap-3">
              <Link href="/login"><Button className="rounded-full px-8 py-6 text-base shadow-lg shadow-primary/20 transition-all hover:scale-105">Start Free Analysis</Button></Link>
              <Link href="/dashboard"><Button variant="secondary" className="rounded-full px-8 py-6 text-base transition-all hover:scale-105">View Demo</Button></Link>
            </div>
            <div className="mx-auto grid max-w-xl grid-cols-3 gap-6 pt-12 text-sm">
              <div className="reveal"><p className="text-3xl font-semibold text-slate-800 dark:text-slate-200"><StatCounter target={98} suffix="%" /></p><p className="mt-1 text-slate-600 dark:text-slate-500">Parsing Accuracy</p></div>
              <div className="reveal"><p className="text-3xl font-semibold text-slate-800 dark:text-slate-200"><StatCounter target={12000} suffix="+" /></p><p className="mt-1 text-slate-600 dark:text-slate-500">Profiles Analyzed</p></div>
              <div className="reveal"><p className="text-3xl font-semibold text-slate-800 dark:text-slate-200"><StatCounter target={4} suffix="x" /></p><p className="mt-1 text-slate-600 dark:text-slate-500">Faster Screening</p></div>
            </div>
          </div>
        </section>

        {/* 4 New Sections with 3D Reveal */}
        <section className="relative mx-auto max-w-5xl space-y-32 px-4 py-24">

          {/* Section 1: What does my app do? */}
          <div className="step-3d-card flex flex-col items-center gap-12 md:flex-row pointer-events-auto">
            <div className="flex-1 space-y-6">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
                <BrainCircuit className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Intelligent Career<br />Acceleration</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Our application isn't just a parser—it's your AI career coach. By analyzing millions of data points across global job descriptions, we understand exactly what the market demands for your dream role.
              </p>
            </div>
            <div className="flex-1">
              <Card className="relative overflow-hidden border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/50 p-8 backdrop-blur-xl">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />
                <h3 className="mb-4 text-xl font-semibold text-slate-800 dark:text-slate-200">Our Core Capabilities</h3>
                <ul className="space-y-4">
                  {features.map((feature, idx) => (
                    <li key={idx} className="flex items-center text-slate-600 dark:text-slate-400">
                      <ArrowRight className="mr-3 h-4 w-4 text-blue-500 dark:text-blue-400" />
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
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400">
                <UserPlus className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Start With Your<br />Ambitions</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                Sign up in seconds and tell us where you're headed. Answer a few targeted questions about your current stack, your dream company, and your ideal role to set the foundation.
              </p>
            </div>
            <div className="flex-1">
              <Card className="relative overflow-hidden border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/50 p-8 backdrop-blur-xl">
                <div className="absolute -left-20 -top-20 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="h-2 w-1/3 rounded-full bg-slate-300 dark:bg-slate-800" />
                    <div className="h-10 w-full rounded-lg border border-slate-200 bg-slate-100/50 dark:border-slate-800 dark:bg-slate-950/50" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-2 w-1/4 rounded-full bg-slate-300 dark:bg-slate-800" />
                    <div className="h-10 w-full rounded-lg border border-slate-200 bg-slate-100/50 dark:border-slate-800 dark:bg-slate-950/50" />
                  </div>
                  <Button className="w-full bg-emerald-100 text-emerald-600 hover:bg-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-400 dark:hover:bg-emerald-500/30">Continue to Upload</Button>
                </div>
              </Card>
            </div>
          </div>

          {/* Section 3: Put your resume */}
          <div className="step-3d-card flex flex-col items-center gap-12 md:flex-row pointer-events-auto">
            <div className="flex-1 space-y-6">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-100 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400">
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
                  <div className="h-48 w-48 rounded-full bg-purple-500/5 blur-3xl" />
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
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-100 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400">
                <Target className="h-8 w-8" />
              </div>
              <h2 className="text-3xl font-bold tracking-tight md:text-5xl">Your Personalized<br />Master Plan</h2>
              <p className="text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                We'll highlight your strongest assets, flag critical missing skills, and generate a week-by-week upskilling roadmap. Know exactly what courses to take and what projects to build next.
              </p>
            </div>
            <div className="flex-1">
              <Card className="relative overflow-hidden border-slate-200 bg-white/50 dark:border-slate-800 dark:bg-slate-900/50 p-8 backdrop-blur-xl">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl" />
                <div className="space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Match Score</span>
                    <span className="rounded-full bg-orange-100 px-3 py-1 text-sm text-orange-600 dark:bg-orange-500/20 dark:text-orange-400">Needs Work (62%)</span>
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
