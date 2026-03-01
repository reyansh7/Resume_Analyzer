"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Copy } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type RewriteSuggestion = {
  section: string;
  before: string;
  after: string;
  improvement_type: string;
};

export function ResumeRewritePanel({ rewrites = [] }: { rewrites?: RewriteSuggestion[] }) {
  const [copied, setCopied] = useState<string | null>(null);

  const copy = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 1200);
  };

  if (!rewrites.length) {
    return <Card><p className="text-sm text-muted-foreground">No rewrite suggestions yet. Upload a resume to generate ATS-safe improvements.</p></Card>;
  }

  return (
    <div className="space-y-3">
      {rewrites.map((item, index) => {
        const key = `${item.section}-${index}`;
        return (
          <motion.div key={key} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}>
            <Card className="space-y-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">{item.section}</p>
                <span className="rounded-full bg-secondary px-2.5 py-1 text-xs">{item.improvement_type}</span>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-border/70 bg-secondary/30 p-3">
                  <p className="text-xs font-medium text-muted-foreground">Before</p>
                  <p className="mt-1 text-sm">{item.before}</p>
                </div>
                <div className="rounded-lg border border-primary/40 bg-primary/5 p-3">
                  <p className="text-xs font-medium text-muted-foreground">After</p>
                  <p className="mt-1 text-sm">{item.after}</p>
                </div>
              </div>
              <Button variant="secondary" onClick={() => copy(item.after, key)}>
                <Copy className="mr-2 h-3.5 w-3.5" /> {copied === key ? "Copied" : "Copy Improved Bullet"}
              </Button>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
