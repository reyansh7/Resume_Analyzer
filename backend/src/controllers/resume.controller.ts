import { NextFunction, Request, Response } from "express";
import axios from "axios";
import { randomUUID } from "crypto";
import { createAnalysis, findUserById, upsertUserByEmail } from "../services/data-store";
import { analyzeResumeWithMl, analyzeResumeWithMlV2 } from "../services/ml.service";
import { extractResumeText } from "../services/resume-text.service";

function shouldFallbackToV1(error: unknown) {
  if (!axios.isAxiosError(error)) {
    return false;
  }

  const status = error.response?.status;
  if (status === 500 || status === 502 || status === 503 || status === 504) {
    return true;
  }

  if (!status) {
    return error.code === "ECONNABORTED" || error.code === "ERR_NETWORK" || error.code === "ECONNRESET";
  }

  return false;
}

const ROLE_SKILL_MAP: Record<string, string[]> = {
  "software engineer": ["python", "typescript", "react", "node", "docker", "kubernetes", "sql", "aws", "system design"],
  "data analyst": ["sql", "python", "tableau", "power bi", "statistics", "pandas", "excel", "data visualization"],
  "product manager": ["roadmapping", "stakeholder management", "analytics", "agile", "a/b testing", "user research"],
  "devops engineer": ["docker", "kubernetes", "terraform", "aws", "ci/cd", "linux", "monitoring", "python"]
};

function normalizeRole(role: string) {
  const cleaned = (role || "software engineer").trim().toLowerCase();
  if (ROLE_SKILL_MAP[cleaned]) return cleaned;
  return "software engineer";
}

function buildFallbackBaseResult(input: {
  resumeText: string;
  targetRole: string;
  currentSkills: string[];
  profession: string;
  experienceLevel: string;
}) {
  const roleKey = normalizeRole(input.targetRole);
  const roleSkills = ROLE_SKILL_MAP[roleKey] ?? ROLE_SKILL_MAP["software engineer"];

  const lowered = input.resumeText.toLowerCase();
  const profileSkills = (input.currentSkills ?? []).map((skill) => skill.toLowerCase());

  const strengths = roleSkills.filter((skill) => lowered.includes(skill) || profileSkills.includes(skill)).slice(0, 6);
  const skillGaps = roleSkills.filter((skill) => !strengths.includes(skill)).slice(0, 6);
  const transferableSkills = ["Problem Solving", "Communication", "Collaboration"].filter((item) => item.length > 0);

  const coverage = roleSkills.length > 0 ? strengths.length / roleSkills.length : 0;
  const matchScore = Math.max(35, Math.min(92, Math.round(40 + coverage * 55)));

  const roadmap = skillGaps.slice(0, 4).map((skill, index) => ({
    title: `Close ${skill} gap`,
    description: `Timeline: Week ${index + 1}. Deliverable: complete one practical task using ${skill}. Success criteria: add a measurable bullet in your resume.`
  }));

  return {
    parsedResume: {
      profession: input.profession,
      targetRole: input.targetRole,
      experienceLevel: input.experienceLevel,
      skillsExtracted: strengths,
      wordCount: input.resumeText.split(/\s+/).filter(Boolean).length,
      resumePreview: input.resumeText.slice(0, 400),
      modelUsed: "backend-local-fallback"
    },
    matchScore,
    strengths,
    skillGaps,
    transferableSkills,
    roadmap,
    certifications: [] as string[],
    predictedCategory: undefined,
    predictedConfidence: undefined
  };
}

function buildFallbackV2FromBase(base: ReturnType<typeof buildFallbackBaseResult>) {
  const overall = base.matchScore;
  const atsStatus: "ATS Safe" | "Needs Optimization" | "High Rejection Risk" = overall >= 70 ? "Needs Optimization" : "High Rejection Risk";
  return {
    ...base,
    overall_score: overall,
    confidence: 0.62,
    breakdown: {
      technical_skills: overall,
      soft_skills: Math.max(45, overall - 10),
      experience_match: Math.max(40, overall - 8),
      education_match: Math.max(42, overall - 6)
    },
    explanations: {
      technical_skills: "Generated via backend fallback due temporary ML unavailability.",
      soft_skills: "Estimated from available resume text and profile context.",
      experience_match: "Estimated from role alignment and extracted keywords.",
      education_match: "Estimated from available resume sections."
    },
    skill_insights: base.skillGaps.map((skill) => ({
      skill,
      detected_from: "Fallback analysis",
      confidence: 0.55,
      related_missing_skills: [],
      improvement_suggestions: `Add one quantified bullet showing impact for ${skill}.`,
      resources: []
    })),
    roadmap_advanced: {
      "30_day_plan": [],
      "60_day_plan": [],
      "90_day_plan": []
    },
    rewrite_suggestions: [],
    ats_analysis: {
      ats_score: Math.max(40, Math.min(85, overall - 5)),
      status: atsStatus,
      issues: ["Detailed ATS diagnostics unavailable in fallback mode"]
    }
  };
}

