"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { getMe } from "@/services/auth-service";
import { saveOnboarding } from "@/services/onboarding-service";

const professionCategories = [
  "INFORMATION-TECHNOLOGY",
  "BUSINESS-DEVELOPMENT",
  "FINANCE",
  "HEALTHCARE",
  "HR",
  "SALES",
  "TEACHER",
  "ENGINEERING",
  "CONSULTANT",
  "DESIGNER"
];

const supportedTargetRoles = ["Software Engineer", "Data Analyst", "Product Manager", "DevOps Engineer"];
const levels = ["Entry", "Mid", "Senior", "Lead"];

export default function OnboardingPage() {
  const router = useRouter();
  const [checkingGuard, setCheckingGuard] = useState(true);
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ profession: "", role: "", level: "Entry", skills: "", goal: "" });

  const progress = (step / 4) * 100;
  const canProceed =
    (step === 1 && Boolean(form.profession)) ||
    (step === 2 && Boolean(form.role) && Boolean(form.level)) ||
    (step === 3 && Boolean(form.skills.trim())) ||
    step === 4;

  const next = () => setStep((s) => Math.min(4, s + 1));
  const prev = () => setStep((s) => Math.max(1, s - 1));

  useEffect(() => {
    let isMounted = true;

    (async () => {
      try {
        const me = await getMe();
        if (!isMounted) return;

        if (me.onboardingComplete) {
          router.replace("/dashboard");
          return;
        }
      } catch {
        if (!isMounted) return;
        router.replace("/login");
        return;
      }

      if (isMounted) {
        setCheckingGuard(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [router]);

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

  if (checkingGuard) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-20">
        <Card>
          <p className="text-sm text-muted-foreground">Checking onboarding status...</p>
        </Card>
      </main>
    );
  }

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
                <h2 className="text-2xl font-semibold">Select your professional domain</h2>
                <p className="text-sm text-muted-foreground">
                  Pick the closest category to your background. These categories align with our resume training dataset.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {professionCategories.map((item) => (
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
                <p className="text-sm text-muted-foreground">
                  Choose one supported role for strongest skill-gap and roadmap accuracy.
                </p>
                <p className="text-xs text-muted-foreground">Target Role</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {supportedTargetRoles.map((item) => (
                    <button
                      type="button"
                      key={item}
                      onClick={() => setForm((f) => ({ ...f, role: item }))}
                      className={`rounded-xl border p-4 text-left transition hover:scale-[1.01] ${form.role === item ? "border-primary bg-primary/10 ring-2 ring-primary/40" : "border-border"}`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground">Experience Level</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {levels.map((item) => (
                    <button
                      type="button"
                      key={item}
                      onClick={() => setForm((f) => ({ ...f, level: item }))}
                      className={`rounded-xl border p-4 text-left transition hover:scale-[1.01] ${form.level === item ? "border-primary bg-primary/10 ring-2 ring-primary/40" : "border-border"}`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
                {!form.role && <p className="text-xs text-amber-500">Select a target role to continue.</p>}
              </>
            )}

            {step === 3 && (
              <>
                <h2 className="text-2xl font-semibold">Current skills</h2>
                <Input placeholder="Python, SQL, Docker, AWS" value={form.skills} onChange={(e) => setForm((f) => ({ ...f, skills: e.target.value }))} />
                <p className="text-sm text-muted-foreground">Tip: use clear comma-separated hard skills to improve matching quality.</p>
              </>
            )}

            {step === 4 && (
              <>
                <h2 className="text-2xl font-semibold">Career goal</h2>
                <Input placeholder="Example: Become a Senior Data Analyst in 12 months" value={form.goal} onChange={(e) => setForm((f) => ({ ...f, goal: e.target.value }))} />
              </>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={prev} disabled={step === 1}>Back</Button>
          {step < 4 ? <Button onClick={next} disabled={!canProceed}>Next</Button> : <Button onClick={finish}>Continue to Upload</Button>}
        </div>
      </Card>
    </main>
  );
}
