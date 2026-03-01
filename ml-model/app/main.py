from fastapi import FastAPI
import logging
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, AnalyzeResponseV2
from app.pipelines.analyze_pipeline import AnalyzePipeline
from app.pipelines.advanced_analyze_pipeline import AdvancedAnalyzePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="Resume Analyzer ML Service", version="1.0.0")
pipeline = AnalyzePipeline()
advanced_pipeline = AdvancedAnalyzePipeline()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ml-model"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    result = pipeline.run(
        resume_text=payload.resumeText,
        target_role=payload.targetRole,
        current_skills=payload.currentSkills,
        profession=payload.profession,
        level=payload.experienceLevel,
    )

    return AnalyzeResponse(
        parsedResume=result.parsed_resume,
        matchScore=result.match_score,
        strengths=result.strengths,
        skillGaps=result.skill_gaps,
        transferableSkills=result.transferable_skills,
        roadmap=result.roadmap,
        certifications=result.certifications,
    )


@app.post("/analyze/v2", response_model=AnalyzeResponseV2)
def analyze_v2(payload: AnalyzeRequest) -> AnalyzeResponseV2:
    result = advanced_pipeline.run(
        resume_text=payload.resumeText,
        target_role=payload.targetRole,
        current_skills=payload.currentSkills,
        profession=payload.profession,
        level=payload.experienceLevel,
    )

    return AnalyzeResponseV2(
        parsedResume=result.parsed_resume,
        matchScore=result.match_score,
        strengths=result.strengths,
        skillGaps=result.skill_gaps,
        transferableSkills=result.transferable_skills,
        roadmap=result.roadmap,
        certifications=result.certifications,
        overall_score=result.overall_score,
        confidence=result.confidence,
        breakdown=result.breakdown,
        explanations=result.explanations,
        skill_insights=result.skill_insights,
        roadmap_advanced=result.roadmap_advanced,
        rewrite_suggestions=result.rewrites,
        ats_analysis=result.ats,
    )
