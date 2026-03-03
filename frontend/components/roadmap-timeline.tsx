"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type RoadmapTask = {
  skill: string;
  title: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  estimated_hours: number;
  priority_score: number;
  suggested_courses: string[];
  youtube_links: string[];
  leetcode_problems: string[];
  details: string;
};

type RoadmapAdvanced = {
  "30_day_plan": RoadmapTask[];
  "60_day_plan": RoadmapTask[];
  "90_day_plan": RoadmapTask[];
};

type PlanKey = keyof RoadmapAdvanced;

const PLAN_LABELS: Record<PlanKey, string> = {
  "30_day_plan": "30-Day Plan",
  "60_day_plan": "60-Day Plan",
  "90_day_plan": "90-Day Plan",
};

function difficultyClass(level: RoadmapTask["difficulty"]) {
  if (level === "Beginner") return "bg-primary/15 text-primary border-primary/30";
  if (level === "Intermediate") return "bg-primary/15 text-primary border-primary/30";
  return "bg-primary/15 text-primary border-primary/30";
}

export function RoadmapTimeline({ roadmap }: { roadmap?: RoadmapAdvanced }) {
  const [activePlan, setActivePlan] = useState<PlanKey>("30_day_plan");
  const [expanded, setExpanded] = useState<string | null>(null);

  const tasks = roadmap?.[activePlan] ?? [];
  const progress = useMemo(() => {
    if (!tasks.length) return 0;
    return Math.round((tasks.filter((_, index) => index < 2).length / tasks.length) * 100);
  }, [tasks]);

  if (!roadmap) {
    return <Card><p className="text-sm text-muted-foreground">Roadmap v2 data will appear after analysis.</p></Card>;
  }

  return (
    <Card>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          {(Object.keys(PLAN_LABELS) as PlanKey[]).map((plan) => (
            <Button key={plan} variant={activePlan === plan ? "default" : "secondary"} onClick={() => setActivePlan(plan)}>
              {PLAN_LABELS[plan]}
            </Button>
          ))}
        </div>

        <div className="rounded-lg border border-border/70 bg-secondary/30 px-3 py-2 text-sm">
          Plan Progress Tracker: <span className="font-medium">{progress}%</span>
        </div>

        <div className="relative space-y-4 pl-6">
          <div className="absolute bottom-0 left-2 top-0 w-px bg-primary/30" />
          {tasks.map((task, index) => {
            const key = `${task.title}-${index}`;
            const isOpen = expanded === key;
            return (
              <motion.div key={key} className="relative rounded-xl border border-border/70 bg-card/60 p-4" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}>
                <span className="absolute -left-[1.45rem] top-6 inline-block h-3 w-3 rounded-full bg-primary" />
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-base">{task.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">📚 {task.skill} • ⏱️ {task.estimated_hours}h • 🎯 {(task.priority_score * 100).toFixed(0)}% priority</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full border px-3 py-1 text-xs font-medium ${difficultyClass(task.difficulty)}`}>{task.difficulty}</span>
                    <Button variant="ghost" onClick={() => setExpanded(isOpen ? null : key)} className="ml-2 h-8 w-8 p-0">{isOpen ? "−" : "+"}</Button>
                  </div>
                </div>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                      <div className="mt-4 space-y-4 border-t border-border/40 pt-4">
                        <div className="rounded-lg bg-secondary/50 px-3 py-2 text-sm leading-relaxed">{task.details}</div>
                        
                        {(task.suggested_courses && task.suggested_courses.length > 0) && (
                          <div>
                            <p className="text-xs font-semibold text-primary flex items-center gap-1">📖 Suggested Courses</p>
                            <ul className="mt-2 space-y-1 text-xs">
                              {task.suggested_courses.map((course) => <li key={course} className="rounded px-2 py-1 bg-primary/10 text-primary">→ {course}</li>)}
                            </ul>
                          </div>
                        )}
                        
                        {(task.youtube_links && task.youtube_links.length > 0) && (
                          <div>
                            <p className="text-xs font-semibold text-primary flex items-center gap-1">▶️ YouTube Resources</p>
                            <ul className="mt-2 space-y-1 text-xs">
                              {task.youtube_links.map((link) => (
                                <li key={link}><a href={link} target="_blank" rel="noreferrer" className="text-primary underline-offset-2 hover:underline break-all">→ {link.substring(0, 60)}...</a></li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {(task.leetcode_problems && task.leetcode_problems.length > 0) && (
                          <div>
                            <p className="text-xs font-semibold text-primary flex items-center gap-1">⚙️ LeetCode Problems</p>
                            <ul className="mt-2 space-y-1 text-xs">
                              {task.leetcode_problems.map((link) => (
                                <li key={link}><a href={link} target="_blank" rel="noreferrer" className="text-primary underline-offset-2 hover:underline break-all">→ {link.substring(0, 60)}...</a></li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
          {tasks.length === 0 && <p className="text-sm text-muted-foreground">No tasks generated yet for this plan.</p>}
        </div>
      </div>
    </Card>
  );
}
