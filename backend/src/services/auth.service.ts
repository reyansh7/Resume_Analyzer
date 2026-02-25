import { randomBytes, scryptSync, timingSafeEqual } from "crypto";
import jwt from "jsonwebtoken";
import { createOrUpdateUserProfile, findUserByEmail, upsertUserByEmail, upsertUserCredentials } from "./data-store";
import { env } from "../utils/env";

type PublicUser = {
  id: string;
  fullName?: string;
  email: string;
  profession?: string;
  targetRole?: string;
  level?: string;
  skills: string[];
  goal?: string;
};

function hashPassword(password: string) {
  const salt = randomBytes(16).toString("hex");
  const hash = scryptSync(password, salt, 64).toString("hex");
  return `${salt}:${hash}`;
}

function verifyPassword(password: string, stored: string) {
  const [salt, key] = stored.split(":");
  if (!salt || !key) return false;

  const hashBuffer = Buffer.from(key, "hex");
  const verifyBuffer = scryptSync(password, salt, 64);

  if (hashBuffer.length !== verifyBuffer.length) return false;
  return timingSafeEqual(hashBuffer, verifyBuffer);
}

function createAuthToken(user: { id: string; email: string }) {
  const expiresIn: jwt.SignOptions["expiresIn"] = env.JWT_EXPIRES_IN as jwt.SignOptions["expiresIn"];

  return jwt.sign({ userId: user.id, email: user.email }, env.JWT_SECRET, {
    expiresIn
  });
}

function toPublicUser(user: {
  id: string;
  fullName?: string;
  email: string;
  profession?: string;
  targetRole?: string;
  level?: string;
  skills: string[];
  goal?: string;
}): PublicUser {
  return {
    id: user.id,
    fullName: user.fullName,
    email: user.email,
    profession: user.profession,
    targetRole: user.targetRole,
    level: user.level,
    skills: user.skills,
    goal: user.goal
  };
}

export async function signInWithEmail(email: string, password: string) {
  const existing = await findUserByEmail(email);

  if (!existing) {
    const created = await upsertUserByEmail(email);
    const token = createAuthToken(created);
    return { token, user: toPublicUser(created) };
  }

  if (!existing.password) {
    const upgraded = await createOrUpdateUserProfile({
      email,
      password: hashPassword(password),
      fullName: existing.fullName || "",
      profession: existing.profession || "",
      targetRole: existing.targetRole || "",
      level: existing.level || "",
      skills: existing.skills,
      goal: existing.goal
    });
    const token = createAuthToken(upgraded);
    return { token, user: toPublicUser(upgraded) };
  }

  if (!verifyPassword(password, existing.password)) {
    throw new Error("Invalid credentials");
  }

  const token = createAuthToken(existing);
  return { token, user: toPublicUser(existing) };
}

export async function registerWithProfile(input: {
  fullName: string;
  email: string;
  password: string;
}) {
  const user = await upsertUserCredentials({
    fullName: input.fullName,
    email: input.email,
    password: hashPassword(input.password)
  });

  const token = createAuthToken(user);
  return { token, user: toPublicUser(user) };
}

export async function registerWithFullProfile(input: {
  fullName: string;
  email: string;
  password: string;
  profession: string;
  targetRole: string;
  level: string;
  skills: string[];
  goal?: string;
}) {
  const user = await createOrUpdateUserProfile({
    ...input,
    password: hashPassword(input.password)
  });

  const token = createAuthToken(user);
  return { token, user: toPublicUser(user) };
}
