import { randomUUID } from "crypto";
import { getDatabase } from "./mongodb";
import { env } from "../utils/env";

type UserRecord = {
  id: string;
  fullName?: string;
  email: string;
  password?: string;
  profession?: string;
  targetRole?: string;
  level?: string;
  skills: string[];
  goal?: string;
};

type AnalysisInput = {
  userId: string;
  fileName: string;
  resumeText: string;
  parsedResume: Record<string, unknown>;
  matchScore: number;
  strengths: string[];
  skillGaps: string[];
  transferableSkills: string[];
  roadmap: Array<{ title: string; description: string }>;
  certifications: string[];
};

const inMemoryUsers = new Map<string, UserRecord>();
const inMemoryUsersByEmail = new Map<string, string>();

const inMemoryAnalyses = new Map<string, AnalysisInput & { id: string }>();
let forceInMemoryFallback = false;

function useMemoryDb() {
  return env.USE_IN_MEMORY_DB || forceInMemoryFallback;
}

function shouldFallbackToMemoryDb(error: unknown) {
  const message = error instanceof Error ? error.message : String(error ?? "");
  const lowered = message.toLowerCase();

  return (
    lowered.includes("ssl routines") ||
    lowered.includes("tlsv1 alert") ||
    lowered.includes("certificate") ||
    lowered.includes("mongo") ||
    lowered.includes("server selection") ||
    lowered.includes("econnrefused") ||
    lowered.includes("enotfound") ||
    lowered.includes("etimedout")
  );
}

function activateMemoryFallback(error: unknown) {
  if (!forceInMemoryFallback) {
    const message = error instanceof Error ? error.message : String(error ?? "");
    console.warn(`[data-store] Mongo unavailable, switching to in-memory fallback. reason=${message}`);
  }
  forceInMemoryFallback = true;
}

function redactSensitiveResumeData(text: string): string {
  return text
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[REDACTED_EMAIL]")
    .replace(/(\+?\d[\d\s().-]{7,}\d)/g, "[REDACTED_PHONE]")
    .replace(/https?:\/\/(www\.)?(linkedin\.com|github\.com)\/[^\s]+/gi, "[REDACTED_PROFILE_URL]");
}

function normalizeResumeTextForStorage(text: string): string {
  if (!env.STORE_RAW_RESUME_TEXT) {
    return "";
  }

  const redacted = redactSensitiveResumeData(text || "");
  return redacted.slice(0, env.RESUME_TEXT_MAX_CHARS);
}

type UserDocument = UserRecord & {
  id: string;
  createdAt: Date;
  updatedAt: Date;
};

type AnalysisDocument = AnalysisInput & {
  id: string;
  createdAt: Date;
};

function toUserRecord(user: UserDocument): UserRecord {
  return {
    id: user.id,
    fullName: user.fullName ?? undefined,
    email: user.email,
    password: user.password ?? undefined,
    profession: user.profession ?? undefined,
    targetRole: user.targetRole ?? undefined,
    level: user.level ?? undefined,
    skills: user.skills ?? [],
    goal: user.goal ?? undefined
  };
}

async function usersCollection() {
  const db = await getDatabase();
  return db.collection<UserDocument>("users");
}

async function analysesCollection() {
  const db = await getDatabase();
  return db.collection<AnalysisDocument>("resume_analyses");
}

export async function upsertUserByEmail(email: string): Promise<UserRecord> {
  if (useMemoryDb()) {
    const existingId = inMemoryUsersByEmail.get(email);
    if (existingId) {
      const existing = inMemoryUsers.get(existingId);
      if (existing) return existing;
    }

    const id = randomUUID();
    const user: UserRecord = { id, email, skills: [] };
    inMemoryUsers.set(id, user);
    inMemoryUsersByEmail.set(email, id);
    return user;
  }

  try {
    const users = await usersCollection();
    const now = new Date();
    await users.updateOne(
      { email },
      {
        $set: { updatedAt: now },
        $setOnInsert: { id: randomUUID(), email, skills: [], createdAt: now }
      },
      { upsert: true }
    );

    const user = await users.findOne({ email });
    if (!user) {
      throw new Error("Failed to upsert user");
    }

    return toUserRecord(user);
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return upsertUserByEmail(email);
  }
}

export async function findUserById(userId: string): Promise<UserRecord | null> {
  if (useMemoryDb()) {
    return inMemoryUsers.get(userId) ?? null;
  }

  try {
    const users = await usersCollection();
    const user = await users.findOne({ id: userId });
    if (!user) return null;

    return toUserRecord(user);
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return findUserById(userId);
  }
}

export async function findUserByEmail(email: string): Promise<UserRecord | null> {
  if (useMemoryDb()) {
    const userId = inMemoryUsersByEmail.get(email);
    if (!userId) return null;
    return inMemoryUsers.get(userId) ?? null;
  }

  try {
    const users = await usersCollection();
    const user = await users.findOne({ email });
    if (!user) return null;

    return toUserRecord(user);
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return findUserByEmail(email);
  }
}