export async function analyzeResumeController(req: Request, res: Response, next: NextFunction) {
  try {
    const requestId = req.requestId;
    const userId = req.user?.userId;
    const userEmail = req.user?.email;
    // Allow guest analysis without authentication

    const file = req.file;
    if (!file) return res.status(400).json({ message: "Resume file is required", requestId });

    let user: any = null;
    if (userId) {
      user = await findUserById(userId);
      if (!user && userEmail) {
        user = await upsertUserByEmail(userEmail);
      }
    }

    let extracted;
    try {
      extracted = await extractResumeText(file.buffer);
    } catch {
      return res.status(400).json({
        message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
        requestId
      });
    }
    const resumeText = extracted.text;

    if (!resumeText.trim()) {
      return res.status(400).json({
        message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
        requestId
      });
    }

    let mlResult;
    try {
      mlResult = await analyzeResumeWithMl({
        resumeText,
        targetRole: user?.targetRole || "Software Engineer",
        currentSkills: user?.skills || [],
        profession: user?.profession || "Engineer",
        experienceLevel: user?.level || "Mid"
      }, {
        requestId,
        uploadFileName: file.originalname,
        route: "analyze"
      });
    } catch (error) {
      console.warn(`[trace] requestId=${requestId ?? "n/a"} route=analyze fallback=local reason=ml_failure error=${error instanceof Error ? error.message : "unknown"}`);
      mlResult = buildFallbackBaseResult({
        resumeText,
        targetRole: user?.targetRole || "Software Engineer",
        currentSkills: user?.skills || [],
        profession: user?.profession || "Engineer",
        experienceLevel: user?.level || "Mid"
      });
    }

    let analysis;
    try {
      analysis = await createAnalysis({
        userId: user?.id,
        fileName: file.originalname,
        resumeText,
        parsedResume: mlResult.parsedResume,
        matchScore: mlResult.matchScore,
        strengths: mlResult.strengths,
        skillGaps: mlResult.skillGaps,
        transferableSkills: mlResult.transferableSkills,
        roadmap: mlResult.roadmap,
        certifications: mlResult.certifications
      });
    } catch (error) {
      console.warn(`[trace] requestId=${requestId ?? "n/a"} route=analyze persistence=fallback reason=${error instanceof Error ? error.message : "unknown"}`);
      analysis = {
        id: randomUUID(),
        userId: user?.id,
        fileName: file.originalname,
        resumeText,
        parsedResume: mlResult.parsedResume,
        matchScore: mlResult.matchScore,
        strengths: mlResult.strengths,
        skillGaps: mlResult.skillGaps,
        transferableSkills: mlResult.transferableSkills,
        roadmap: mlResult.roadmap,
        certifications: mlResult.certifications
      };
    }

    return res.json({
      id: analysis.id,
      matchScore: analysis.matchScore,
      parsedResume: analysis.parsedResume,
      strengths: analysis.strengths,
      skillGaps: analysis.skillGaps,
      transferableSkills: analysis.transferableSkills,
      roadmap: analysis.roadmap,
      certifications: analysis.certifications,
      predictedCategory: mlResult?.predictedCategory,
      predictedConfidence: mlResult?.predictedConfidence
    });
  } catch (error) {
    return next(error);
  }
}

