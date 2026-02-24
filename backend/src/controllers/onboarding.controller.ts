import { Request, Response } from "express";
import { z } from "zod";
import { updateUserOnboarding } from "../services/data-store";

const schema = z.object({
  profession: z.string().min(1),
  targetRole: z.string().min(1),
  level: z.string().min(1),
  skills: z.array(z.string()).default([]),
  goal: z.string().optional()
});

export async function saveOnboardingController(req: Request, res: Response) {
  const userId = req.user?.userId;
  if (!userId) return res.status(401).json({ message: "Unauthorized" });

  const payload = schema.parse(req.body);

  await updateUserOnboarding(userId, {
    profession: payload.profession,
    targetRole: payload.targetRole,
    level: payload.level,
    skills: payload.skills,
    goal: payload.goal
  });

  return res.json({ message: "Onboarding saved" });
}
