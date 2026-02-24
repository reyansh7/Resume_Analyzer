from pydantic import BaseModel, Field
from typing import List, Dict


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
