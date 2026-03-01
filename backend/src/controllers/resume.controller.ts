import { Request, Response } from "express";
import { createAnalysis, findUserById, upsertUserByEmail } from "../services/data-store";
import { analyzeResumeWithMl, analyzeResumeWithMlV2 } from "../services/ml.service";
import { extractResumeText } from "../services/resume-text.service";

export async function analyzeResumeController(req: Request, res: Response) {
  const userId = req.user?.userId;
  const userEmail = req.user?.email;
  if (!userId) return res.status(401).json({ message: "Unauthorized" });

  const file = req.file;
  if (!file) return res.status(400).json({ message: "Resume file is required" });

  let user = await findUserById(userId);
  if (!user && userEmail) {
    user = await upsertUserByEmail(userEmail);
  }
  if (!user) return res.status(404).json({ message: "User not found. Please login again." });

  const extracted = await extractResumeText(file.buffer);
  const resumeText = extracted.text;

  const mlResult = await analyzeResumeWithMl({
    resumeText,
    targetRole: user.targetRole || "Software Engineer",
    currentSkills: user.skills,
    profession: user.profession || "Engineer",
    experienceLevel: user.level || "Mid"
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
}

export async function analyzeResumeV2Controller(req: Request, res: Response) {
  const userId = req.user?.userId;
  const userEmail = req.user?.email;
  if (!userId) return res.status(401).json({ message: "Unauthorized" });

  const file = req.file;
  if (!file) return res.status(400).json({ message: "Resume file is required" });

  let user = await findUserById(userId);
  if (!user && userEmail) {
    user = await upsertUserByEmail(userEmail);
  }
  if (!user) return res.status(404).json({ message: "User not found. Please login again." });

  const extracted = await extractResumeText(file.buffer);
  const resumeText = extracted.text;

  const mlResult = await analyzeResumeWithMlV2({
    resumeText,
    targetRole: user.targetRole || "Software Engineer",
    currentSkills: user.skills,
    profession: user.profession || "Engineer",
    experienceLevel: user.level || "Mid"
  });

  const analysis = await createAnalysis({
    userId: user.id,
    fileName: file.originalname,
    resumeText,
    parsedResume: {
      ...mlResult.parsedResume,
      advancedAnalysis: {
        overall_score: mlResult.overall_score,
        confidence: mlResult.confidence,
        breakdown: mlResult.breakdown,
        explanations: mlResult.explanations,
        skill_insights_count: mlResult.skill_insights.length,
        ats_status: mlResult.ats_analysis.status
      }
    },
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
    certifications: analysis.certifications,
    overall_score: mlResult.overall_score,
    confidence: mlResult.confidence,
    breakdown: mlResult.breakdown,
    explanations: mlResult.explanations,
    skill_insights: mlResult.skill_insights,
    roadmap_advanced: mlResult.roadmap_advanced,
    rewrite_suggestions: mlResult.rewrite_suggestions,
    ats_analysis: mlResult.ats_analysis
  });
}