export async function analyzeResumeV2Controller(req: Request, res: Response, next: NextFunction) {
  try {
    const requestId = req.requestId;
    const userId = req.user?.userId;
    const userEmail = req.user?.email;
    // Allow guest analysis without authentication

    const file = req.file;
    if (!file) return res.status(400).json({ message: "Resume file is required", requestId });

    let user: any = null;
    if (userId) {
      user = await findUserById(userId);
      if (!user && userEmail) {
        user = await upsertUserByEmail(userEmail);
      }
    }

    let extracted;
    try {
      extracted = await extractResumeText(file.buffer);
    } catch {
      return res.status(400).json({
        message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
        requestId
      });
    }
    const resumeText = extracted.text;

    if (!resumeText.trim()) {
      return res.status(400).json({
        message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
        requestId
      });
    }

    let baseMlResult: Awaited<ReturnType<typeof analyzeResumeWithMl>>;
    let advancedMlResult: Awaited<ReturnType<typeof analyzeResumeWithMlV2>> | null = null;
    const fallbackBase = buildFallbackBaseResult({
      resumeText,
      targetRole: user?.targetRole || "Software Engineer",
      currentSkills: user?.skills || [],
      profession: user?.profession || "Engineer",
      experienceLevel: user?.level || "Mid"
    });

    try {
      advancedMlResult = await analyzeResumeWithMlV2({
        resumeText,
        targetRole: user?.targetRole || "Software Engineer",
        currentSkills: user?.skills || [],
        profession: user?.profession || "Engineer",
        experienceLevel: user?.level || "Mid"
      }, {
        requestId,
        uploadFileName: file.originalname,
        route: "analyze/v2"
      });
      baseMlResult = advancedMlResult;
    } catch (error) {
      if (!shouldFallbackToV1(error)) {
        console.warn(
          `[trace] requestId=${requestId ?? "n/a"} route=analyze/v2 fallback=local reason=non_transient_v2_failure uploadFile=${file.originalname}`
        );
        const localFallback = buildFallbackV2FromBase(fallbackBase);
        advancedMlResult = localFallback;
        baseMlResult = localFallback;
      } else {
        console.warn(
          `[trace] requestId=${requestId ?? "n/a"} route=analyze/v2 fallback=v1 reason=transient_v2_failure uploadFile=${file.originalname}`
        );

        try {
          baseMlResult = await analyzeResumeWithMl({
            resumeText,
            targetRole: user.targetRole || "Software Engineer",
            currentSkills: user.skills,
            profession: user.profession || "Engineer",
            experienceLevel: user.level || "Mid"
          }, {
            requestId,
            uploadFileName: file.originalname,
            route: "analyze/v2"
          });
        } catch (fallbackError) {
          console.warn(
            `[trace] requestId=${requestId ?? "n/a"} route=analyze/v2 fallback=local reason=v1_failure uploadFile=${file.originalname} error=${fallbackError instanceof Error ? fallbackError.message : "unknown"}`
          );
          const localFallback = buildFallbackV2FromBase(fallbackBase);
          advancedMlResult = localFallback;
          baseMlResult = localFallback;
        }
      }
    }

    let analysis;
    try {
      analysis = await createAnalysis({
        userId: user?.id,
        fileName: file.originalname,
        resumeText,
        parsedResume: {
          ...baseMlResult.parsedResume,
          ...(advancedMlResult
            ? {
                advancedAnalysis: {
                  overall_score: advancedMlResult.overall_score,
                  confidence: advancedMlResult.confidence,
                  breakdown: advancedMlResult.breakdown,
                  explanations: advancedMlResult.explanations,
                  skill_insights_count: advancedMlResult.skill_insights.length,
                  ats_status: advancedMlResult.ats_analysis.status
                }
              }
            : {})
        },
        matchScore: baseMlResult.matchScore,
        strengths: baseMlResult.strengths,
        skillGaps: baseMlResult.skillGaps,
        transferableSkills: baseMlResult.transferableSkills,
        roadmap: baseMlResult.roadmap,
        certifications: baseMlResult.certifications
      });
    } catch (error) {
      console.warn(`[trace] requestId=${requestId ?? "n/a"} route=analyze/v2 persistence=fallback reason=${error instanceof Error ? error.message : "unknown"}`);
      analysis = {
        id: randomUUID(),
        userId: user?.id,
        fileName: file.originalname,
        resumeText,
        parsedResume: {
          ...baseMlResult.parsedResume,
          ...(advancedMlResult
            ? {
                advancedAnalysis: {
                  overall_score: advancedMlResult.overall_score,
                  confidence: advancedMlResult.confidence,
                  breakdown: advancedMlResult.breakdown,
                  explanations: advancedMlResult.explanations,
                  skill_insights_count: advancedMlResult.skill_insights.length,
                  ats_status: advancedMlResult.ats_analysis.status
                }
              }
            : {})
        },
        matchScore: baseMlResult.matchScore,
        strengths: baseMlResult.strengths,
        skillGaps: baseMlResult.skillGaps,
        transferableSkills: baseMlResult.transferableSkills,
        roadmap: baseMlResult.roadmap,
        certifications: baseMlResult.certifications
      };
    }

    return res.json({
      id: analysis.id,
      matchScore: analysis.matchScore,
      parsedResume: analysis.parsedResume,
      strengths: analysis.strengths,
      skillGaps: analysis.skillGaps,
      transferableSkills: analysis.transferableSkills,
      roadmap: analysis.roadmap,
      certifications: analysis.certifications,
      predictedCategory: baseMlResult?.predictedCategory,
      predictedConfidence: baseMlResult?.predictedConfidence,
      ...(advancedMlResult
        ? {
            overall_score: advancedMlResult.overall_score,
            confidence: advancedMlResult.confidence,
            breakdown: advancedMlResult.breakdown,
            explanations: advancedMlResult.explanations,
            skill_insights: advancedMlResult.skill_insights,
            roadmap_advanced: advancedMlResult.roadmap_advanced,
            rewrite_suggestions: advancedMlResult.rewrite_suggestions,
            ats_analysis: advancedMlResult.ats_analysis
          }
        : {})
    });
  } catch (error) {
    return next(error);
  }
}
