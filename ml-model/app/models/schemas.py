from pydantic import BaseModel, Field
from typing import List, Dict, Literal


class AnalyzeRequest(BaseModel):
    resumeText: str = Field(min_length=1)
    targetRole: str = Field(min_length=1)
    currentSkills: List[str] = Field(default_factory=list)
    profession: str = Field(min_length=1)
    experienceLevel: str = Field(min_length=1)


class RoadmapStep(BaseModel):
    title: str
    description: str


class AnalyzeResponse(BaseModel):
    parsedResume: Dict[str, object]
    matchScore: float
    strengths: List[str]
    skillGaps: List[str]
    transferableSkills: List[str]
    roadmap: List[RoadmapStep]
    certifications: List[str]
    predictedCategory: str | None = None
    predictedConfidence: float | None = None


class SkillBreakdown(BaseModel):
    technical_skills: float
    soft_skills: float
    experience_match: float
    education_match: float


class SkillExplanations(BaseModel):
    technical_skills: str
    soft_skills: str
    experience_match: str
    education_match: str


class SkillInsightResource(BaseModel):
    title: str
    type: str
    link: str


class SkillInsightItem(BaseModel):
    skill: str
    detected_from: str
    confidence: float
    related_missing_skills: List[str]
    improvement_suggestions: str
    resources: List[SkillInsightResource]


class RoadmapTask(BaseModel):
    skill: str
    title: str
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]
    estimated_hours: int
    priority_score: float
    suggested_courses: List[str]
    youtube_links: List[str]
    leetcode_problems: List[str]
    details: str


class ProgressiveRoadmap(BaseModel):
    thirty_day_plan: List[RoadmapTask] = Field(alias="30_day_plan")
    sixty_day_plan: List[RoadmapTask] = Field(alias="60_day_plan")
    ninety_day_plan: List[RoadmapTask] = Field(alias="90_day_plan")


class RewriteSuggestion(BaseModel):
    section: str
    before: str
    after: str
    improvement_type: str


class AtsAnalysis(BaseModel):
    ats_score: float
    status: Literal["ATS Safe", "Needs Optimization", "High Rejection Risk"]
    issues: List[str]


class AnalyzeResponseV2(AnalyzeResponse):
    overall_score: float
    confidence: float
    breakdown: SkillBreakdown
    explanations: SkillExplanations
    skill_insights: List[SkillInsightItem]
    roadmap_advanced: ProgressiveRoadmap
    rewrite_suggestions: List[RewriteSuggestion]
    ats_analysis: AtsAnalysis
