"use client";

import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar } from "recharts";

const radarData = [
  { skill: "Frontend", score: 86 },
  { skill: "Backend", score: 72 },
  { skill: "System Design", score: 64 },
  { skill: "Cloud", score: 59 },
  { skill: "ML", score: 51 }
];

const gapData = [
  { skill: "Docker", gap: 28 },
  { skill: "Kubernetes", gap: 35 },
  { skill: "MLOps", gap: 31 },
  { skill: "CI/CD", gap: 22 }
];

export function DashboardCharts() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="glass-card h-80 p-4">
        <p className="mb-2 text-sm font-medium">Skill Alignment Radar</p>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="skill" />
            <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.4} />
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
            <Bar dataKey="gap" fill="#06b6d4" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
