from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import re
from typing import Dict, List
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.modules import (
    AtsChecker,
    ProgressiveRoadmapGenerator,
    ResumeRewriteEngine,
    SkillExtractor,
    WeightedScorer,
)
from app.pipelines.analyze_pipeline import AnalyzePipeline
from app.services.embedding_service import EmbeddingService
from app.services.ollama_service import (
    USE_OLLAMA,
    OLLAMA_MODEL,
    analyze_resume_overview as ollama_analyze_resume_overview,
    generate_skill_insights as ollama_generate_skill_insights,
    generate_advanced_roadmap as ollama_generate_advanced_roadmap,
    generate_ollama_rewrites,
    is_ollama_available,
)
from app.services.gemini_service import (
    USE_GEMINI,
    USE_GEMINI_ROADMAP,
    GEMINI_MODEL,
    analyze_resume_overview as gemini_analyze_resume_overview,
    generate_skill_insights as gemini_generate_skill_insights,
    generate_advanced_roadmap as gemini_generate_advanced_roadmap,
    generate_gemini_rewrites,
)
from app.utils.skill_dictionary import ROLE_SKILL_MAP


logger = logging.getLogger(__name__)


@dataclass
class AdvancedAnalysisResult:
    parsed_resume: Dict[str, object]
    match_score: float
    strengths: List[str]
    skill_gaps: List[str]
    transferable_skills: List[str]
    roadmap: List[Dict[str, str]]
    certifications: List[str]
    overall_score: float
    confidence: float
    breakdown: Dict[str, float]
    explanations: Dict[str, str]
    skill_insights: List[dict]
    roadmap_advanced: dict
    rewrites: List[dict]
    ats: dict
    predicted_category: str | None = None
    predicted_confidence: float | None = None


