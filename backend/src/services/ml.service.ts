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

type MlRequestMeta = {
  requestId?: string;
  uploadFileName?: string;
  route: "analyze" | "analyze/v2";
};

function buildTraceHeaders(meta: MlRequestMeta) {
  const headers: Record<string, string> = {};
  if (meta.requestId) {
    headers["x-request-id"] = meta.requestId;
  }
  if (meta.uploadFileName) {
    headers["x-upload-filename"] = meta.uploadFileName;
  }
  return headers;
}

function shouldRetryMlError(error: unknown) {
  if (!axios.isAxiosError(error)) return false;

  const status = error.response?.status;
  if (!status) {
    return true;
  }

  return status === 502 || status === 503 || status === 504;
}

async function postMlWithRetry<TResponse>(url: string, payload: MlRequest, timeoutMs: number, meta: MlRequestMeta) {
  const headers = buildTraceHeaders(meta);

  try {
    const { data } = await axios.post<TResponse>(url, payload, {
      timeout: timeoutMs,
      headers
    });
    return data;
  } catch (error) {
    if (!shouldRetryMlError(error)) {
      throw error;
    }

    console.warn(
      `[trace] requestId=${meta.requestId ?? "n/a"} route=${meta.route} uploadFile=${meta.uploadFileName ?? "n/a"} retry=1 reason=transient_ml_error`
    );

    await new Promise((resolve) => setTimeout(resolve, 250));

    const { data } = await axios.post<TResponse>(url, payload, {
      timeout: timeoutMs,
      headers
    });
    return data;
  }
}

export async function analyzeResumeWithMl(payload: MlRequest, meta: MlRequestMeta) {
  const started = Date.now();
  const data = await postMlWithRetry<MlResponse>(`${env.ML_SERVICE_URL}/analyze`, payload, 90000, meta);
  console.log(
    `[trace] requestId=${meta.requestId ?? "n/a"} route=${meta.route} uploadFile=${meta.uploadFileName ?? "n/a"} mlElapsedMs=${Date.now() - started}`
  );
  return data;
}

export async function analyzeResumeWithMlV2(payload: MlRequest, meta: MlRequestMeta) {
  const started = Date.now();
  const data = await postMlWithRetry<MlResponseV2>(`${env.ML_SERVICE_URL}/analyze/v2`, payload, 240000, meta);
  console.log(
    `[trace] requestId=${meta.requestId ?? "n/a"} route=${meta.route} uploadFile=${meta.uploadFileName ?? "n/a"} mlElapsedMs=${Date.now() - started}`
  );
  return data;
}
