from fastapi import FastAPI
import logging
from functools import lru_cache
import os
from pathlib import Path
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, AnalyzeResponseV2
from app.pipelines.analyze_pipeline import AnalyzePipeline
from app.pipelines.advanced_analyze_pipeline import AdvancedAnalyzePipeline

# Load .env file before initializing pipelines
env_file = Path(__file__).resolve().parents[1] / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        env_key = key.strip()
        env_value = value.strip().strip('"').strip("'")
        if env_key and env_key not in os.environ:
            os.environ[env_key] = env_value

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="Resume Analyzer ML Service", version="1.0.0")


@app.on_event("startup")
def startup_event():
    # If configured to use local HF LLM, attempt to warm-load model to surface issues early
    try:
        if os.getenv("USE_HF_LLM", "false").strip().lower() in {"1", "true", "yes"}:
            from app.services.llm_service import get_model_wrapper

            wrapper = get_model_wrapper()
            if wrapper is None:
                logging.getLogger(__name__).warning("USE_HF_LLM enabled but model failed to load at startup")
            else:
                logging.getLogger(__name__).info("HF LLM model loaded at startup")
    except Exception:
        logging.getLogger(__name__).exception("Error while warming HF LLM at startup")


@lru_cache(maxsize=1)
def get_advanced_pipeline() -> AdvancedAnalyzePipeline:
    return AdvancedAnalyzePipeline()


def get_pipeline() -> AnalyzePipeline:
    return get_advanced_pipeline().base_pipeline


@app.get("/health")
def health_check() -> dict:
    pipeline = get_pipeline()
    use_classifier = os.getenv("USE_RESUME_CLASSIFIER", "false").strip().lower() in {"1", "true", "yes", "on"}
    model_loaded = pipeline.classifier_bundle is not None if use_classifier else False
    
    return {
        "status": "ok", 
        "service": "ml-model",
        "custom_model_enabled": use_classifier,
        "custom_model_loaded": model_loaded,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    pipeline = get_pipeline()
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
        predictedCategory=result.predicted_category,
        predictedConfidence=result.predicted_confidence,
    )


@app.post("/analyze/v2", response_model=AnalyzeResponseV2)
def analyze_v2(payload: AnalyzeRequest) -> AnalyzeResponseV2:
    advanced_pipeline = get_advanced_pipeline()
    result = advanced_pipeline.run(
        resume_text=payload.resumeText,
        target_role=payload.targetRole,
        current_skills=payload.currentSkills,
        profession=payload.profession,
        level=payload.experienceLevel,
        rewrite_instructions=payload.rewriteInstructions,
    )

    return AnalyzeResponseV2(
        parsedResume=result.parsed_resume,
        matchScore=result.match_score,
        strengths=result.strengths,
        skillGaps=result.skill_gaps,
        transferableSkills=result.transferable_skills,
        roadmap=result.roadmap,
        certifications=result.certifications,
        predictedCategory=result.predicted_category,
        predictedConfidence=result.predicted_confidence,
        overall_score=result.overall_score,
        confidence=result.confidence,
        breakdown=result.breakdown,
        explanations=result.explanations,
        skill_insights=result.skill_insights,
        roadmap_advanced=result.roadmap_advanced,
        rewrite_suggestions=result.rewrites,
        ats_analysis=result.ats,
    )
