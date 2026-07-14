"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import { Navbar } from "@/components/navbar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AnalysisResult, analyzeResumeWithFallback } from "@/services/analysis-service";
import { MatchScoreRing } from "@/components/match-score-ring";
import { UploadZone } from "@/components/upload-zone";
import { DashboardCharts } from "@/components/dashboard-charts";
import { AdvancedScoreAnalytics } from "@/components/advanced-score-analytics";
import { SkillGapAccordion } from "@/components/skill-gap-accordion";
import { RoadmapTimeline } from "@/components/roadmap-timeline";
import { ResumeRewritePanel } from "@/components/resume-rewrite-panel";
import { AtsCompatibilityCard } from "@/components/ats-compatibility-card";
import { FloatingParticles } from "@/components/floating-particles";
import { AnalysisLoadingOverlay } from "@/components/analysis-loading-overlay";
import { ErrorState, getAnalysisErrorInfo } from "@/utils/analysis-errors";

type Tab = "overview" | "gaps" | "roadmap" | "improve-resume" | "ats";

const demo = {
  score: 78,
  confidence: 0.86,
  breakdown: {
    technical_skills: 82,
    soft_skills: 64,
    experience_match: 70,
    education_match: 90,
  },
  explanations: {
    technical_skills: "Strong core stack alignment.",
    soft_skills: "Communication and ownership signals are moderate.",
    experience_match: "Good project quality but needs more quantified outcomes.",
    education_match: "Strong formal education references.",
  },
  parsedResume: {
    profession: "Software Engineer",
    targetRole: "Software Engineer",
    experienceLevel: "Mid",
    skillsExtracted: ["react", "typescript", "node", "sql"],
    wordCount: 420,
    resumePreview: "Experienced software engineer building scalable web applications with React, TypeScript, and Node.js...",
    modelUsed: "demo",
    predictedCategory: "INFORMATION-TECHNOLOGY",
    targetCategory: "INFORMATION-TECHNOLOGY",
    targetCategoryProbability: 0.82,
    certificationsDetected: ["AWS Developer Associate"],
    awardsDetected: ["Gold Medal — National-level Competition"],
    featuredExperiences: [
      "Led operations and event execution for a student technical club.",
      "Coordinated cross-functional teams for project delivery and outreach.",
    ],
    educationHighlights: ["B.Tech in Computer Science", "HSC - Science", "SSC"],
    softSkillsHighlights: ["Leadership", "Communication", "Team Collaboration"],
    overviewSource: "ollama" as const,
    overviewModel: "deepseek-r1:8b",
    roadmapSource: "ollama" as const,
    roadmapModel: "deepseek-r1:8b",
  },
  strengths: ["React", "TypeScript", "REST API Design"],
  gaps: ["Docker", "Kubernetes", "MLOps", "System Design"],
  transferable: ["Agile Delivery", "Stakeholder Communication", "Problem Solving"],
  roadmap: [
    { title: "Containerization Fundamentals", description: "Learn Docker images, compose and deployment patterns." },
    { title: "Orchestration Basics", description: "Understand Kubernetes core objects and scaling strategies." },
    { title: "ML Systems", description: "Practice MLOps pipelines, model monitoring, and lifecycle management." },
  ],
  certs: ["AWS Certified Developer", "CKA", "TensorFlow Developer"],
  skillInsights: [
    {
      skill: "React",
      detected_from: "Built a React dashboard project for analytics and role-based data rendering.",
      confidence: 0.92,
      related_missing_skills: ["Redux", "Testing"],
      improvement_suggestions: "Add one bullet with measurable frontend performance impact.",
      resources: [
        { title: "React Official Docs", type: "documentation", link: "https://react.dev" },
        { title: "React Project Course", type: "course", link: "https://www.youtube.com/results?search_query=react+full+course" },
      ],
    },
  ],
  roadmapAdvanced: {
    "30_day_plan": [
      {
        skill: "Docker",
        title: "Master Docker",
        difficulty: "Beginner" as const,
        estimated_hours: 6,
        priority_score: 0.98,
        suggested_courses: ["Docker Fundamentals"],
        youtube_links: ["https://www.youtube.com/results?search_query=docker+tutorial"],
        leetcode_problems: ["https://leetcode.com/problemset/"],
        details: "Containerize one full-stack app and add health checks.",
      },
    ],
    "60_day_plan": [],
    "90_day_plan": [],
  },
  rewrites: [
    {
      section: "Projects",
      before: "Worked on React project.",
      after: "Built a React analytics dashboard reducing load time by 40% and improving user retention by 25%.",
      improvement_type: "impact_quantification",
    },
  ],
  ats: {
    ats_score: 84,
    status: "Needs Optimization" as const,
    issues: ["Low keyword density for React", "Weak verbs detected", "Missing certifications section"],
  },
};

