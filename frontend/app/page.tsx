"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useGsapReveal } from "@/animations/use-gsap-reveal";
import { useParallax } from "@/animations/use-parallax";
import { StatCounter } from "@/components/stat-counter";

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
  }, []);

  return (
    <main>
      <Navbar />
      <section ref={heroRef} className="mx-auto grid min-h-[88vh] max-w-6xl place-items-center px-4 py-20 text-center">
        <div className="space-y-8">
          <p className="subhead inline-flex rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            Premium AI Career Intelligence
          </p>
          <h1 className="headline text-balance text-4xl font-semibold leading-tight md:text-6xl">
            Analyze your resume. Reveal skill gaps. Build a roadmap to your target role.
          </h1>
          <p className="subhead mx-auto max-w-2xl text-lg text-muted-foreground">
            Resume Analyzer delivers deep AI-powered matching, strengths detection, and actionable upskilling plans with a modern enterprise-grade experience.
          </p>
          <div className="hero-cta flex flex-wrap items-center justify-center gap-3">
            <Link href="/login"><Button className="px-6 py-5">Start Free Analysis</Button></Link>
            <Link href="/dashboard"><Button variant="secondary" className="px-6 py-5">View Demo Dashboard</Button></Link>
          </div>
          <div className="mx-auto grid max-w-xl grid-cols-3 gap-6 pt-6 text-sm">
            <div className="reveal"><p className="text-2xl font-semibold"><StatCounter target={98} suffix="%" /></p><p className="text-muted-foreground">Parsing Accuracy</p></div>
            <div className="reveal"><p className="text-2xl font-semibold"><StatCounter target={12000} suffix="+" /></p><p className="text-muted-foreground">Profiles Analyzed</p></div>
            <div className="reveal"><p className="text-2xl font-semibold"><StatCounter target={4} suffix="x" /></p><p className="text-muted-foreground">Faster Screening</p></div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20">
        <div className="grid gap-5 md:grid-cols-2">
          {features.map((item) => (
            <Card key={item} className="reveal parallax">
              <p className="font-medium">{item}</p>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
