import { api } from "@/services/api";

export type AnalysisResult = {
  id: string;
  matchScore: number;
  parsedResume?: {
    profession?: string;
    experienceLevel?: string;
    skillsExtracted?: string[];
    skillsFromResumeCount?: number;
    skillsFromProfileCount?: number;
    wordCount?: number;
    resumePreview?: string;
    predictedCategory?: string | null;
    predictionConfidence?: number | null;
    targetCategory?: string | null;
    targetCategoryProbability?: number | null;
    certificationsDetected?: string[];
    awardsDetected?: string[];
    featuredProject?: string | null;
    featuredProjects?: string[];
    featuredExperiences?: string[];
    roadmapSource?: "gemini" | "local";
    roadmapModel?: string | null;
    modelUsed?: string;
  };
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
