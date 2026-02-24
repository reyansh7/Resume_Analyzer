"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { saveOnboarding } from "@/services/onboarding-service";

const professions = ["Software Engineer", "Data Analyst", "Product Manager", "DevOps Engineer"];
const levels = ["Entry", "Mid", "Senior", "Lead"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ profession: "", role: "", level: "", skills: "", goal: "" });

  const progress = (step / 4) * 100;

  const next = () => setStep((s) => Math.min(4, s + 1));
  const prev = () => setStep((s) => Math.max(1, s - 1));

  const finish = async () => {
    const payload = {
      profession: form.profession,
      targetRole: form.role,
      level: form.level || "Entry",
      skills: form.skills
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      goal: form.goal
    };

    try {
      await saveOnboarding(payload);
    } catch {
      // Preserve UX continuity in case backend is temporarily unavailable.
    }

    localStorage.setItem("onboarding", JSON.stringify(form));
    router.push("/dashboard");
  };

  return (
    <main className="mx-auto max-w-3xl px-4 py-20">
      <Card className="space-y-8">
        <div>
          <p className="text-sm text-muted-foreground">Step {step} of 4</p>
          <Progress value={progress} />
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.35 }}
            className="space-y-4"
          >
            {step === 1 && (
              <>
                <h2 className="text-2xl font-semibold">Select your profession</h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  {professions.map((item) => (
                    <button
                      key={item}
                      onClick={() => setForm((f) => ({ ...f, profession: item }))}
                      className={`rounded-xl border p-4 text-left transition hover:scale-[1.01] ${form.profession === item ? "border-primary bg-primary/10" : "border-border"}`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </>
            )}

            {step === 2 && (
              <>
                <h2 className="text-2xl font-semibold">Target role & experience</h2>
                <Input placeholder="Target role (e.g. Senior Backend Engineer)" value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))} />
                <input
                  type="range"
                  min={0}
                  max={3}
                  value={levels.indexOf(form.level || "Entry")}
                  onChange={(e) => setForm((f) => ({ ...f, level: levels[Number(e.target.value)] }))}
                  className="w-full"
                />
                <p className="text-sm text-muted-foreground">Selected level: {form.level || "Entry"}</p>
              </>
            )}

            {step === 3 && (
              <>
                <h2 className="text-2xl font-semibold">Current skills</h2>
                <Input placeholder="React, Node.js, SQL, AWS" value={form.skills} onChange={(e) => setForm((f) => ({ ...f, skills: e.target.value }))} />
                <p className="text-sm text-muted-foreground">Tip: comma-separated skills help us personalize your roadmap.</p>
              </>
            )}

            {step === 4 && (
              <>
                <h2 className="text-2xl font-semibold">Career goal</h2>
                <Input placeholder="What role or outcome are you aiming for?" value={form.goal} onChange={(e) => setForm((f) => ({ ...f, goal: e.target.value }))} />
              </>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={prev} disabled={step === 1}>Back</Button>
          {step < 4 ? <Button onClick={next}>Next</Button> : <Button onClick={finish}>Continue to Upload</Button>}
        </div>
      </Card>
    </main>
  );
}
