"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { Card } from "@/components/ui/card";

type SkillInsight = {
  skill: string;
  detected_from: string;
  confidence: number;
  related_missing_skills: string[];
  improvement_suggestions: string;
  resources: Array<{ title: string; type: string; link: string }>;
};

export function SkillGapAccordion({ items }: { items: SkillInsight[] }) {
  const [openSkill, setOpenSkill] = useState<string | null>(items[0]?.skill ?? null);

  if (!items.length) {
    return <Card><p className="text-sm text-muted-foreground">No skill insights available yet.</p></Card>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const open = openSkill === item.skill;
        return (
          <Card key={`${item.skill}-${item.detected_from.slice(0, 20)}`} className="p-0">
            <button
              className="flex w-full items-center justify-between px-4 py-3 text-left"
              onClick={() => setOpenSkill(open ? null : item.skill)}
              type="button"
            >
              <div>
                <p className="font-medium">{item.skill}</p>
                <p className="text-xs text-muted-foreground">Confidence {(item.confidence * 100).toFixed(0)}%</p>
              </div>
              <motion.span animate={{ rotate: open ? 180 : 0 }}>
                <ChevronDown className="h-4 w-4" />
              </motion.span>
            </button>

            <AnimatePresence initial={false}>
              {open && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="overflow-hidden border-t border-border/60 px-4 py-3"
                >
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">Detected from</p>
                      <p className="mt-1 rounded-md bg-secondary/70 px-3 py-2 leading-relaxed">{item.detected_from}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">Missing related skills</p>
                      <div className="mt-1 flex flex-wrap gap-2">
                        {(item.related_missing_skills.length ? item.related_missing_skills : ["None detected"]).map((skill) => (
                          <span key={skill} className="rounded-full bg-secondary/80 px-2.5 py-1 text-xs">{skill}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">How to improve</p>
                      <p className="mt-1">{item.improvement_suggestions}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">Suggested learning resources</p>
                      <ul className="mt-1 space-y-1">
                        {item.resources.map((resource) => (
                          <li key={resource.link}>
                            <a className="text-primary underline-offset-2 hover:underline" href={resource.link} target="_blank" rel="noreferrer">
                              {resource.title} <span className="text-xs text-muted-foreground">({resource.type})</span>
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        );
      })}
    </div>
  );
}
