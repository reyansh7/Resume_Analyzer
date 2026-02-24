import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const envSchema = z.object({
  PORT: z.coerce.number().default(8080),
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  DIRECT_URL: z.string().min(1).optional(),
  JWT_SECRET: z.string().min(10),
  CORS_ORIGIN: z.string().url(),
  ML_SERVICE_URL: z.string().url(),
  USE_IN_MEMORY_DB: z.coerce.boolean().default(false)
});

export const env = envSchema.parse(process.env);