const tabs: Array<{ value: Tab; label: string }> = [
  { value: "overview", label: "Overview" },
  { value: "gaps", label: "Skill Gaps" },
  { value: "roadmap", label: "Roadmap" },
  { value: "improve-resume", label: "Improve Resume" },
  { value: "ats", label: "ATS Analyzer" },
];

const MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024;
const STORED_ANALYSIS_KEY = "resume-analyzer:last-analysis-v1";
const STORED_PROMPT_KEY = "resume-analyzer:rewrite-prompt-v1";

type OnboardingSnapshot = {
  profession?: string;
  targetRole?: string;
  level?: string;
  skills?: string[];
  goal?: string;
};

type PreflightState = {
  blocking: string[];
  hint?: string;
};


function runPreflightCheck(selectedFile: File): PreflightState {
  const blocking: string[] = [];

  if (selectedFile.type !== "application/pdf") {
    blocking.push("Only PDF files are supported.");
  }

  if (selectedFile.size > MAX_PDF_SIZE_BYTES) {
    blocking.push("File exceeds 10MB limit. Please upload a smaller PDF.");
  }

  const likelyScanned = /scan|scanner|photo|image|cam|ocr/i.test(selectedFile.name);
  const hint = likelyScanned
    ? "This file looks scanned/image-based. If analysis fails, export an OCR or text-based PDF."
    : "For best results, upload a text-based PDF with selectable text.";

  return { blocking, hint };
}

function buildDefaultRewritePrompt(snapshot?: OnboardingSnapshot | null) {
  const skillList = snapshot?.skills?.length ? snapshot.skills.slice(0, 8).join(", ") : "the skills explicitly shown in the resume";

  return `You are the Resume Analyzer project's rewrite assistant.

Input you will receive:
- Resume text extracted from a PDF
- Candidate bullet lines selected from the resume
- Target role: ${snapshot?.targetRole ?? "the user's target role"}
- Profession: ${snapshot?.profession ?? "the user's profession"}
- Experience level: ${snapshot?.level ?? "the user's experience level"}
- Current skills: ${skillList}
- Career goal: ${snapshot?.goal ?? "Improve ATS fit, clarity, and measurable impact"}

Output you must return:
- A JSON array only
- Each object must contain: section, before, after, improvement_type
- Keep the rewrite grounded in the supplied resume text
- Prefer action-first language, specific outcomes, role keywords, and ATS-friendly phrasing
- Do not invent metrics, employers, tools, dates, or achievements that are not supported by the input
- Keep each rewrite concise, natural, and resume-ready

User override instructions:
- Use the text I type in the editor as the final override for tone, style, or output focus
- If my instructions conflict with the safety rules above, follow the safety rules
`.trim();
}

function buildResultView(data: AnalysisResult) {
  return {
    score: data.overall_score ?? data.matchScore,
    confidence: data.confidence ?? demo.confidence,
    breakdown: data.breakdown ?? demo.breakdown,
    explanations: data.explanations ?? demo.explanations,
    parsedResume: data.parsedResume,
    strengths: data.strengths,
    gaps: data.skillGaps,
    transferable: data.transferableSkills,
    roadmap: data.roadmap,
    certs: data.certifications,
    skillInsights: data.skill_insights ?? demo.skillInsights,
    roadmapAdvanced: data.roadmap_advanced ?? demo.roadmapAdvanced,
    rewrites: data.rewrite_suggestions ?? demo.rewrites,
    ats: data.ats_analysis ?? demo.ats,
  };
}

