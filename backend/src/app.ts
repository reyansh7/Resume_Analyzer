import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import authRoutes from "./routes/auth.routes";
import onboardingRoutes from "./routes/onboarding.routes";
import resumeRoutes from "./routes/resume.routes";
import { env } from "./utils/env";
import { errorMiddleware } from "./middleware/error.middleware";

export const app = express();

app.use(
  cors({
    origin: env.CORS_ORIGIN,
    credentials: true
  })
);
app.use(express.json({ limit: "2mb" }));
app.use(cookieParser());

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "backend", timestamp: new Date().toISOString() });
});

app.get("/api", (_req, res) => {
  res.json({
    service: "resume-analyzer-backend",
    status: "ok",
    routes: {
      health: "/health",
      authLogin: "/api/auth/login",
      onboarding: "/api/onboarding",
      resumeAnalyze: "/api/resume/analyze",
      resumeAnalyzeV2: "/api/resume/analyze/v2"
    }
  });
});

app.use("/api/auth", authRoutes);
app.use("/api/onboarding", onboardingRoutes);
app.use("/api/resume", resumeRoutes);
app.use(errorMiddleware);
