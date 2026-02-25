import { Request, Response } from "express";
import { z } from "zod";
import { registerWithProfile, signInWithEmail } from "../services/auth.service";
import { findUserById } from "../services/data-store";
import { env } from "../utils/env";

function setAuthCookie(res: Response, token: string) {
  res.cookie(env.JWT_COOKIE_NAME, token, {
    httpOnly: true,
    secure: env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/"
  });
}

function clearAuthCookie(res: Response) {
  res.clearCookie(env.JWT_COOKIE_NAME, {
    httpOnly: true,
    secure: env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/"
  });
}

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

const registerSchema = z.object({
  fullName: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8)
});

export async function loginController(req: Request, res: Response) {
  try {
    const payload = loginSchema.parse(req.body);
    const result = await signInWithEmail(payload.email, payload.password);
    setAuthCookie(res, result.token);
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
    setAuthCookie(res, result.token);
    return res.json(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ message: "Invalid register payload", errors: error.flatten() });
    }

    return res.status(500).json({ message: "Registration failed" });
  }
}

export function logoutController(_req: Request, res: Response) {
  clearAuthCookie(res);
  return res.json({ message: "Logged out" });
}

export async function meController(req: Request, res: Response) {
  if (!req.user) {
    return res.status(401).json({ message: "No token" });
  }

  const dbUser = await findUserById(req.user.userId);

  const onboardingComplete = Boolean(
    dbUser?.profession &&
      dbUser.targetRole &&
      dbUser.level &&
      Array.isArray(dbUser.skills) &&
      dbUser.skills.length > 0
  );

  return res.json({
    message: "Protected data",
    user: {
      ...req.user,
      profession: dbUser?.profession,
      targetRole: dbUser?.targetRole,
      level: dbUser?.level,
      skills: dbUser?.skills ?? [],
      goal: dbUser?.goal
    },
    onboardingComplete
  });
}
