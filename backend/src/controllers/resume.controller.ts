import { Request, Response } from "express";
import pdfParse from "pdf-parse";
import { createAnalysis, findUserById } from "../services/data-store";
import { analyzeResumeWithMl } from "../services/ml.service";

export async function analyzeResumeController(req: Request, res: Response) {
  const userId = req.user?.userId;
  if (!userId) return res.status(401).json({ message: "Unauthorized" });

  const file = req.file;
  if (!file) return res.status(400).json({ message: "Resume file is required" });

  const user = await findUserById(userId);
  if (!user) return res.status(404).json({ message: "User not found" });

  const parsedPdf = await pdfParse(file.buffer);
  const resumeText = parsedPdf.text || "";

  const mlResult = await analyzeResumeWithMl({
    resumeText,
    targetRole: user.targetRole || "Software Engineer",
    currentSkills: user.skills,
    profession: user.profession || "Engineer",
    experienceLevel: user.level || "Mid"
  });

  const analysis = await createAnalysis({
    userId,
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
    strengths: analysis.strengths,
    skillGaps: analysis.skillGaps,
    transferableSkills: analysis.transferableSkills,
    roadmap: analysis.roadmap,
    certifications: analysis.certifications
  });
}
