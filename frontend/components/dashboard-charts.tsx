"use client";

import { useMemo } from "react";
import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar } from "recharts";

type DashboardChartsProps = {
  strengths: string[];
  gaps: string[];
  extractedSkills?: string[];
};

function toRadarBuckets(strengths: string[], extractedSkills: string[], gaps: string[]) {
  const sourceSkills = (extractedSkills.length > 0 ? extractedSkills : strengths).map((item) => item.toLowerCase());
  const sourceGaps = gaps.map((item) => item.toLowerCase());

  const domains: Array<{ skill: string; keywords: string[] }> = [
    { skill: "Frontend", keywords: ["react", "next", "typescript", "javascript", "html", "css", "tailwind", "redux", "vue", "angular"] },
    { skill: "Backend", keywords: ["node", "express", "api", "rest", "graphql", "django", "flask", "spring", "java", "microservice", "postgres", "mysql", "mongodb"] },
    { skill: "System", keywords: ["system design", "architecture", "distributed", "scalability", "design pattern", "high availability"] },
    { skill: "Cloud", keywords: ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "devops", "ci/cd", "monitoring"] },
    { skill: "Data", keywords: ["sql", "pandas", "numpy", "tableau", "power bi", "excel", "statistics", "data analysis", "machine learning", "ml"] }
  ];

  const hasKeyword = (text: string, keyword: string) => text.includes(keyword);

  return domains.map((domain) => {
    const evidenceHits = domain.keywords.filter((keyword) => sourceSkills.some((skill) => hasKeyword(skill, keyword))).length;
    const gapHits = domain.keywords.filter((keyword) => sourceGaps.some((gap) => hasKeyword(gap, keyword))).length;
    const base = evidenceHits > 0 ? 18 : 6;
    const weighted = base + evidenceHits * 16 - gapHits * 10;

    return {
      skill: domain.skill,
      score: Math.max(5, Math.min(95, Math.round(weighted)))
    };
  });
}

function toGapBars(gaps: string[], extractedSkills: string[]) {
  const sanitized = gaps.filter((item) => item.trim().length > 0).slice(0, 6);
  if (sanitized.length === 0) {
    return [{ skill: "No critical gaps", gap: 0 }];
  }

  const normalize = (value: string) =>
    value
      .toLowerCase()
      .replace(/[^a-z0-9+/#.\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const canonicalize = (value: string) => {
    const normalized = normalize(value);
    const aliases: Record<string, string> = {
      "node.js": "node",
      nodejs: "node",
      "node js": "node",
      javascript: "javascript",
      typescript: "typescript",
      "my sql": "sql",
      k8s: "kubernetes",
      "amazon web services": "aws"
    };

    return aliases[normalized] || normalized;
  };

  const evidence = new Set(extractedSkills.map((item) => canonicalize(item)));
  const hasEvidenceForGap = (gap: string) => {
    const gapCanonical = canonicalize(gap);
    if (!gapCanonical) return false;
    if (evidence.has(gapCanonical)) return true;

    const gapTokens = new Set(gapCanonical.split(" "));
    for (const skill of evidence) {
      const skillTokens = new Set(skill.split(" "));
      const overlap = [...gapTokens].filter((token) => skillTokens.has(token)).length;
      if (overlap > 0 && overlap === gapTokens.size) {
        return true;
      }
    }

    return false;
  };

  const filtered = sanitized.filter((skill) => !hasEvidenceForGap(skill));
  if (filtered.length === 0) {
    return [{ skill: "No critical gaps", gap: 0 }];
  }

  const total = filtered.length;

  return filtered.map((skill, index) => ({
    skill: skill.length > 16 ? `${skill.slice(0, 16)}…` : skill,
    gap: Math.round(42 + ((total - index) / total) * 48)
  }));
}

export function DashboardCharts({ strengths, gaps, extractedSkills = [] }: DashboardChartsProps) {
  const radarData = useMemo(() => toRadarBuckets(strengths, extractedSkills, gaps), [strengths, extractedSkills, gaps]);
  const gapData = useMemo(() => toGapBars(gaps, extractedSkills), [gaps, extractedSkills]);
  const hasGapData = gapData.some((item) => item.gap > 0);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="glass-card h-80 p-4">
        <p className="mb-2 text-sm font-medium">Skill Alignment Radar</p>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="skill" />
            <Radar dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.35} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="glass-card h-80 p-4">
        <p className="mb-2 text-sm font-medium">Priority Skill Gaps</p>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={gapData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="skill" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="gap" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        {!hasGapData && <p className="mt-1 text-xs text-muted-foreground">No high-priority skill gaps detected for this profile.</p>}
      </div>
    </div>
  );
}