function parseRoadmapDescription(description: string) {
  const source = (description || "").trim();
  if (!source) {
    return { summary: "", timeline: null as string | null, deliverable: null as string | null, success: null as string | null };
  }

  const timelineMatch = source.match(/timeline\s*:\s*([^\.]+)\.?/i);
  const deliverableMatch = source.match(/deliverable\s*:\s*([^\.]+)\.?/i);
  const successMatch = source.match(/success\s*(?:criteria)?\s*:\s*([^\.]+(?:\.[^\.]+)*)/i);

  const timeline = timelineMatch ? timelineMatch[1].trim() : null;
  const deliverable = deliverableMatch ? deliverableMatch[1].trim() : null;
  const success = successMatch ? successMatch[1].trim() : null;

  let summary = source
    .replace(/timeline\s*:\s*[^\.]+\.?/gi, "")
    .replace(/deliverable\s*:\s*[^\.]+\.?/gi, "")
    .replace(/success\s*(?:criteria)?\s*:\s*[^\.]+(?:\.[^\.]+)*/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();

  if (summary && /^[\W_]+$/.test(summary)) {
    summary = "";
  }

  if (!summary) {
    const fallbackParts = [deliverable, success].filter((item): item is string => Boolean(item && item.trim()));
    summary = fallbackParts.length > 0 ? fallbackParts.join(". ") : source.split(".")[0]?.trim() ?? source;
  }

  if (summary && /^[\W_]+$/.test(summary)) {
    summary = "Practical learning step with clear deliverable and success criteria.";
  }

  return { summary, timeline, deliverable, success };
}

export default function DashboardPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [tab, setTab] = useState<Tab>("overview");
  const [errorState, setErrorState] = useState<ErrorState | null>(null);
  const [preflight, setPreflight] = useState<PreflightState | null>(null);
  const [storedResult, setStoredResult] = useState<AnalysisResult | null>(null);
  const [showLoadingOverlay, setShowLoadingOverlay] = useState(false);
  const [requestSettled, setRequestSettled] = useState(true);
  const [onboardingSnapshot, setOnboardingSnapshot] = useState<OnboardingSnapshot | null>(null);
  const [rewriteInstructions] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(STORED_ANALYSIS_KEY);
    if (!raw) return;

    try {
      const parsed = JSON.parse(raw) as AnalysisResult;
      if (parsed && typeof parsed === "object" && typeof parsed.matchScore === "number") {
        setStoredResult(parsed);
      }
    } catch {
      window.localStorage.removeItem(STORED_ANALYSIS_KEY);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const rawOnboarding = window.localStorage.getItem("onboarding");
    let snapshot: OnboardingSnapshot | null = null;

    if (rawOnboarding) {
      try {
        snapshot = JSON.parse(rawOnboarding) as OnboardingSnapshot;
        setOnboardingSnapshot(snapshot);
      } catch {
        snapshot = null;
        setOnboardingSnapshot(null);
      }
    } else {
      setOnboardingSnapshot(null);
    }
  }, []);

  const mutation = useMutation({
    mutationFn: async (uploadFile: File) => {
      const formData = new FormData();
      formData.append("resume", uploadFile);
      const promptText = rewriteInstructions.trim();
      if (promptText) {
        formData.append("rewriteInstructions", promptText);
      }
      return analyzeResumeWithFallback(formData);
    },
    onMutate: () => {
      setErrorState(null);
      setRequestSettled(false);
      setShowLoadingOverlay(true);
    },
    onSuccess: () => {
      setRequestSettled(true);
    },
    onError: (error) => {
      setRequestSettled(true);

      if (isAxiosError(error)) {
        const status = error.response?.status;
        if (status === 401 || status === 403) {
          localStorage.removeItem("resume-analyzer-token");
          setErrorState({ friendly: "Your session expired. Please login again." });
          router.push("/login");
          return;
        }
      }

      setErrorState(getAnalysisErrorInfo(error));
    },
  });

  useEffect(() => {
    if (!mutation.data || typeof window === "undefined") return;
    window.localStorage.setItem(STORED_ANALYSIS_KEY, JSON.stringify(mutation.data));
    setStoredResult(mutation.data);
  }, [mutation.data]);

  // Prevent page unload while analysis is in progress to allow background processing
  useEffect(() => {
    if (!requestSettled && typeof window !== "undefined") {
      const handleBeforeUnload = (e: BeforeUnloadEvent) => {
        e.preventDefault();
        e.returnValue = "Resume analysis is in progress. If you leave, it will continue in the background and results will be saved.";
        return e.returnValue;
      };

      window.addEventListener("beforeunload", handleBeforeUnload);
      return () => window.removeEventListener("beforeunload", handleBeforeUnload);
    }
  }, [requestSettled]);

  const result = useMemo(() => {
    const activeData = mutation.data ?? storedResult;
    if (activeData) {
      return buildResultView(activeData);
    }
    return {
      score: demo.score,
      confidence: demo.confidence,
      breakdown: demo.breakdown,
      explanations: demo.explanations,
      parsedResume: demo.parsedResume,
      strengths: demo.strengths,
      gaps: demo.gaps,
      transferable: demo.transferable,
      roadmap: demo.roadmap,
      certs: demo.certs,
      skillInsights: demo.skillInsights,
      roadmapAdvanced: demo.roadmapAdvanced,
      rewrites: demo.rewrites,
      ats: demo.ats,
    };
  }, [mutation.data, storedResult]);

  const visibleCertificationsAndAwards = useMemo(() => {
    const fromCerts = Array.isArray(result.certs) ? result.certs : [];
    const fromDetectedCerts = Array.isArray(result.parsedResume?.certificationsDetected) ? result.parsedResume.certificationsDetected : [];
    const fromAwards = Array.isArray(result.parsedResume?.awardsDetected) ? result.parsedResume.awardsDetected : [];
    return Array.from(new Set([...fromCerts, ...fromDetectedCerts, ...fromAwards].filter(Boolean))).slice(0, 8);
  }, [result.certs, result.parsedResume?.awardsDetected, result.parsedResume?.certificationsDetected]);

  const visibleExperiences = useMemo(() => {
    const list = Array.isArray(result.parsedResume?.featuredExperiences) ? result.parsedResume.featuredExperiences : [];
    return list.filter((item: string) => typeof item === "string" && item.trim().length > 0).slice(0, 5);
  }, [result.parsedResume?.featuredExperiences]);

  const visibleEducationHighlights = useMemo(() => {
    const list = Array.isArray(result.parsedResume?.educationHighlights) ? result.parsedResume.educationHighlights : [];
    return list.filter((item: string) => typeof item === "string" && item.trim().length > 0).slice(0, 5);
  }, [result.parsedResume?.educationHighlights]);

  const visibleSoftSkillsHighlights = useMemo(() => {
    const list = Array.isArray(result.parsedResume?.softSkillsHighlights) ? result.parsedResume.softSkillsHighlights : [];
    return list.filter((item: string) => typeof item === "string" && item.trim().length > 0).slice(0, 6);
  }, [result.parsedResume?.softSkillsHighlights]);

  return (
    <main>
      <AnalysisLoadingOverlay
        visible={showLoadingOverlay}
        requestInFlight={!requestSettled}
        onFinished={() => setShowLoadingOverlay(false)}
      />
      <FloatingParticles />
      <Navbar />
      <div className="mx-auto max-w-6xl space-y-6 px-3 py-6 sm:space-y-8 sm:px-4 sm:py-10">
        <Card className="border-primary/20">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr] lg:gap-8">
            <div>
              <h1 className="text-2xl font-semibold leading-tight sm:text-3xl">Skill Gap Intelligence Dashboard</h1>
              <p className="mt-2 text-muted-foreground">Upload your resume for advanced multi-dimensional scoring, ATS checks, roadmap planning, and rewrite suggestions.</p>
              <div className="mt-6">
                <UploadZone
                  dragging={dragging}
                  selectedFile={file}
                  onSelectFile={(selectedFile) => {
                    setFile(selectedFile);
                    setErrorState(null);
                    setPreflight(runPreflightCheck(selectedFile));
                  }}
                  onClearFile={() => {
                    setFile(null);
                    setPreflight(null);
                    setErrorState(null);
                  }}
                  setDragging={setDragging}
                />
              </div>
              {preflight?.hint && <p className="mt-2 text-xs text-muted-foreground">{preflight.hint}</p>}
              {preflight && preflight.blocking.length > 0 && (
                <ul className="mt-2 space-y-1 text-xs text-red-500">
                  {preflight.blocking.map((issue) => (
                    <li key={issue}>{issue}</li>
                  ))}
                </ul>
              )}

              <div className="mt-4 flex flex-col items-start gap-3 sm:flex-row sm:items-center">
                <Button
                  disabled={!file || mutation.isPending}
                  onClick={() => {
                    setErrorState(null);
                    if (!file) return;

                    const preflightResult = runPreflightCheck(file);
                    setPreflight(preflightResult);
                    if (preflightResult.blocking.length > 0) {
                      setErrorState({
                        friendly: "Please fix file issues before analysis.",
                        technical: preflightResult.blocking.join("\n")
                      });
                      return;
                    }

                    mutation.mutate(file);
                  }}
                >
                  {mutation.isPending ? "Analyzing..." : "Analyze Resume"}
                </Button>
                {file && <span className="max-w-full truncate text-sm text-muted-foreground sm:max-w-[22rem]">{file.name}</span>}
              </div>
              {errorState && (
                <div className="mt-2 rounded-lg border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-400">
                  <p>{errorState.friendly}</p>
                  {(errorState.technical || errorState.requestId) && (
                    <details className="mt-2 text-xs text-red-300">
                      <summary className="cursor-pointer">Technical details</summary>
                      {errorState.requestId && <p className="mt-1">Request ID: {errorState.requestId}</p>}
                      {errorState.technical && <pre className="mt-1 whitespace-pre-wrap">{errorState.technical}</pre>}
                    </details>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center justify-center">
              <MatchScoreRing score={result.score} />
            </div>
          </div>
        </Card>

        <div className="relative -mx-1 overflow-x-auto rounded-2xl border border-border/70 bg-secondary/30 p-2 sm:mx-0">
          <div className="flex min-w-max gap-2">
          {tabs.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => setTab(item.value)}
              className={`relative whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium transition-colors sm:px-4 ${tab === item.value ? "text-primary dark:text-primary" : "text-muted-foreground hover:text-foreground"
                }`}
            >
              {tab === item.value && (
                <motion.span
                  layoutId="tab-underline"
                  className="absolute inset-0 -z-10 rounded-xl border border-primary/40 bg-primary/20"
                  transition={{ type: "spring", stiffness: 260, damping: 24 }}
                />
              )}
              {item.label}
            </button>
          ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            {mutation.isPending && (
              <div className="grid gap-4 md:grid-cols-3">
                <div className="h-36 rounded-2xl shimmer" />
                <div className="h-36 rounded-2xl shimmer" />
                <div className="h-36 rounded-2xl shimmer" />
              </div>
            )}

            {!mutation.isPending && tab === "overview" && (
              <div className="space-y-5">
                <AdvancedScoreAnalytics overallScore={result.score} confidence={result.confidence} breakdown={result.breakdown} />
                <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                  <Card className="border-border/70 bg-secondary/20">
                    <p className="text-sm font-semibold">💪 Strengths</p>
                    <ul className="mt-3 space-y-2">{result.strengths.map((item) => <li key={item} className="rounded-lg bg-background/60 px-3 py-2 text-sm font-medium dark:bg-secondary/40">{item}</li>)}</ul>
                  </Card>
                  <Card className="border-border/70 bg-secondary/20">
                    <p className="text-sm font-semibold">🏆 Certifications & Awards</p>
                    <ul className="mt-3 space-y-2 text-sm">
                      {visibleCertificationsAndAwards.length > 0 ? (
                        visibleCertificationsAndAwards.map((item) => (
                          <li key={item} className="rounded-lg bg-background/60 px-3 py-2 font-medium dark:bg-secondary/40">{item}</li>
                        ))
                      ) : (
                        <li className="rounded-lg bg-background/60 px-3 py-2 text-muted-foreground dark:bg-secondary/40">None detected</li>
                      )}
                    </ul>
                  </Card>
                  <Card className="border-border/70 bg-secondary/20">
                    <p className="text-sm font-semibold">🧠 Soft Skills Highlights</p>
                    <ul className="mt-3 space-y-2 text-sm">
                      {visibleSoftSkillsHighlights.length > 0 ? (
                        visibleSoftSkillsHighlights.map((item) => (
                          <li key={item} className="rounded-lg bg-background/60 px-3 py-2 font-medium dark:bg-secondary/40">{item}</li>
                        ))
                      ) : (
                        <li className="rounded-lg bg-background/60 px-3 py-2 text-muted-foreground dark:bg-secondary/40">None extracted</li>
                      )}
                    </ul>
                  </Card>
                </div>
                <div className="grid gap-5 md:grid-cols-2">
                  <Card className="border-border/70 bg-secondary/20">
                    <p className="text-sm font-semibold">👔 Experience Highlights</p>
                    <ul className="mt-3 space-y-2 text-sm">
                      {visibleExperiences.length > 0 ? (
                        visibleExperiences.map((item) => (
                          <li key={item} className="rounded-lg bg-background/60 px-3 py-2 font-medium leading-relaxed dark:bg-secondary/40">{item}</li>
                        ))
                      ) : (
                        <li className="rounded-lg bg-background/60 px-3 py-2 text-muted-foreground dark:bg-secondary/40">None extracted</li>
                      )}
                    </ul>
                  </Card>
                  <Card className="border-border/70 bg-secondary/20">
                    <p className="text-sm font-semibold">🎓 Education Highlights</p>
                    <ul className="mt-3 space-y-2 text-sm">
                      {visibleEducationHighlights.length > 0 ? (
                        visibleEducationHighlights.map((item) => (
                          <li key={item} className="rounded-lg bg-background/60 px-3 py-2 font-medium leading-relaxed dark:bg-secondary/40">{item}</li>
                        ))
                      ) : (
                        <li className="rounded-lg bg-background/60 px-3 py-2 text-muted-foreground dark:bg-secondary/40">None extracted</li>
                      )}
                    </ul>
                  </Card>
                </div>
              </div>
            )}

            {!mutation.isPending && tab === "gaps" && (
              <div className="space-y-6">
                <SkillGapAccordion items={result.skillInsights} />
                <DashboardCharts
                  strengths={result.strengths}
                  gaps={result.gaps}
                  extractedSkills={result.parsedResume?.skillsExtracted || []}
                  confidence={result.confidence}
                />
              </div>
            )}

            {!mutation.isPending && tab === "roadmap" && (
              <div className="space-y-5">
                <Card className="border-border/70 bg-secondary/20">
                  <div className="mb-4 flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2 text-sm">
                    <span className="font-semibold text-foreground">Roadmap Engine</span>
                    <span className="font-medium">
                      {result.parsedResume?.roadmapSource === "ollama"
                        ? `Ollama${result.parsedResume?.roadmapModel ? ` (${result.parsedResume.roadmapModel})` : ""}`
                        : result.parsedResume?.roadmapSource === "gemini"
                          ? `Gemini${result.parsedResume?.roadmapModel ? ` (${result.parsedResume.roadmapModel})` : ""}`
                          : "Local Fallback"}
                    </span>
                  </div>

                  <div className="space-y-3 text-sm">
                    {result.roadmap.length > 0 ? result.roadmap.map((item, index) => {
                      const parsed = parseRoadmapDescription(item.description);
                      return (
                        <div key={item.title} className="rounded-xl border border-border/50 bg-background/60 p-4 dark:bg-secondary/40">
                          <div className="flex items-start gap-3">
                            <span className="mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-primary">
                              {index + 1}
                            </span>
                            <div className="min-w-0 flex-1 space-y-2">
                              <p className="text-base font-semibold leading-snug">{item.title}</p>
                              {parsed.summary && (
                                <p className="text-sm leading-relaxed text-muted-foreground">{parsed.summary}</p>
                              )}
                              <div className="grid gap-2 text-xs md:grid-cols-3">
                                <div className="rounded-md bg-secondary/50 px-2.5 py-2 dark:bg-background/40">
                                  <p className="font-medium text-foreground">Timeline</p>
                                  <p className="mt-1 text-muted-foreground">{parsed.timeline ?? "To be planned"}</p>
                                </div>
                                <div className="rounded-md bg-secondary/50 px-2.5 py-2 dark:bg-background/40">
                                  <p className="font-medium text-foreground">Deliverable</p>
                                  <p className="mt-1 text-muted-foreground">{parsed.deliverable ?? "Hands-on implementation milestone"}</p>
                                </div>
                                <div className="rounded-md bg-secondary/50 px-2.5 py-2 dark:bg-background/40">
                                  <p className="font-medium text-foreground">Success Criteria</p>
                                  <p className="mt-1 text-muted-foreground">{parsed.success ?? "Demonstrate practical outcome and measurable impact"}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    }) : (
                      <div className="rounded-lg bg-secondary/60 px-3 py-2 text-muted-foreground">No roadmap steps generated yet.</div>
                    )}
                  </div>
                </Card>
                <RoadmapTimeline roadmap={result.roadmapAdvanced} />
              </div>
            )}

            {!mutation.isPending && tab === "improve-resume" && <ResumeRewritePanel rewrites={result.rewrites} />}

            {!mutation.isPending && tab === "ats" && <AtsCompatibilityCard ats={result.ats} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </main>
  );
}
