import { NextFunction, Request, Response } from "express";
import jwt from "jsonwebtoken";
import { env } from "../utils/env";

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  const rawHeaderToken = authHeader?.startsWith("Bearer ") ? authHeader.split(" ")[1] : undefined;
  const headerToken = rawHeaderToken && rawHeaderToken.trim() !== "" ? rawHeaderToken : undefined;
  const cookieToken = req.cookies?.[env.JWT_COOKIE_NAME] as string | undefined;
  const token = headerToken ?? cookieToken;

  if (!token) {
    return res.status(401).json({ message: "No token" });
  }

  try {
    const payload = jwt.verify(token, env.JWT_SECRET) as { userId: string; email: string };
    req.user = payload;
    next();
  } catch {
    return res.status(403).json({ message: "Invalid token" });
  }
}

// Optional auth middleware for public endpoints like resume analysis
export function optionalAuthMiddleware(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  const rawHeaderToken = authHeader?.startsWith("Bearer ") ? authHeader.split(" ")[1] : undefined;
  const headerToken = rawHeaderToken && rawHeaderToken.trim() !== "" ? rawHeaderToken : undefined;
  const cookieToken = req.cookies?.[env.JWT_COOKIE_NAME] as string | undefined;
  const token = headerToken ?? cookieToken;

  // If token exists, verify it; otherwise allow access
  if (token) {
    try {
      const payload = jwt.verify(token, env.JWT_SECRET) as { userId: string; email: string };
      req.user = payload;
    } catch {
      // Token invalid but don't block - optional auth
    }
  }
  
  next();
}
