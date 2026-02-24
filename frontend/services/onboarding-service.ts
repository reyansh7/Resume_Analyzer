import { api } from "@/services/api";

export type OnboardingPayload = {
  profession: string;
  targetRole: string;
  level: string;
  skills: string[];
  goal?: string;
};

export async function saveOnboarding(payload: OnboardingPayload) {
  const { data } = await api.post<{ message: string }>("/onboarding", payload);
  return data;
}
