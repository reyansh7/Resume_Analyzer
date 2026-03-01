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

export type MlSkillInsight = {
  skill: string;
  detected_from: string;
  confidence: number;
  related_missing_skills: string[];
  improvement_suggestions: string;
  resources: Array<{ title: string; type: string; link: string }>;
};

export type MlRoadmapTask = {
  skill: string;
  title: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  estimated_hours: number;
  priority_score: number;
  suggested_courses: string[];
  youtube_links: string[];
  leetcode_problems: string[];
  details: string;
};

export type MlResponseV2 = MlResponse & {
  overall_score: number;
  confidence: number;
  breakdown: {
    technical_skills: number;
    soft_skills: number;
    experience_match: number;
    education_match: number;
  };
  explanations: {
    technical_skills: string;
    soft_skills: string;
    experience_match: string;
    education_match: string;
  };
  skill_insights: MlSkillInsight[];
  roadmap_advanced: {
    "30_day_plan": MlRoadmapTask[];
    "60_day_plan": MlRoadmapTask[];
    "90_day_plan": MlRoadmapTask[];
  };
  rewrite_suggestions: Array<{
    section: string;
    before: string;
    after: string;
    improvement_type: string;
  }>;
  ats_analysis: {
    ats_score: number;
    status: "ATS Safe" | "Needs Optimization" | "High Rejection Risk";
    issues: string[];
  };
};

export async function analyzeResumeWithMl(payload: MlRequest) {
  const { data } = await axios.post<MlResponse>(`${env.ML_SERVICE_URL}/analyze`, payload, {
    timeout: 30000
  });
  return data;
}

export async function analyzeResumeWithMlV2(payload: MlRequest) {
  const { data } = await axios.post<MlResponseV2>(`${env.ML_SERVICE_URL}/analyze/v2`, payload, {
    timeout: 45000
  });
  return data;
}
