import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const booleanFromEnv = z.preprocess((value) => {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "on"].includes(normalized)) return true;
    if (["false", "0", "no", "off", ""].includes(normalized)) return false;
  }
  return value;
}, z.boolean());

const envSchema = z.object({
  PORT: z.coerce.number().default(8080),
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  MONGODB_URI: z.string().min(1),
  MONGODB_DB_NAME: z.string().min(1).default("resume_analyzer"),
  JWT_SECRET: z.string().min(10),
  JWT_EXPIRES_IN: z.string().default("1d"),
  JWT_COOKIE_NAME: z.string().default("access_token"),
  CORS_ORIGIN: z.string().min(1),
  ML_SERVICE_URL: z.string().url(),
  STORE_RAW_RESUME_TEXT: booleanFromEnv.default(false),
  RESUME_TEXT_MAX_CHARS: z.coerce.number().int().positive().default(4000),
  USE_IN_MEMORY_DB: booleanFromEnv.default(false)
}).superRefine((value, ctx) => {
  const jwtSecret = value.JWT_SECRET?.trim() ?? "";
  if (value.NODE_ENV === "production") {
    const looksWeak =
      jwtSecret.length < 32 ||
      /^change_me/i.test(jwtSecret) ||
      /^secret$/i.test(jwtSecret) ||
      /^jwt/i.test(jwtSecret);

    if (looksWeak) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "JWT_SECRET is too weak for production. Use a random secret with at least 32 characters."
      });
    }

    const mongoUri = value.MONGODB_URI.trim();
    const isMongoSrv = /^mongodb\+srv:\/\//i.test(mongoUri);
    const hasTlsParam = /(?:[?&](?:tls|ssl)=true)(?:&|$)/i.test(mongoUri);
    const isLocalHost = /mongodb:\/\/(?:[^@/]+@)?(?:localhost|127\.0\.0\.1|mongodb)(?::\d+)?(?:[,/?]|$)/i.test(mongoUri);

    if (!isLocalHost && !isMongoSrv && !hasTlsParam) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Production MongoDB connection must enforce TLS. Use mongodb+srv://... or add ?tls=true to MONGODB_URI."
      });
    }
  }

  const corsOrigins = value.CORS_ORIGIN
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);

  if (corsOrigins.length === 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "CORS_ORIGIN must include at least one origin."
    });
  }

  for (const origin of corsOrigins) {
    const isWildcardHttps = /^https:\/\/\*\.[a-z0-9.-]+$/i.test(origin);
    const isValidAbsoluteUrl = /^https?:\/\//i.test(origin);

    if (isWildcardHttps) continue;

    if (!isValidAbsoluteUrl) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `CORS_ORIGIN entry \"${origin}\" is invalid. Use full URL(s) or wildcard like https://*.vercel.app`
      });
      continue;
    }

    try {
      new URL(origin);
    } catch {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `CORS_ORIGIN entry \"${origin}\" is not a valid URL.`
      });
    }
  }
});

export const env = envSchema.parse(process.env);
