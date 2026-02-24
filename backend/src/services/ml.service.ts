import axios from "axios";
import { env } from "../utils/env";

export type MlRequest = {
  resumeText: string;
  targetRole: string;
  currentSkills: string[];
  profession: string;
  experienceLevel: string;
};

export type MlResponse = {
  parsedResume: Record<string, unknown>;
  matchScore: number;
  strengths: string[];
  skillGaps: string[];
  transferableSkills: string[];
  roadmap: Array<{ title: string; description: string }>;
  certifications: string[];
};

export async function analyzeResumeWithMl(payload: MlRequest) {
  const { data } = await axios.post<MlResponse>(`${env.ML_SERVICE_URL}/analyze`, payload, {
    timeout: 30000
  });
  return data;
}
