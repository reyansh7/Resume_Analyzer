"use client";

import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Navbar } from "@/components/navbar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { uploadResume } from "@/services/analysis-service";
import { MatchScoreRing } from "@/components/match-score-ring";
import { UploadZone } from "@/components/upload-zone";
import { DashboardCharts } from "@/components/dashboard-charts";

type Tab = "overview" | "gaps" | "roadmap";

const demo = {
  score: 78,
  parsedResume: {
    profession: "Software Engineer",
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
    featuredProject: "Next-Word Prediction using LSTM & GRU — Built and trained sequence models on Hamlet dataset.",
    featuredProjects: [
      "Next-Word Prediction using LSTM & GRU — Built and trained sequence models on Hamlet dataset.",
      "Fraud Detection System — Developed anomaly detection workflows with model evaluation metrics.",
      "Customer Churn Prediction — Built churn classifier and feature-engineering pipeline for retention signals."
    ],
    featuredExperiences: [
      "Led creative strategy for major hackathon and conference events.",
      "Coordinated expert sessions and managed article-writing operations."
    ],
    roadmapSource: "gemini",
    roadmapModel: "gemini-2.0-flash"
  },
  strengths: ["React", "TypeScript", "REST API Design"],
  gaps: ["Docker", "Kubernetes", "MLOps", "System Design"],
  transferable: ["Agile Delivery", "Stakeholder Communication", "Problem Solving"],
  roadmap: [
    { title: "Containerization Fundamentals", description: "Learn Docker images, compose and deployment patterns." },
    { title: "Orchestration Basics", description: "Understand Kubernetes core objects and scaling strategies." },
    { title: "ML Systems", description: "Practice MLOps pipelines, model monitoring, and lifecycle management." }
  ],
  certs: ["AWS Certified Developer", "CKA", "TensorFlow Developer"]
};

