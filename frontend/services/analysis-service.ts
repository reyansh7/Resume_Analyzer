import { api } from "@/services/api";
import { isAxiosError } from "axios";

export type AnalysisResult = {
  id: string;
  matchScore: number;
  parsedResume?: {
    profession?: string;
    targetRole?: string;
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
    educationHighlights?: string[];
    softSkillsHighlights?: string[];
    overviewSource?: "gemini" | "ollama" | "local";
    overviewModel?: string | null;
    roadmapSource?: "ollama" | "gemini" | "local";
    roadmapModel?: string | null;
    modelUsed?: string;
  };
  strengths: string[];
  skillGaps: string[];
  transferableSkills: string[];
  roadmap: Array<{ title: string; description: string }>;
  certifications: string[];
  overall_score?: number;
  confidence?: number;
  breakdown?: {
    technical_skills: number;
    soft_skills: number;
    experience_match: number;
    education_match: number;
  };
  explanations?: {
    technical_skills: string;
    soft_skills: string;
    experience_match: string;
    education_match: string;
  };
  skill_insights?: Array<{
    skill: string;
    detected_from: string;
    confidence: number;
    related_missing_skills: string[];
    improvement_suggestions: string;
    resources: Array<{ title: string; type: string; link: string }>;
  }>;
  roadmap_advanced?: {
    "30_day_plan": Array<{
      skill: string;
      title: string;
      difficulty: "Beginner" | "Intermediate" | "Advanced";
      estimated_hours: number;
      priority_score: number;
      suggested_courses: string[];
      youtube_links: string[];
      leetcode_problems: string[];
      details: string;
    }>;
    "60_day_plan": Array<{
      skill: string;
      title: string;
      difficulty: "Beginner" | "Intermediate" | "Advanced";
      estimated_hours: number;
      priority_score: number;
      suggested_courses: string[];
      youtube_links: string[];
      leetcode_problems: string[];
      details: string;
    }>;
    "90_day_plan": Array<{
      skill: string;
      title: string;
      difficulty: "Beginner" | "Intermediate" | "Advanced";
      estimated_hours: number;
      priority_score: number;
      suggested_courses: string[];
      youtube_links: string[];
      leetcode_problems: string[];
      details: string;
    }>;
  };
  rewrite_suggestions?: Array<{
    section: string;
    before: string;
    after: string;
    improvement_type: string;
  }>;
  ats_analysis?: {
    ats_score: number;
    status: "ATS Safe" | "Needs Optimization" | "High Rejection Risk";
    issues: string[];
  };
};

export type ServicesHealthResult = {
  status: "ok" | "degraded";
  requestId?: string;
  backend: { status: "ok" | "degraded" | "down" };
  ml: { status: "ok" | "degraded" | "down"; detail?: unknown };
  elapsedMs?: number;
  action?: string;
};

export async function uploadResume(formData: FormData) {
  const { data } = await api.post<AnalysisResult>("/resume/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function uploadResumeV2(formData: FormData) {
  const { data } = await api.post<AnalysisResult>("/resume/analyze/v2", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function analyzeResumeWithFallback(formData: FormData) {
  try {
    return await uploadResumeV2(formData);
  } catch (error) {
    if (!isAxiosError(error)) {
      throw error;
    }

    const status = error.response?.status;

    const shouldFallback =
      status === 404 ||
      status === 405 ||
      status === 500 ||
      status === 502 ||
      status === 503 ||
      status === 504 ||
      (!status && (error.code === "ECONNABORTED" || error.code === "ERR_NETWORK"));

    if (!shouldFallback) {
      throw error;
    }
  }

  return uploadResume(formData);
}

export async function fetchServicesHealth() {
  const { data } = await api.get<ServicesHealthResult>("/health/services", {
    timeout: 6000
  });
  return data;
}
