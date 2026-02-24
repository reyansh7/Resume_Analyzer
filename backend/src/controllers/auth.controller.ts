import { Request, Response } from "express";
import { z } from "zod";
import { registerWithProfile, signInWithEmail } from "../services/auth.service";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

const registerSchema = z.object({
  fullName: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
  profession: z.string().min(1),
  targetRole: z.string().min(1),
  level: z.string().min(1),
  skills: z.array(z.string()).default([]),
  goal: z.string().optional()
});

export async function loginController(req: Request, res: Response) {
  try {
    const payload = loginSchema.parse(req.body);
    const result = await signInWithEmail(payload.email, payload.password);
    return res.json(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ message: "Invalid login payload", errors: error.flatten() });
    }

    if (error instanceof Error && error.message === "Invalid credentials") {
      return res.status(401).json({ message: "Invalid credentials" });
    }

    return res.status(500).json({ message: "Login failed" });
  }
}

export async function registerController(req: Request, res: Response) {
  try {
    const payload = registerSchema.parse(req.body);
    const result = await registerWithProfile(payload);
    return res.json(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ message: "Invalid register payload", errors: error.flatten() });
    }

    return res.status(500).json({ message: "Registration failed" });
  }
}
