"use client";

import { Card } from "@/components/ui/card";

type Ats = {
  ats_score: number;
  status: "ATS Safe" | "Needs Optimization" | "High Rejection Risk";
  issues: string[];
};

function statusClasses(status: Ats["status"]) {
  if (status === "ATS Safe") return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
  if (status === "Needs Optimization") return "bg-amber-500/15 text-amber-300 border-amber-500/30";
  return "bg-rose-500/15 text-rose-300 border-rose-500/30";
}

export function AtsCompatibilityCard({ ats }: { ats?: Ats }) {
  if (!ats) {
    return <Card><p className="text-sm text-muted-foreground">ATS analysis will appear after advanced analysis.</p></Card>;
  }

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">ATS Compatibility</p>
          <p className="text-xs text-muted-foreground">Automated screening readiness check</p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs ${statusClasses(ats.status)}`}>{ats.status}</span>
      </div>
      <div className="rounded-lg border border-border/60 bg-secondary/30 p-3">
        <p className="text-2xl font-semibold">{Math.round(ats.ats_score)}%</p>
        <p className="text-xs text-muted-foreground">ATS Score</p>
      </div>
      <ul className="space-y-2 text-sm">
        {ats.issues.map((issue) => (
          <li key={issue} className="rounded-lg bg-secondary/60 px-3 py-2">{issue}</li>
        ))}
        {ats.issues.length === 0 && <li className="rounded-lg bg-secondary/60 px-3 py-2">No major ATS blockers detected.</li>}
      </ul>
    </Card>
  );
}
