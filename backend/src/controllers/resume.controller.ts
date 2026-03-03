import { NextFunction, Request, Response } from "express";
import axios from "axios";
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

export async function analyzeResumeController(req: Request, res: Response, next: NextFunction) {
  try {
    const requestId = req.requestId;
    const userId = req.user?.userId;
    const userEmail = req.user?.email;
    if (!userId) return res.status(401).json({ message: "Unauthorized", requestId });

    const file = req.file;
    if (!file) return res.status(400).json({ message: "Resume file is required", requestId });

    let user = await findUserById(userId);
    if (!user && userEmail) {
      user = await upsertUserByEmail(userEmail);
    }
    if (!user) return res.status(404).json({ message: "User not found. Please login again.", requestId });

    const extracted = await extractResumeText(file.buffer);
    const resumeText = extracted.text;

    if (!resumeText.trim()) {
      return res.status(400).json({
        message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
        requestId
      });
    }

    const mlResult = await analyzeResumeWithMl({
      resumeText,
      targetRole: user.targetRole || "Software Engineer",
      currentSkills: user.skills,
      profession: user.profession || "Engineer",
      experienceLevel: user.level || "Mid"
    }, {
      requestId,
      uploadFileName: file.originalname,
      route: "analyze"
    });

    const analysis = await createAnalysis({
      userId: user.id,
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

    return res.json({
      id: analysis.id,
      matchScore: analysis.matchScore,
      parsedResume: analysis.parsedResume,
      strengths: analysis.strengths,
      skillGaps: analysis.skillGaps,
      transferableSkills: analysis.transferableSkills,
      roadmap: analysis.roadmap,
      certifications: analysis.certifications
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
    if (!userId) return res.status(401).json({ message: "Unauthorized", requestId });

    const file = req.file;
    if (!file) return res.status(400).json({ message: "Resume file is required", requestId });

    let user = await findUserById(userId);
    if (!user && userEmail) {
      user = await upsertUserByEmail(userEmail);
    }
    if (!user) return res.status(404).json({ message: "User not found. Please login again.", requestId });

    const extracted = await extractResumeText(file.buffer);
    const resumeText = extracted.text;

    if (!resumeText.trim()) {
      return res.status(400).json({
        message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
        requestId
      });
    }

    let baseMlResult: Awaited<ReturnType<typeof analyzeResumeWithMl>>;
    let advancedMlResult: Awaited<ReturnType<typeof analyzeResumeWithMlV2>> | null = null;

    try {
      advancedMlResult = await analyzeResumeWithMlV2({
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
      baseMlResult = advancedMlResult;
    } catch (error) {
      if (!shouldFallbackToV1(error)) {
        throw error;
      }

      console.warn(
        `[trace] requestId=${requestId ?? "n/a"} route=analyze/v2 fallback=v1 reason=transient_v2_failure uploadFile=${file.originalname}`
      );

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
    }

    const analysis = await createAnalysis({
      userId: user.id,
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

    return res.json({
      id: analysis.id,
      matchScore: analysis.matchScore,
      parsedResume: analysis.parsedResume,
      strengths: analysis.strengths,
      skillGaps: analysis.skillGaps,
      transferableSkills: analysis.transferableSkills,
      roadmap: analysis.roadmap,
      certifications: analysis.certifications,
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
