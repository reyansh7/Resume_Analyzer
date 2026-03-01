"use client";

import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import { Navbar } from "@/components/navbar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { uploadResume, uploadResumeV2 } from "@/services/analysis-service";
import { MatchScoreRing } from "@/components/match-score-ring";
import { UploadZone } from "@/components/upload-zone";
import { DashboardCharts } from "@/components/dashboard-charts";
import { AdvancedScoreAnalytics } from "@/components/advanced-score-analytics";
import { SkillGapAccordion } from "@/components/skill-gap-accordion";
import { RoadmapTimeline } from "@/components/roadmap-timeline";
import { ResumeRewritePanel } from "@/components/resume-rewrite-panel";
import { AtsCompatibilityCard } from "@/components/ats-compatibility-card";
import { FloatingParticles } from "@/components/floating-particles";

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
    roadmapSource: "gemini" as const,
    roadmapModel: "gemini-2.0-flash",
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

  if (!summary) {
    summary = source.split(".")[0]?.trim() ?? source;
  }

  return { summary, timeline, deliverable, success };
}

export default function DashboardPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [tab, setTab] = useState<Tab>("overview");
  const [authError, setAuthError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async (uploadFile: File) => {
      const formData = new FormData();
      formData.append("resume", uploadFile);
      try {
        return await uploadResumeV2(formData);
      } catch (error) {
        if (isAxiosError(error)) {
          const status = error.response?.status;
          if (status === 401 || status === 403) {
            throw error;
          }

          if (!status) {
            throw error;
          }

          if (status !== 404 && status !== 405) {
            throw error;
          }
        }

        return uploadResume(formData);
      }
    },
    onError: (error) => {
      if (isAxiosError(error)) {
        const status = error.response?.status;
        if (status === 401 || status === 403) {
          localStorage.removeItem("resume-analyzer-token");
          setAuthError("Your session expired. Please login again.");
          router.push("/login");
          return;
        }

        if (error.code === "ERR_NETWORK") {
          setAuthError("Backend service is unreachable. Please start backend on port 8080 and ML on 8000.");
          return;
        }
      }

      setAuthError("Analysis failed. Please try again.");
    },
  });

  const result = useMemo(() => {
    if (mutation.data) {
      return {
        score: mutation.data.overall_score ?? mutation.data.matchScore,
        confidence: mutation.data.confidence ?? demo.confidence,
        breakdown: mutation.data.breakdown ?? demo.breakdown,
        explanations: mutation.data.explanations ?? demo.explanations,
        parsedResume: mutation.data.parsedResume,
        strengths: mutation.data.strengths,
        gaps: mutation.data.skillGaps,
        transferable: mutation.data.transferableSkills,
        roadmap: mutation.data.roadmap,
        certs: mutation.data.certifications,
        skillInsights: mutation.data.skill_insights ?? demo.skillInsights,
        roadmapAdvanced: mutation.data.roadmap_advanced ?? demo.roadmapAdvanced,
        rewrites: mutation.data.rewrite_suggestions ?? demo.rewrites,
        ats: mutation.data.ats_analysis ?? demo.ats,
      };
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
  }, [mutation.data]);

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

  return (
    <main>
      <FloatingParticles />
      <Navbar />
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10">
        <Card className="border-primary/20">
          <div className="grid gap-8 lg:grid-cols-[1.2fr_1fr]">
            <div>
              <h1 className="text-3xl font-semibold">Skill Gap Intelligence Dashboard</h1>
              <p className="mt-2 text-muted-foreground">Upload your resume for advanced multi-dimensional scoring, ATS checks, roadmap planning, and rewrite suggestions.</p>
              <div className="mt-6">
                <UploadZone dragging={dragging} selectedFile={file} onSelectFile={setFile} onClearFile={() => setFile(null)} setDragging={setDragging} />
              </div>
              <div className="mt-4 flex items-center gap-3">
                <Button
                  disabled={!file || mutation.isPending}
                  onClick={() => {
                    setAuthError(null);
                    if (file) mutation.mutate(file);
                  }}
                >
                  {mutation.isPending ? "Analyzing..." : "Analyze Resume"}
                </Button>
                {file && <span className="text-sm text-muted-foreground">{file.name}</span>}
              </div>
              {authError && <p className="mt-2 text-sm text-red-500">{authError}</p>}
            </div>
            <div className="flex items-center justify-center">
              <MatchScoreRing score={result.score} />
            </div>
          </div>
        </Card>

        <div className="relative flex flex-wrap gap-2 rounded-2xl border border-border/70 bg-secondary/30 p-2">
          {tabs.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => setTab(item.value)}
              className={`relative rounded-xl px-4 py-2 text-sm font-medium transition-colors ${tab === item.value ? "text-primary dark:text-primary" : "text-muted-foreground hover:text-foreground"
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
                    <p className="text-sm font-semibold">📋 Explanation Highlights</p>
                    <ul className="mt-3 space-y-2 text-xs">
                      <li className="rounded-lg bg-background/60 px-3 py-2 dark:bg-secondary/40"><span className="font-medium">Tech:</span> {result.explanations.technical_skills}</li>
                      <li className="rounded-lg bg-background/60 px-3 py-2 dark:bg-secondary/40"><span className="font-medium">Exp:</span> {result.explanations.experience_match}</li>
                      <li className="rounded-lg bg-background/60 px-3 py-2 dark:bg-secondary/40"><span className="font-medium">Soft:</span> {result.explanations.soft_skills}</li>
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
                    <p className="text-sm font-semibold">📊 Score Insights</p>
                    <div className="mt-3 space-y-3 text-xs">
                      <div className="rounded-lg bg-background/60 px-3 py-2 dark:bg-secondary/40">
                        <p className="font-medium">Technical Skills</p>
                        <p className="font-semibold text-primary">{Math.round(result.breakdown.technical_skills || 0)}%</p>
                      </div>
                      <div className="rounded-lg bg-background/60 px-3 py-2 dark:bg-secondary/40">
                        <p className="font-medium">Experience Match</p>
                        <p className="font-semibold text-primary">{Math.round(result.breakdown.experience_match || 0)}%</p>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {!mutation.isPending && tab === "gaps" && (
              <div className="space-y-6">
                <SkillGapAccordion items={result.skillInsights} />
                <DashboardCharts strengths={result.strengths} gaps={result.gaps} extractedSkills={result.parsedResume?.skillsExtracted || []} />
              </div>
            )}

            {!mutation.isPending && tab === "roadmap" && (
              <div className="space-y-5">
                <Card className="border-border/70 bg-secondary/20">
                  <div className="mb-4 flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2 text-sm">
                    <span className="font-semibold text-foreground">Roadmap Engine</span>
                    <span className="font-medium">
                      {result.parsedResume?.roadmapSource === "gemini"
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
