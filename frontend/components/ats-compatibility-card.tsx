"use client";

import { Card } from "@/components/ui/card";

type Ats = {
  ats_score: number;
  status: "ATS Safe" | "Needs Optimization" | "High Rejection Risk";
  issues: string[];
};

type IssueDetail = {
  area: "Keywords" | "Structure" | "Content Depth" | "Formatting" | "Action Verbs" | "General";
  impact: "High" | "Medium" | "Low";
  why: string;
  fix: string;
};

function statusClasses(status: Ats["status"]) {
  if (status === "ATS Safe") return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
  if (status === "Needs Optimization") return "bg-amber-500/15 text-amber-300 border-amber-500/30";
  return "bg-rose-500/15 text-rose-300 border-rose-500/30";
}

function impactClasses(impact: IssueDetail["impact"]) {
  if (impact === "High") return "bg-rose-500/15 text-rose-300 border-rose-500/30";
  if (impact === "Medium") return "bg-amber-500/15 text-amber-300 border-amber-500/30";
  return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
}

function describeIssue(issue: string): IssueDetail {
  const text = issue.toLowerCase();

  if (text.includes("keyword")) {
    return {
      area: "Keywords",
      impact: "High",
      why: "ATS systems rank resumes by exact role keywords and tool terms found in job descriptions.",
      fix: "Add missing role keywords naturally in Summary, Skills, and 2-3 recent impact bullets."
    };
  }

  if (text.includes("certification")) {
    return {
      area: "Structure",
      impact: "Medium",
      why: "Missing certification sections can hide relevant credentials from screening rules.",
      fix: "Add a dedicated Certifications section with certificate name, issuer, and completion date."
    };
  }

  if (text.includes("verb")) {
    return {
      area: "Action Verbs",
      impact: "Medium",
      why: "Weak verbs reduce clarity of your impact and can lower semantic relevance.",
      fix: "Rewrite bullets with strong verbs like Led, Built, Optimized, Delivered, Automated."
    };
  }

  if (text.includes("short") || text.includes("depth") || text.includes("detail")) {
    return {
      area: "Content Depth",
      impact: "High",
      why: "Thin descriptions reduce ATS confidence and make role matching less accurate.",
      fix: "Expand each recent role with impact metrics, tools used, and outcomes (3-5 bullets per role)."
    };
  }

  if (text.includes("format") || text.includes("layout") || text.includes("read")) {
    return {
      area: "Formatting",
      impact: "Medium",
      why: "Complex formatting can break ATS parsing and cause missed information.",
      fix: "Use simple headings, standard fonts, and avoid text-in-images/tables for critical content."
    };
  }

  return {
    area: "General",
    impact: "Medium",
    why: "This issue may reduce ATS readability or matching quality.",
    fix: "Address this item directly and re-check your resume score after updating content."
  };
}

function statusSummary(status: Ats["status"]) {
  if (status === "ATS Safe") {
    return "Your resume is generally ATS-friendly. Improve role-specific keywords to push matching consistency even higher.";
  }
  if (status === "Needs Optimization") {
    return "Your resume is parseable but may miss relevant matches for competitive roles due to optimization gaps.";
  }
  return "Your resume currently has major ATS blockers and may be filtered out before recruiter review.";
}

export function AtsCompatibilityCard({ ats }: { ats?: Ats }) {
  if (!ats) {
    return <Card><p className="text-sm text-muted-foreground">ATS analysis will appear after advanced analysis.</p></Card>;
  }

  const score = Math.max(0, Math.min(100, Math.round(ats.ats_score)));
  const detailedIssues = ats.issues.map((issue) => ({ issue, detail: describeIssue(issue) }));
  const highImpactCount = detailedIssues.filter((item) => item.detail.impact === "High").length;
  const mediumImpactCount = detailedIssues.filter((item) => item.detail.impact === "Medium").length;

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">ATS Compatibility</p>
          <p className="text-xs text-muted-foreground">Automated screening readiness check</p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs ${statusClasses(ats.status)}`}>{ats.status}</span>
      </div>

      <div className="rounded-lg border border-border/60 bg-secondary/30 p-4">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-3xl font-semibold">{score}%</p>
            <p className="text-xs text-muted-foreground">ATS Score</p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <p>High impact: {highImpactCount}</p>
            <p>Medium impact: {mediumImpactCount}</p>
          </div>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{statusSummary(ats.status)}</p>
      </div>

      <div className="grid gap-2 text-xs sm:grid-cols-3">
        <div className="rounded-lg bg-secondary/50 px-3 py-2">
          <p className="font-medium text-foreground">Keywords</p>
          <p className="mt-1 text-muted-foreground">Role terms, stack terms, and domain nouns should appear naturally in your bullets.</p>
        </div>
        <div className="rounded-lg bg-secondary/50 px-3 py-2">
          <p className="font-medium text-foreground">Experience Depth</p>
          <p className="mt-1 text-muted-foreground">Each role should show impact, tools, and measurable outcomes to improve matching.</p>
        </div>
        <div className="rounded-lg bg-secondary/50 px-3 py-2">
          <p className="font-medium text-foreground">Section Coverage</p>
          <p className="mt-1 text-muted-foreground">Use clear sections like Skills, Experience, Projects, Education, and Certifications.</p>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        {detailedIssues.map(({ issue, detail }) => (
          <div key={issue} className="rounded-lg bg-secondary/60 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="font-medium">{issue}</p>
              <span className={`rounded-full border px-2 py-0.5 text-[11px] ${impactClasses(detail.impact)}`}>{detail.impact} impact</span>
            </div>
            <p className="mt-2 text-xs text-muted-foreground"><span className="font-medium text-foreground">Why it matters:</span> {detail.why}</p>
            <p className="mt-1.5 text-xs text-muted-foreground"><span className="font-medium text-foreground">How to fix:</span> {detail.fix}</p>
            <p className="mt-1.5 text-[11px] text-muted-foreground">Area: {detail.area}</p>
          </div>
        ))}
        {detailedIssues.length === 0 && <div className="rounded-lg bg-secondary/60 px-3 py-2">No major ATS blockers detected.</div>}
      </div>
    </Card>
  );
}