export async function createOrUpdateUserProfile(input: {
  email: string;
  password: string;
  fullName: string;
  profession: string;
  targetRole: string;
  level: string;
  skills: string[];
  goal?: string;
}): Promise<UserRecord> {
  if (useMemoryDb()) {
    const existing = await findUserByEmail(input.email);

    if (existing) {
      const next: UserRecord = {
        ...existing,
        fullName: input.fullName,
        password: input.password,
        profession: input.profession,
        targetRole: input.targetRole,
        level: input.level,
        skills: input.skills,
        goal: input.goal
      };
      inMemoryUsers.set(existing.id, next);
      return next;
    }

    const id = randomUUID();
    const created: UserRecord = {
      id,
      fullName: input.fullName,
      email: input.email,
      password: input.password,
      profession: input.profession,
      targetRole: input.targetRole,
      level: input.level,
      skills: input.skills,
      goal: input.goal
    };
    inMemoryUsers.set(id, created);
    inMemoryUsersByEmail.set(input.email, id);
    return created;
  }

  try {
    const users = await usersCollection();
    const now = new Date();

    await users.updateOne(
      { email: input.email },
      {
        $set: {
          fullName: input.fullName,
          password: input.password,
          profession: input.profession,
          targetRole: input.targetRole,
          level: input.level,
          skills: input.skills,
          goal: input.goal,
          updatedAt: now
        },
        $setOnInsert: {
          id: randomUUID(),
          email: input.email,
          createdAt: now
        }
      },
      { upsert: true }
    );

    const user = await users.findOne({ email: input.email });
    if (!user) {
      throw new Error("Failed to upsert user profile");
    }

    return toUserRecord(user);
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return createOrUpdateUserProfile(input);
  }
}

export async function upsertUserCredentials(input: {
  fullName: string;
  email: string;
  password: string;
}): Promise<UserRecord> {
  if (useMemoryDb()) {
    const existing = await findUserByEmail(input.email);

    if (existing) {
      const next: UserRecord = {
        ...existing,
        fullName: input.fullName,
        password: input.password
      };
      inMemoryUsers.set(existing.id, next);
      return next;
    }

    const id = randomUUID();
    const created: UserRecord = {
      id,
      fullName: input.fullName,
      email: input.email,
      password: input.password,
      skills: []
    };
    inMemoryUsers.set(id, created);
    inMemoryUsersByEmail.set(input.email, id);
    return created;
  }

  try {
    const users = await usersCollection();
    const now = new Date();

    await users.updateOne(
      { email: input.email },
      {
        $set: {
          fullName: input.fullName,
          password: input.password,
          updatedAt: now
        },
        $setOnInsert: {
          id: randomUUID(),
          email: input.email,
          skills: [],
          createdAt: now
        }
      },
      { upsert: true }
    );

    const user = await users.findOne({ email: input.email });
    if (!user) {
      throw new Error("Failed to upsert user credentials");
    }

    return toUserRecord(user);
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return upsertUserCredentials(input);
  }
}

export async function updateUserOnboarding(
  userId: string,
  payload: { profession: string; targetRole: string; level: string; skills: string[]; goal?: string }
): Promise<void> {
  if (useMemoryDb()) {
    const existing = inMemoryUsers.get(userId);
    if (!existing) return;

    inMemoryUsers.set(userId, {
      ...existing,
      profession: payload.profession,
      targetRole: payload.targetRole,
      level: payload.level,
      skills: payload.skills,
      goal: payload.goal
    });
    return;
  }

  try {
    const users = await usersCollection();
    await users.updateOne(
      { id: userId },
      {
        $set: {
          profession: payload.profession,
          targetRole: payload.targetRole,
          level: payload.level,
          skills: payload.skills,
          goal: payload.goal,
          updatedAt: new Date()
        }
      }
    );
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return updateUserOnboarding(userId, payload);
  }
}

export async function createAnalysis(input: AnalysisInput) {
  const safeResumeText = normalizeResumeTextForStorage(input.resumeText);

  if (useMemoryDb()) {
    const id = randomUUID();
    const analysis = { id, ...input, resumeText: safeResumeText };
    inMemoryAnalyses.set(id, analysis);
    return analysis;
  }

  try {
    const analyses = await analysesCollection();
    const id = randomUUID();

    await analyses.insertOne({
      id,
      userId: input.userId,
      fileName: input.fileName,
      resumeText: safeResumeText,
      parsedResume: input.parsedResume,
      matchScore: input.matchScore,
      strengths: input.strengths,
      skillGaps: input.skillGaps,
      transferableSkills: input.transferableSkills,
      roadmap: input.roadmap,
      certifications: input.certifications,
      createdAt: new Date()
    });

    const analysis = await analyses.findOne({ id });
    if (!analysis) {
      throw new Error("Failed to create analysis");
    }

    return {
      id: analysis.id,
      userId: analysis.userId,
      fileName: analysis.fileName,
      resumeText: analysis.resumeText,
      parsedResume: analysis.parsedResume as Record<string, unknown>,
      matchScore: analysis.matchScore,
      strengths: analysis.strengths,
      skillGaps: analysis.skillGaps,
      transferableSkills: analysis.transferableSkills,
      roadmap: analysis.roadmap as Array<{ title: string; description: string }>,
      certifications: analysis.certifications
    };
  } catch (error) {
    if (!shouldFallbackToMemoryDb(error)) {
      throw error;
    }
    activateMemoryFallback(error);
    return createAnalysis(input);
  }
}
