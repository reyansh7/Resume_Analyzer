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

const levels = ["Entry", "Mid", "Senior", "Lead"];

type ProfessionSkillHint = {
  placeholder: string;
  tip: string;
};

const defaultSkillHint: ProfessionSkillHint = {
  placeholder: "Excel, SQL, Stakeholder Management, Process Improvement",
  tip: "Add role-relevant, measurable skills so we can map stronger gap insights."
};

const professionSkillHints: Record<string, ProfessionSkillHint> = {
  "INFORMATION-TECHNOLOGY": {
    placeholder: "Python, SQL, Docker, AWS, System Design",
    tip: "Include core stack + platform skills (languages, cloud, infra, architecture)."
  },
  "BUSINESS-DEVELOPMENT": {
    placeholder: "Lead Generation, CRM, Market Research, Negotiation, Pipeline Management",
    tip: "List growth and revenue-impact skills so roadmap steps align with GTM outcomes."
  },
  FINANCE: {
    placeholder: "Financial Modeling, Excel, Budgeting, Forecasting, Power BI, SQL",
    tip: "Include analysis/reporting tools and core finance workflows for sharper gap scoring."
  },
  HEALTHCARE: {
    placeholder: "Patient Care, Clinical Documentation, EMR, Triage, Infection Control",
    tip: "Mention clinical or healthcare-operations competencies used in real settings."
  },
  HR: {
    placeholder: "Talent Acquisition, HRIS, Onboarding, Employee Relations, Payroll",
    tip: "Add hiring, people-ops, and compliance skills to improve HR role matching."
  },
  SALES: {
    placeholder: "Prospecting, Objection Handling, CRM, Deal Closing, Account Management",
    tip: "Use pipeline and closing-related skills so gaps reflect practical sales execution."
  },
  TEACHER: {
    placeholder: "Curriculum Planning, Classroom Management, Assessment Design, EdTech",
    tip: "Include pedagogy, classroom, and learning-outcome skills for better education fit."
  },
  ENGINEERING: {
    placeholder: "AutoCAD, SolidWorks, MATLAB, ANSYS, Quality Control, GD&T",
    tip: "List technical design/simulation tools and engineering standards you actually use."
  },
  CONSULTANT: {
    placeholder: "Problem Structuring, Stakeholder Management, Data Analysis, PowerPoint, Excel",
    tip: "Highlight analysis, communication, and client-delivery skills for consulting tracks."
  },
  DESIGNER: {
    placeholder: "Figma, Adobe XD, Wireframing, Prototyping, Design Systems, User Research",
    tip: "Include UX/UI workflow skills and tools so design gap analysis is role-accurate."
  }
};

type ProfessionConfig = {
  roles: string[];
  followUps: Array<{
    id: "specialization" | "focusTool";
    question: string;
    options: string[];
  }>;
};

const defaultProfessionConfig: ProfessionConfig = {
  roles: ["Product Manager", "Business Analyst", "Operations Manager", "Consultant"],
  followUps: [
    {
      id: "specialization",
      question: "Which specialization best fits your direction?",
      options: ["Strategy", "Operations", "Client Delivery", "Analytics"]
    },
    {
      id: "focusTool",
      question: "Which toolset do you use the most?",
      options: ["Excel", "Power BI", "SQL", "Project Management Tools"]
    }
  ]
};

