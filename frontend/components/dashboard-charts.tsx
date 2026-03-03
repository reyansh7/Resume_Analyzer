"use client";

import { useMemo } from "react";
import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar } from "recharts";

type DashboardChartsProps = {
  strengths: string[];
  gaps: string[];
  extractedSkills?: string[];
  confidence?: number;
};

function normalizeSkill(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9+/#.\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenizeSkill(value: string) {
  return normalizeSkill(value)
    .split(/[\s/-]+/)
    .map((token) => token.trim())
    .filter((token) => token.length >= 2);
}

function titleCaseSkill(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .map((part) => (part.length <= 3 ? part.toUpperCase() : `${part[0]?.toUpperCase() ?? ""}${part.slice(1)}`))
    .join(" ");
}

function collectDynamicAxes(strengths: string[], extractedSkills: string[], gaps: string[], limit = 5) {
  const orderedCandidates = [...strengths, ...extractedSkills, ...gaps]
    .map((item) => normalizeSkill(item))
    .filter((item) => item.length >= 2);

  const uniqueCandidates = Array.from(new Set(orderedCandidates));
  const selected = uniqueCandidates.slice(0, limit);

  if (selected.length >= 3) {
    return selected;
  }

  const fallbackPool = ["core skills", "domain knowledge", "execution", "communication", "tools"];
  for (const fallback of fallbackPool) {
    if (selected.length >= limit) break;
    if (!selected.includes(fallback)) {
      selected.push(fallback);
    }
  }

  return selected;
}

function toRadarBuckets(strengths: string[], extractedSkills: string[], gaps: string[]) {
  const evidenceSource = [...strengths, ...extractedSkills].map((item) => normalizeSkill(item));
  const gapSource = gaps.map((item) => normalizeSkill(item));
  const axes = collectDynamicAxes(strengths, extractedSkills, gaps);

  const overlapRatio = (axisTokens: string[], sourceValue: string) => {
    if (!axisTokens.length || !sourceValue) return 0;
    const sourceTokens = new Set(tokenizeSkill(sourceValue));
    if (sourceTokens.size === 0) return 0;
    const overlap = axisTokens.filter((token) => sourceTokens.has(token)).length;
    return overlap / axisTokens.length;
  };

  return axes.map((axis) => {
    const axisTokens = tokenizeSkill(axis);
    const evidenceScore = evidenceSource.reduce((max, value) => Math.max(max, overlapRatio(axisTokens, value)), 0);
    const gapScore = gapSource.reduce((max, value) => Math.max(max, overlapRatio(axisTokens, value)), 0);
    const weighted = 30 + evidenceScore * 55 - gapScore * 35;

    return {
      skill: titleCaseSkill(axis),
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

export function DashboardCharts({ strengths, gaps, extractedSkills = [], confidence }: DashboardChartsProps) {
  const radarData = useMemo(() => toRadarBuckets(strengths, extractedSkills, gaps), [strengths, extractedSkills, gaps]);
  const gapData = useMemo(() => toGapBars(gaps, extractedSkills), [gaps, extractedSkills]);
  const hasGapData = gapData.some((item) => item.gap > 0);
  const evidenceCount = useMemo(() => new Set([...strengths, ...extractedSkills].map((item) => normalizeSkill(item)).filter(Boolean)).size, [strengths, extractedSkills]);
  const isLowConfidence = (typeof confidence === "number" && confidence < 0.45) || evidenceCount < 2;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="glass-card h-80 p-4">
        <p className="mb-2 text-sm font-medium">Skill Alignment Radar</p>
        {isLowConfidence && (
          <p className="mb-2 text-xs text-muted-foreground">
            Limited evidence detected for this resume. Radar is approximate; add more readable skill/project text for higher confidence.
          </p>
        )}
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="skill" />
            <Radar dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={isLowConfidence ? 0.2 : 0.35} />
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
            <Bar dataKey="gap" fill="hsl(var(--primary))" fillOpacity={isLowConfidence ? 0.65 : 1} radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        {!hasGapData && <p className="mt-1 text-xs text-muted-foreground">No high-priority skill gaps detected for this profile.</p>}
      </div>
    </div>
  );
}