export default function DashboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [tab, setTab] = useState<Tab>("overview");

  const mutation = useMutation({
    mutationFn: async (uploadFile: File) => {
      const formData = new FormData();
      formData.append("resume", uploadFile);
      return uploadResume(formData);
    }
  });

  const result = useMemo(() => {
    if (mutation.data) {
      return {
        score: mutation.data.matchScore,
        parsedResume: mutation.data.parsedResume,
        strengths: mutation.data.strengths,
        gaps: mutation.data.skillGaps,
        transferable: mutation.data.transferableSkills,
        roadmap: mutation.data.roadmap,
        certs: mutation.data.certifications
      };
    }
    return demo;
  }, [mutation.data]);

  const normalizeTextList = (items: Array<string | null | undefined> | undefined): string[] => {
    if (!Array.isArray(items)) return [];
    return Array.from(
      new Set(
        items
          .map((item) => (typeof item === "string" ? item.trim() : ""))
          .filter((item) => item.length > 0)
      )
    );
  };

  const formatDisplayLine = (value: string): string => {
    return value
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      .replace(/,(?=\S)/g, ", ")
      .replace(/\b(Led|Built|Created|Developed|Implemented)(?=[a-z])/g, "$1 ")
      .replace(/ofthe/gi, "of the")
      .replace(/formorethan/gi, "for more than")
      .replace(/\s+/g, " ")
      .trim();
  };

  const visibleCertifications = useMemo(() => {
    const fromParsed = normalizeTextList(result.parsedResume?.certificationsDetected);
    const fromTopLevel = normalizeTextList(result.certs);
    return Array.from(new Set([...fromParsed, ...fromTopLevel]));
  }, [result.certs, result.parsedResume?.certificationsDetected]);

  const visibleAwardsAndCertifications = useMemo(() => {
    const awards = normalizeTextList(result.parsedResume?.awardsDetected);
    const certs = Array.isArray(visibleCertifications) ? visibleCertifications : [];
    return Array.from(new Set([...awards, ...certs]));
  }, [result.parsedResume?.awardsDetected, visibleCertifications]);

  const visibleProjects = useMemo(() => {
    const fromList = normalizeTextList(result.parsedResume?.featuredProjects);
    const fromSingle = normalizeTextList([result.parsedResume?.featuredProject]);
    return Array.from(new Set([...fromList, ...fromSingle]));
  }, [result.parsedResume?.featuredProject, result.parsedResume?.featuredProjects]);

  const visibleExperiences = useMemo(() => {
    return normalizeTextList(result.parsedResume?.featuredExperiences);
  }, [result.parsedResume?.featuredExperiences]);

  return (
    <main>
      <Navbar />
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10">
        <Card>
          <div className="grid gap-8 lg:grid-cols-[1.2fr_1fr]">
            <div>
              <h1 className="text-3xl font-semibold">Skill Gap Intelligence Dashboard</h1>
              <p className="mt-2 text-muted-foreground">Upload your resume to generate a role-based AI skill-gap and roadmap report.</p>
              <div className="mt-6">
                <UploadZone dragging={dragging} onSelectFile={setFile} setDragging={setDragging} />
              </div>
              <div className="mt-4 flex items-center gap-3">
                <Button disabled={!file || mutation.isPending} onClick={() => file && mutation.mutate(file)}>
                  {mutation.isPending ? "Analyzing..." : "Analyze Resume"}
                </Button>
                {file && <span className="text-sm text-muted-foreground">{file.name}</span>}
              </div>
            </div>
            <div className="flex items-center justify-center">
              <MatchScoreRing score={result.score} />
            </div>
          </div>
        </Card>

        <div className="flex gap-2">
          {(["overview", "gaps", "roadmap"] as Tab[]).map((item) => (
            <Button key={item} variant={tab === item ? "default" : "secondary"} onClick={() => setTab(item)}>
              {item}
            </Button>
          ))}
        </div>

        <motion.div key={tab} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          {mutation.isPending && (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="h-36 rounded-2xl shimmer" />
              <div className="h-36 rounded-2xl shimmer" />
              <div className="h-36 rounded-2xl shimmer" />
            </div>
          )}

          {!mutation.isPending && tab === "overview" && (
            <>
              <div className={`grid gap-5 ${visibleAwardsAndCertifications.length > 0 ? "md:grid-cols-3" : "md:grid-cols-2"}`}>
                <Card>
                  <p className="text-sm font-medium text-muted-foreground">Strengths</p>
                  <ul className="mt-3 space-y-2">{result.strengths.map((item) => <li key={item} className="rounded-lg bg-secondary/70 px-3 py-2">{item}</li>)}</ul>
                </Card>
                <Card>
                  <p className="text-sm font-medium text-muted-foreground">Transferable Skills</p>
                  <ul className="mt-3 space-y-2">{result.transferable.map((item) => <li key={item} className="rounded-lg bg-secondary/70 px-3 py-2">{item}</li>)}</ul>
                </Card>
                {visibleAwardsAndCertifications.length > 0 && (
                  <Card>
                    <p className="text-sm font-medium text-muted-foreground">Awards & Certifications</p>
                    <ul className="mt-3 space-y-2">{visibleAwardsAndCertifications.map((item) => <li key={item} className="rounded-lg bg-secondary/70 px-3 py-2">{formatDisplayLine(item)}</li>)}</ul>
                  </Card>
                )}
              </div>

              {mutation.data && (visibleProjects.length > 0 || visibleExperiences.length > 0) && (
                <div className="mt-5 grid gap-5 md:grid-cols-2">
                  {visibleProjects.length > 0 && (
                    <Card>
                      <p className="text-sm font-medium text-muted-foreground">Highlighted Projects</p>
                      <ul className="mt-3 space-y-2">
                        {visibleProjects.map((project) => (
                            <li key={project} className="rounded-lg bg-secondary/70 px-3 py-2 text-sm leading-relaxed">
                              {formatDisplayLine(project)}
                            </li>
                          ))}
                      </ul>
                    </Card>
                  )}
                  {visibleExperiences.length > 0 && (
                    <Card>
                      <p className="text-sm font-medium text-muted-foreground">Highlighted Experiences</p>
                      <ul className="mt-3 space-y-2">
                        {visibleExperiences.map((item) => (
                          <li key={item} className="rounded-lg bg-secondary/70 px-3 py-2 text-sm">{formatDisplayLine(item)}</li>
                        ))}
                      </ul>
                    </Card>
                  )}
                </div>
              )}

              <Card className="mt-5">
                <p className="text-sm font-medium text-muted-foreground">Resume Snapshot</p>
                <div className="mt-3 grid gap-4 md:grid-cols-2">
                  <div className="space-y-3 rounded-xl border border-border/70 bg-secondary/30 p-4 text-sm">
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Profession</span><span className="font-medium">{result.parsedResume?.profession || "-"}</span></div>
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Experience Level</span><span className="font-medium">{result.parsedResume?.experienceLevel || "-"}</span></div>
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Word Count</span><span className="font-medium">{result.parsedResume?.wordCount ?? "-"}</span></div>
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Category</span><span className="font-medium">{result.parsedResume?.predictedCategory || "-"}</span></div>
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Target Category</span><span className="font-medium">{result.parsedResume?.targetCategory || "-"}</span></div>
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Target Match Probability</span><span className="font-medium">{typeof result.parsedResume?.targetCategoryProbability === "number" ? `${Math.round(result.parsedResume.targetCategoryProbability * 100)}%` : "-"}</span></div>
                    <div className="flex items-center justify-between"><span className="text-muted-foreground">Model</span><span className="font-medium">{result.parsedResume?.modelUsed || "-"}</span></div>
                  </div>
                  <div className="rounded-xl border border-border/70 bg-secondary/30 p-4">
                    <p className="text-sm font-medium">Extracted Resume Skills</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(result.parsedResume?.skillsExtracted || []).slice(0, 16).map((item) => (
                        <span key={item} className="rounded-full bg-secondary/80 px-3 py-1 text-xs font-medium">{item}</span>
                      ))}
                      {(!result.parsedResume?.skillsExtracted || result.parsedResume.skillsExtracted.length === 0) && (
                        <span className="text-sm text-muted-foreground">No resume skills extracted.</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-4 rounded-xl border border-border/70 bg-secondary/40 p-3">
                  <p className="text-xs font-medium text-muted-foreground">Resume Text Preview</p>
                  <p className="mt-1 text-sm leading-relaxed">{result.parsedResume?.resumePreview || "Preview unavailable for this analysis."}</p>
                </div>
              </Card>
            </>
          )}

          {!mutation.isPending && tab === "gaps" && (
            <div className="space-y-6">
              <Card>
                <ul className="space-y-3">
                  {result.gaps.map((item, index) => (
                    <motion.li
                      key={item}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.08 }}
                      className="flex items-center justify-between rounded-lg bg-secondary/70 px-4 py-3"
                    >
                      <span>{item}</span>
                      <span className="text-sm text-muted-foreground">Gap Priority #{index + 1}</span>
                    </motion.li>
                  ))}
                </ul>
              </Card>
              <DashboardCharts
                strengths={result.strengths}
                gaps={result.gaps}
                matchScore={result.score}
                extractedSkills={result.parsedResume?.skillsExtracted || []}
              />
            </div>
          )}

          {!mutation.isPending && tab === "roadmap" && (
            <Card>
              <div className="mb-4 flex items-center justify-between rounded-lg bg-secondary/40 px-3 py-2 text-sm">
                <span className="text-muted-foreground">Roadmap Engine</span>
                <span className="font-medium">
                  {result.parsedResume?.roadmapSource === "gemini"
                    ? `Gemini${result.parsedResume?.roadmapModel ? ` (${result.parsedResume.roadmapModel})` : ""}`
                    : "Local Fallback"}
                </span>
              </div>
              <div className="relative pl-6">
                <div className="absolute bottom-0 left-2 top-0 w-px bg-primary/30" />
                <div className="space-y-5">
                  {result.roadmap.map((item, index) => (
                    <motion.div
                      key={item.title}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.12 }}
                      className="relative rounded-xl border border-border bg-white/60 p-4 dark:bg-white/5"
                    >
                      <span className="absolute -left-[1.45rem] top-5 inline-block h-3 w-3 rounded-full bg-primary" />
                      <h3 className="font-medium">{item.title}</h3>
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                        {item.description
                          .split(/\.\s+/)
                          .map((part) => part.trim())
                          .filter(Boolean)
                          .map((part) => (
                            <li key={`${item.title}-${part}`}>{part.endsWith(".") ? part : `${part}.`}</li>
                          ))}
                      </ul>
                    </motion.div>
                  ))}
                </div>
              </div>
            </Card>
          )}
        </motion.div>
      </div>
    </main>
  );
}