const professionConfig: Record<string, ProfessionConfig> = {
  "INFORMATION-TECHNOLOGY": {
    roles: ["Software Engineer", "Data Analyst", "Product Manager", "DevOps Engineer"],
    followUps: [
      {
        id: "specialization",
        question: "Which IT track are you targeting?",
        options: ["Backend Development", "Frontend Development", "Data Analytics", "Cloud & DevOps"]
      },
      {
        id: "focusTool",
        question: "Which primary tool stack do you use?",
        options: ["Python + SQL", "React + TypeScript", "Docker + Kubernetes", "AWS + CI/CD"]
      }
    ]
  },
  FINANCE: {
    roles: ["Financial Analyst", "Investment Analyst", "Accountant", "Risk Analyst"],
    followUps: [
      {
        id: "specialization",
        question: "Which finance area are you focused on?",
        options: ["FP&A", "Investment Research", "Accounting", "Risk & Compliance"]
      },
      {
        id: "focusTool",
        question: "Which finance tools do you use most?",
        options: ["Excel Modeling", "Power BI", "SQL", "Bloomberg Terminal"]
      }
    ]
  },
  ENGINEERING: {
    roles: ["Mechanical Engineer", "Civil Engineer", "Electrical Engineer", "Industrial Engineer"],
    followUps: [
      {
        id: "specialization",
        question: "Which engineering specialization matches your profile?",
        options: ["Design & CAD", "Analysis & Simulation", "Production", "Quality & Safety"]
      },
      {
        id: "focusTool",
        question: "Which core tools are you strongest in?",
        options: ["AutoCAD", "SolidWorks", "MATLAB", "ANSYS"]
      }
    ]
  },
  "BUSINESS-DEVELOPMENT": {
    roles: ["Business Development Manager", "Sales Manager", "Product Manager", "Consultant"],
    followUps: [
      {
        id: "specialization",
        question: "Which business function are you targeting?",
        options: ["Partnerships", "Sales Strategy", "Go-to-Market", "Account Growth"]
      },
      {
        id: "focusTool",
        question: "Which tools are most relevant to your workflow?",
        options: ["CRM Platforms", "Excel", "Power BI", "Presentation & Pitching"]
      }
    ]
  }
};

function getProfessionConfig(profession: string): ProfessionConfig {
  return professionConfig[profession] ?? defaultProfessionConfig;
}

function deriveSkills(rawSkills: string, specialization: string, focusTool: string) {
  return Array.from(
    new Set(
      [
        ...rawSkills
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        specialization,
        focusTool
      ].filter(Boolean)
    )
  );
}

function getSkillHint(profession: string): ProfessionSkillHint {
  return professionSkillHints[profession] ?? defaultSkillHint;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [checkingGuard, setCheckingGuard] = useState(true);
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    profession: "",
    role: "",
    level: "Entry",
    specialization: "",
    focusTool: "",
    skills: "",
    goal: ""
  });

  const selectedProfessionConfig = getProfessionConfig(form.profession);
  const selectedSkillHint = getSkillHint(form.profession);

  const progress = (step / 4) * 100;
  const canProceed =
    (step === 1 && Boolean(form.profession)) ||
    (step === 2 && Boolean(form.role) && Boolean(form.level) && Boolean(form.specialization) && Boolean(form.focusTool)) ||
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
      skills: deriveSkills(form.skills, form.specialization, form.focusTool),
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
                      onClick={() =>
                        setForm((f) => ({
                          ...f,
                          profession: item,
                          role: "",
                          specialization: "",
                          focusTool: ""
                        }))
                      }
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
                  Follow-up questions now adapt to your selected domain so the analysis and gap suggestions stay field-specific.
                </p>
                <p className="text-xs text-muted-foreground">Target Role</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {selectedProfessionConfig.roles.map((item) => (
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

                {selectedProfessionConfig.followUps.map((followUp) => (
                  <div key={followUp.id} className="space-y-2">
                    <p className="text-xs text-muted-foreground">{followUp.question}</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {followUp.options.map((option) => {
                        const isSelected = form[followUp.id] === option;

                        return (
                          <button
                            type="button"
                            key={option}
                            onClick={() => setForm((f) => ({ ...f, [followUp.id]: option }))}
                            className={`rounded-xl border p-4 text-left transition hover:scale-[1.01] ${isSelected ? "border-primary bg-primary/10 ring-2 ring-primary/40" : "border-border"}`}
                          >
                            {option}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}

                {(!form.role || !form.specialization || !form.focusTool) && (
                  <p className="text-xs text-amber-500">Complete role and both follow-up selections to continue.</p>
                )}
              </>
            )}

            {step === 3 && (
              <>
                <h2 className="text-2xl font-semibold">Current skills</h2>
                <Input placeholder={selectedSkillHint.placeholder} value={form.skills} onChange={(e) => setForm((f) => ({ ...f, skills: e.target.value }))} />
                <p className="text-sm text-muted-foreground">Tip: {selectedSkillHint.tip}</p>
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
