"use client";

import { useEffect } from "react";
import { motion, useSpring, useTransform } from "framer-motion";
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis, Tooltip } from "recharts";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

type Props = {
  overallScore: number;
  confidence: number;
  breakdown: {
    technical_skills: number;
    soft_skills: number;
    experience_match: number;
    education_match: number;
  };
};

const LABELS: Array<{ key: keyof Props["breakdown"]; label: string }> = [
  { key: "technical_skills", label: "Technical Skills" },
  { key: "experience_match", label: "Experience Match" },
  { key: "soft_skills", label: "Soft Skills" },
  { key: "education_match", label: "Education Match" },
];

export function AdvancedScoreAnalytics({ overallScore, confidence, breakdown }: Props) {
  const normalized = Math.max(0, Math.min(100, overallScore));
  const animated = useSpring(0, { stiffness: 45, damping: 15 });
  const animatedText = useTransform(animated, (value) => `${Math.round(value)}%`);

  useEffect(() => {
    animated.set(normalized);
  }, [animated, normalized]);

  const radialData = [{ name: "match", value: normalized, fill: "hsl(var(--primary))" }];

  return (
    <Card className="overflow-hidden border-primary/30">
      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <div className="relative flex h-[280px] items-center justify-center">
          <motion.div
            className="absolute h-44 w-44 rounded-full bg-primary/20 blur-2xl"
            animate={{ opacity: [0.45, 0.9, 0.45], scale: [0.92, 1.05, 0.92] }}
            transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
          />
          <div className="absolute h-52 w-52 rounded-full border border-primary/40" />
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart innerRadius="72%" outerRadius="100%" data={radialData} startAngle={90} endAngle={-270}>
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar dataKey="value" cornerRadius={20} background={{ fill: "hsl(var(--secondary))" }} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute text-center">
            <motion.p className="text-4xl font-semibold">{animatedText}</motion.p>
            <p className="text-xs text-muted-foreground">Overall Match</p>
            <p className="mt-1 text-xs text-muted-foreground">Confidence: {(confidence * 100).toFixed(0)}% ± 5%</p>
          </div>
        </div>

        <div className="space-y-4 rounded-xl border border-border/70 bg-secondary/20 p-4">
          <p className="text-sm font-medium">Skill Gap Breakdown</p>
          {LABELS.map(({ key, label }) => (
            <div key={key} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span>{label}</span>
                <span className="text-muted-foreground">{Math.round(breakdown[key])}%</span>
              </div>
              <Progress value={breakdown[key]} />
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
