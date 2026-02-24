"use client";

import { useMemo } from "react";
import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar } from "recharts";

type DashboardChartsProps = {
  strengths: string[];
  gaps: string[];
  matchScore: number;
};

function toRadarBuckets(strengths: string[], matchScore: number) {
  const lower = strengths.map((item) => item.toLowerCase());

  const has = (keywords: string[]) => keywords.some((keyword) => lower.some((item) => item.includes(keyword)));
  const bump = (condition: boolean, amount: number) => (condition ? amount : 0);

  return [
    {
      skill: "Frontend",
      score: Math.min(100, Math.round(matchScore * 0.45 + bump(has(["react", "frontend", "typescript"]), 28)))
    },
    {
      skill: "Backend",
      score: Math.min(100, Math.round(matchScore * 0.5 + bump(has(["node", "python", "api", "sql"]), 30)))
    },
    {
      skill: "System",
      score: Math.min(100, Math.round(matchScore * 0.4 + bump(has(["system design", "architecture"]), 35)))
    },
    {
      skill: "Cloud",
      score: Math.min(100, Math.round(matchScore * 0.35 + bump(has(["aws", "azure", "gcp", "docker", "kubernetes"]), 32)))
    },
    {
      skill: "Data",
      score: Math.min(100, Math.round(matchScore * 0.3 + bump(has(["sql", "analytics", "pandas"]), 28)))
    }
  ];
}

function toGapBars(gaps: string[]) {
  return gaps.slice(0, 6).map((skill, index) => ({
    skill: skill.length > 16 ? `${skill.slice(0, 16)}…` : skill,
    gap: Math.max(8, 36 - index * 4)
  }));
}

export function DashboardCharts({ strengths, gaps, matchScore }: DashboardChartsProps) {
  const radarData = useMemo(() => toRadarBuckets(strengths, matchScore), [strengths, matchScore]);
  const gapData = useMemo(() => toGapBars(gaps), [gaps]);

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
            <YAxis />
            <Tooltip />
            <Bar dataKey="gap" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