class AdvancedAnalyzePipeline:
    def __init__(self) -> None:
        self.base_pipeline = AnalyzePipeline()
        self.skill_extractor = SkillExtractor()
        self.scorer = WeightedScorer()
        self.roadmap_generator = ProgressiveRoadmapGenerator()
        self.rewrite_engine = ResumeRewriteEngine()
        self.ats_checker = AtsChecker()
        self.embedding_service = EmbeddingService()

    def _normalize_role(self, target_role: str) -> str:
        normalized = re.sub(r"[^a-z0-9 ]+", " ", target_role.lower())
        normalized = " ".join(normalized.split())
        if normalized in ROLE_SKILL_MAP:
            return normalized
        return "software engineer"

    def _gap_insights(self, missing_skills: List[str]) -> List[dict]:
        insights: List[dict] = []
        for skill in missing_skills[:16]:
            slug = skill.lower().replace(" ", "+")
            insights.append(
                {
                    "skill": skill,
                    "detected_from": f"No strong explicit evidence found for {skill} in the current resume.",
                    "confidence": 0.15,
                    "related_missing_skills": [other for other in missing_skills if other != skill][:3],
                    "improvement_suggestions": f"Add a measurable bullet demonstrating hands-on {skill} delivery.",
                    "resources": [
                        {
                            "title": f"{skill} Practical Course",
                            "type": "course",
                            "link": f"https://www.youtube.com/results?search_query={slug}+project+course",
                        }
                    ],
                }
            )
        return insights

    def _safe_similarity(self, text_a: str, text_b: str) -> float:
        try:
            embeddings = self.embedding_service.encode([text_a, text_b])
            sim = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])
            if np.isnan(sim):
                return 0.0
            return max(0.0, min(1.0, sim))
        except Exception:
            return 0.0

    def _prioritize_gaps(self, role_skills: List[str], missing_skills: List[str], current_skills: List[str], level: str) -> List[str]:
        if not missing_skills:
            return []

        lower_current = {item.lower().strip() for item in current_skills if item.strip()}
        filtered_missing = [skill for skill in missing_skills if skill.lower().strip() not in lower_current]
        if not filtered_missing:
            filtered_missing = missing_skills[:]

        # Keep only genuinely needed skills (avoid overwhelming users with every possible gap).
        level_factor = 1.15 if any(token in level.lower() for token in ["senior", "lead"]) else 1.0
        scored: List[tuple[float, str]] = []
        for idx, skill in enumerate(filtered_missing):
            role_index_weight = max(0.2, 1.0 - (idx * 0.05))
            relatedness = max(self._safe_similarity(skill, role_skill) for role_skill in role_skills) if role_skills else 0.0
            score = (role_index_weight * 0.65 + relatedness * 0.35) * level_factor
            scored.append((score, skill))

        scored.sort(key=lambda item: item[0], reverse=True)
        prioritized = [skill for _, skill in scored[:8]]
        return list(dict.fromkeys(prioritized))

    def run(
        self,
        resume_text: str,
        target_role: str,
        current_skills: List[str],
        profession: str,
        level: str,
        rewrite_instructions: str | None = None,
    ) -> AdvancedAnalysisResult:
        logger.info(
            "Running advanced analysis — target_role=%s level=%s ollama_enabled=%s",
            target_role, level, USE_OLLAMA,
        )

        # ------------------------------------------------------------------
        # 1. Base deterministic pipeline (skill extraction, scoring, etc.)
        # ------------------------------------------------------------------
        base_result = self.base_pipeline.run(
            resume_text=resume_text,
            target_role=target_role,
            current_skills=current_skills,
            profession=profession,
            level=level,
        )

        role_key = self._normalize_role(target_role)
        role_skills = ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])

        technical_skills, soft_skills, detected_insights = self.skill_extractor.extract(
            resume_text=resume_text,
            target_role=target_role,
            role_key=role_key,
        )

        score = self.scorer.score(
            resume_text=resume_text,
            role_skills=role_skills,
            extracted_skills=technical_skills,
            soft_skills=soft_skills,
        )

        prioritized_gaps = self._prioritize_gaps(
            role_skills=role_skills,
            missing_skills=base_result.skill_gaps,
            current_skills=current_skills,
            level=level,
        )

        # ------------------------------------------------------------------
        # 2. LLM enhancement — priority: Ollama (local) → Gemini → local
        # ------------------------------------------------------------------
        ollama_live = USE_OLLAMA and is_ollama_available()
        if USE_OLLAMA and not ollama_live:
            logger.warning("[ollama] USE_OLLAMA_ENHANCEMENTS=true but Ollama is not reachable")
        if not ollama_live and USE_GEMINI:
            logger.info("[gemini] Ollama unavailable — using Gemini for LLM tasks")
        if not ollama_live and not USE_GEMINI:
            logger.info("[llm] no LLM available — using local fallbacks only")

        # --- 2a. Resume overview ---
        overview_source = "local"
        overview_model: str | None = None
        llm_overview: Dict = {}

        if ollama_live:
            try:
                llm_overview = ollama_analyze_resume_overview(
                    resume_text=resume_text,
                    target_role=target_role,
                    profession=profession,
                    level=level,
                    current_skills=current_skills,
                )
                if llm_overview:
                    overview_source = "ollama"
                    overview_model = OLLAMA_MODEL
                    logger.info("[ollama] overview OK")
            except Exception:
                logger.exception("[ollama] overview failed")
        elif USE_GEMINI:
            try:
                llm_overview = gemini_analyze_resume_overview(
                    resume_text=resume_text,
                    target_role=target_role,
                    profession=profession,
                    level=level,
                    current_skills=current_skills,
                )
                if llm_overview:
                    overview_source = "gemini"
                    overview_model = GEMINI_MODEL
                    logger.info("[gemini] overview OK")
            except Exception:
                logger.exception("[gemini] overview failed")

        # --- 2b. Skill insights ---
        skill_insights_source = "local"
        merged_insights: List[dict]
        llm_insights: List[dict] = []

        if ollama_live:
            try:
                llm_insights = ollama_generate_skill_insights(
                    resume_text=resume_text,
                    target_role=target_role,
                    strengths=base_result.strengths,
                    skill_gaps=prioritized_gaps,
                    level=level,
                )
                if llm_insights:
                    skill_insights_source = "ollama"
                    logger.info("[ollama] skill insights OK count=%d", len(llm_insights))
            except Exception:
                logger.exception("[ollama] skill insights failed")
        elif USE_GEMINI:
            try:
                llm_insights = gemini_generate_skill_insights(
                    resume_text=resume_text,
                    target_role=target_role,
                    strengths=base_result.strengths,
                    skill_gaps=prioritized_gaps,
                    level=level,
                )
                if llm_insights:
                    skill_insights_source = "gemini"
                    logger.info("[gemini] skill insights OK count=%d", len(llm_insights))
            except Exception:
                logger.exception("[gemini] skill insights failed")

        merged_insights = llm_insights if llm_insights else (
            [item.__dict__ for item in detected_insights] + self._gap_insights(prioritized_gaps)
        )

        # --- 2c. Advanced roadmap ---
        roadmap_source = "local"
        roadmap_model: str | None = None
        advanced_roadmap: Dict = {}

        if ollama_live:
            try:
                ollama_roadmap = ollama_generate_advanced_roadmap(
                    missing_skills=prioritized_gaps,
                    target_role=target_role,
                    level=level,
                    resume_text=resume_text,
                )
                if any(ollama_roadmap.get(k) for k in ("30_day_plan", "60_day_plan", "90_day_plan")):
                    advanced_roadmap = ollama_roadmap
                    roadmap_source = "ollama"
                    roadmap_model = OLLAMA_MODEL
                    logger.info("[ollama] roadmap OK")
            except Exception:
                logger.exception("[ollama] roadmap failed")
        elif USE_GEMINI_ROADMAP:
            try:
                gemini_roadmap = gemini_generate_advanced_roadmap(
                    missing_skills=prioritized_gaps,
                    target_role=target_role,
                    level=level,
                    resume_text=resume_text,
                )
                if any(gemini_roadmap.get(k) for k in ("30_day_plan", "60_day_plan", "90_day_plan")):
                    advanced_roadmap = gemini_roadmap
                    roadmap_source = "gemini"
                    roadmap_model = GEMINI_MODEL
                    logger.info("[gemini] roadmap OK")
            except Exception:
                logger.exception("[gemini] roadmap failed")

        if not advanced_roadmap:
            advanced_roadmap = self.roadmap_generator.generate(
                missing_skills=prioritized_gaps, target_role=target_role
            )

        # --- 2d. Resume rewrites ---
        rewrite_source = "local"
        rewrites: List[dict] = []

        if ollama_live:
            try:
                ollama_rewrites = generate_ollama_rewrites(
                    resume_text=resume_text,
                    target_role=target_role,
                    profession=profession,
                    level=level,
                    current_skills=current_skills,
                    rewrite_instructions=rewrite_instructions,
                )
                if ollama_rewrites:
                    rewrites = ollama_rewrites
                    rewrite_source = "ollama"
                    logger.info("[ollama] rewrites OK count=%d", len(rewrites))
            except Exception:
                logger.exception("[ollama] rewrites failed")
        elif USE_GEMINI:
            try:
                gemini_rewrites = generate_gemini_rewrites(
                    resume_text=resume_text,
                    target_role=target_role,
                    profession=profession,
                    level=level,
                    current_skills=current_skills,
                    rewrite_instructions=rewrite_instructions,
                )
                if gemini_rewrites:
                    rewrites = gemini_rewrites
                    rewrite_source = "gemini"
                    logger.info("[gemini] rewrites OK count=%d", len(rewrites))
            except Exception:
                logger.exception("[gemini] rewrites failed")

        if not rewrites:
            rewrites = self.rewrite_engine.analyze_and_rewrite(
                resume_text=resume_text,
                target_role=target_role,
                profession=profession,
                experience_level=level,
                current_skills=current_skills,
                rewrite_instructions=rewrite_instructions,
            )

        # ------------------------------------------------------------------
        # 3. ATS check (always local — fast and deterministic)
        # ------------------------------------------------------------------
        ats = self.ats_checker.evaluate(resume_text=resume_text, target_role_skills=role_skills)

        # ------------------------------------------------------------------
        # 4. Build enriched parsedResume (merge base + LLM overview)
        # ------------------------------------------------------------------
        parsed_resume = dict(base_result.parsed_resume)

        # Merge LLM overview fields (they override local where present)
        if llm_overview:
            for field in (
                "skillsExtracted", "softSkillsHighlights", "certificationsDetected",
                "awardsDetected", "featuredExperiences", "featuredProjects",
                "predictedCategory", "resumePreview", "wordCount",
            ):
                val = llm_overview.get(field)
                if val is not None and val != [] and val != "":
                    parsed_resume[field] = val

            edu = llm_overview.get("educationHighlights")
            if edu:
                parsed_resume["educationHighlights"] = edu

        # Always stamp the source/model fields so the UI "Roadmap Engine" badge works
        parsed_resume["overviewSource"] = overview_source
        parsed_resume["overviewModel"] = overview_model
        parsed_resume["roadmapSource"] = roadmap_source
        parsed_resume["roadmapModel"] = roadmap_model

        parsed_resume["advanced"] = {
            "skillInsightsCount": len(merged_insights),
            "rewriteSuggestionsCount": len(rewrites),
            "atsStatus": ats.get("status"),
            "skillGapSource": skill_insights_source,
            "rewriteSource": rewrite_source,
            "atsSource": "local",
        }

        return AdvancedAnalysisResult(
            parsed_resume=parsed_resume,
            match_score=base_result.match_score,
            strengths=base_result.strengths,
            skill_gaps=prioritized_gaps,
            transferable_skills=base_result.transferable_skills,
            roadmap=base_result.roadmap,
            certifications=base_result.certifications,
            overall_score=score.overall_score,
            confidence=score.confidence,
            breakdown=score.breakdown,
            explanations=score.explanations,
            skill_insights=merged_insights,
            roadmap_advanced=advanced_roadmap,
            rewrites=rewrites,
            ats=ats,
            predicted_category=base_result.predicted_category,
            predicted_confidence=base_result.predicted_confidence,
        )
