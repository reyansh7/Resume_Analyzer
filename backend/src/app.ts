import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import helmet from "helmet";
import { rateLimit } from "express-rate-limit";
import axios from "axios";
import { randomUUID } from "crypto";
import authRoutes from "./routes/auth.routes";
import onboardingRoutes from "./routes/onboarding.routes";
import resumeRoutes from "./routes/resume.routes";
import { env } from "./utils/env";
import { errorMiddleware } from "./middleware/error.middleware";

export const app = express();

const corsOriginTokens = env.CORS_ORIGIN
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function matchesCorsOrigin(origin: string) {
  for (const token of corsOriginTokens) {
    if (token === origin) {
      return true;
    }

    if (token.includes("*")) {
      const pattern = `^${escapeRegex(token).replace(/\\\*/g, "[^.]+")}$`;
      if (new RegExp(pattern, "i").test(origin)) {
        return true;
      }
    }
  }

  return false;
}

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 50,
  standardHeaders: true,
  legacyHeaders: false,
  message: { message: "Too many auth requests. Please try again later." }
});

const resumeLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { message: "Too many resume analysis requests. Please try again later." }
});

app.use(
  helmet({
    crossOriginResourcePolicy: false
  })
);

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || matchesCorsOrigin(origin)) {
        callback(null, true);
        return;
      }

      callback(new Error(`Origin ${origin} is not allowed by CORS`));
    },
    credentials: true
  })
);

app.use((req, res, next) => {
  const requestId = (req.header("x-request-id") || randomUUID()).trim();
  req.requestId = requestId;
  req.requestStartTime = Date.now();
  res.setHeader("x-request-id", requestId);

  res.on("finish", () => {
    const elapsedMs = Date.now() - (req.requestStartTime ?? Date.now());
    const uploadName = typeof req.file?.originalname === "string" ? req.file.originalname : "n/a";
    console.log(
      `[trace] requestId=${requestId} method=${req.method} path=${req.originalUrl} status=${res.statusCode} elapsedMs=${elapsedMs} uploadFile=${uploadName}`
    );
  });

  next();
});

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

app.get("/api/health/services", async (req, res) => {
  const started = Date.now();

  try {
    const mlResponse = await axios.get<{ status?: string }>(`${env.ML_SERVICE_URL}/health`, {
      timeout: 4000,
      headers: req.requestId ? { "x-request-id": req.requestId } : undefined
    });

    return res.json({
      status: "ok",
      requestId: req.requestId,
      backend: { status: "ok" },
      ml: { status: mlResponse.data?.status === "ok" ? "ok" : "degraded" },
      elapsedMs: Date.now() - started
    });
  } catch (error) {
    const detail = axios.isAxiosError(error)
      ? error.response?.data ?? error.message
      : error instanceof Error
        ? error.message
        : "unknown error";

    return res.status(503).json({
      status: "degraded",
      requestId: req.requestId,
      backend: { status: "ok" },
      ml: { status: "down", detail },
      elapsedMs: Date.now() - started,
      action: "Start ML service on port 8000 and retry."
    });
  }
});

app.use("/api/auth", authLimiter, authRoutes);
app.use("/api/onboarding", onboardingRoutes);
app.use("/api/resume", resumeLimiter, resumeRoutes);
app.use(errorMiddleware);
