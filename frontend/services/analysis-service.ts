import { api } from "@/services/api";

export type AnalysisResult = {
  id: string;
  matchScore: number;
  strengths: string[];
  skillGaps: string[];
  transferableSkills: string[];
  roadmap: Array<{ title: string; description: string }>;
  certifications: string[];
};

export async function uploadResume(formData: FormData) {
  const { data } = await api.post<AnalysisResult>("/resume/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}
