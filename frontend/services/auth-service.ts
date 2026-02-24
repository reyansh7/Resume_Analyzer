import { api } from "@/services/api";

export type AuthResponse = {
  token: string;
  user: { id: string; email: string };
};

export type RegisterPayload = {
  fullName: string;
  email: string;
  password: string;
  profession: string;
  targetRole: string;
  level: string;
  skills: string[];
  goal?: string;
};

export async function login(email: string, password: string) {
  const { data } = await api.post<AuthResponse>("/auth/login", { email, password });
  return data;
}

export async function register(payload: RegisterPayload) {
  const { data } = await api.post<AuthResponse>("/auth/register", payload);
  return data;
}
