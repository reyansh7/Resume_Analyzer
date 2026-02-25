import { randomUUID } from "crypto";
import { Prisma } from "@prisma/client";
import { prisma } from "./prisma";
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

function useMemoryDb() {
  return env.USE_IN_MEMORY_DB;
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

  const user = await prisma.user.upsert({
    where: { email },
    update: {},
    create: { email, skills: [] }
  });

  return {
    id: user.id,
    fullName: user.fullName ?? undefined,
    email: user.email,
    password: user.password ?? undefined,
    profession: user.profession ?? undefined,
    targetRole: user.targetRole ?? undefined,
    level: user.level ?? undefined,
    skills: user.skills,
    goal: user.goal ?? undefined
  };
}

export async function findUserById(userId: string): Promise<UserRecord | null> {
  if (useMemoryDb()) {
    return inMemoryUsers.get(userId) ?? null;
  }

  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) return null;

  return {
    id: user.id,
    fullName: user.fullName ?? undefined,
    email: user.email,
    password: user.password ?? undefined,
    profession: user.profession ?? undefined,
    targetRole: user.targetRole ?? undefined,
    level: user.level ?? undefined,
    skills: user.skills,
    goal: user.goal ?? undefined
  };
}

export async function findUserByEmail(email: string): Promise<UserRecord | null> {
  if (useMemoryDb()) {
    const userId = inMemoryUsersByEmail.get(email);
    if (!userId) return null;
    return inMemoryUsers.get(userId) ?? null;
  }

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) return null;

  return {
    id: user.id,
    fullName: user.fullName ?? undefined,
    email: user.email,
    password: user.password ?? undefined,
    profession: user.profession ?? undefined,
    targetRole: user.targetRole ?? undefined,
    level: user.level ?? undefined,
    skills: user.skills,
    goal: user.goal ?? undefined
  };
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

  const user = await prisma.user.upsert({
    where: { email: input.email },
    update: {
      fullName: input.fullName,
      password: input.password,
      profession: input.profession,
      targetRole: input.targetRole,
      level: input.level,
      skills: input.skills,
      goal: input.goal
    },
    create: {
      fullName: input.fullName,
      email: input.email,
      password: input.password,
      profession: input.profession,
      targetRole: input.targetRole,
      level: input.level,
      skills: input.skills,
      goal: input.goal
    }
  });

  return {
    id: user.id,
    fullName: user.fullName ?? undefined,
    email: user.email,
    password: user.password ?? undefined,
    profession: user.profession ?? undefined,
    targetRole: user.targetRole ?? undefined,
    level: user.level ?? undefined,
    skills: user.skills,
    goal: user.goal ?? undefined
  };
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

  const user = await prisma.user.upsert({
    where: { email: input.email },
    update: {
      fullName: input.fullName,
      password: input.password
    },
    create: {
      fullName: input.fullName,
      email: input.email,
      password: input.password,
      skills: []
    }
  });

  return {
    id: user.id,
    fullName: user.fullName ?? undefined,
    email: user.email,
    password: user.password ?? undefined,
    profession: user.profession ?? undefined,
    targetRole: user.targetRole ?? undefined,
    level: user.level ?? undefined,
    skills: user.skills,
    goal: user.goal ?? undefined
  };
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

  await prisma.user.update({
    where: { id: userId },
    data: {
      profession: payload.profession,
      targetRole: payload.targetRole,
      level: payload.level,
      skills: payload.skills,
      goal: payload.goal
    }
  });
}

export async function createAnalysis(input: AnalysisInput) {
  if (useMemoryDb()) {
    const id = randomUUID();
    const analysis = { id, ...input };
    inMemoryAnalyses.set(id, analysis);
    return analysis;
  }

  const analysis = await prisma.resumeAnalysis.create({
    data: {
      userId: input.userId,
      fileName: input.fileName,
      resumeText: input.resumeText,
      parsedResume: input.parsedResume as Prisma.InputJsonValue,
      matchScore: input.matchScore,
      strengths: input.strengths,
      skillGaps: input.skillGaps,
      transferableSkills: input.transferableSkills,
      roadmap: input.roadmap as Prisma.InputJsonValue,
      certifications: input.certifications
    }
  });

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
}
