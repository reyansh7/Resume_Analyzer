from fastapi import FastAPI
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.pipelines.analyze_pipeline import AnalyzePipeline

app = FastAPI(title="Resume Analyzer ML Service", version="1.0.0")
pipeline = AnalyzePipeline()


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
