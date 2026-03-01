from __future__ import annotations

from dataclasses import dataclass
import logging
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
from app.services.gemini_enhancement_service import GeminiEnhancementService
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


class AdvancedAnalyzePipeline:
    def __init__(self) -> None:
        self.base_pipeline = AnalyzePipeline()
        self.skill_extractor = SkillExtractor()
        self.scorer = WeightedScorer()
        self.roadmap_generator = ProgressiveRoadmapGenerator()
        self.rewrite_engine = ResumeRewriteEngine()
        self.ats_checker = AtsChecker()
        self.embedding_service = EmbeddingService()
        self.gemini_enhancer = GeminiEnhancementService()

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

    def run(self, resume_text: str, target_role: str, current_skills: List[str], profession: str, level: str) -> AdvancedAnalysisResult:
        logger.info("Running advanced analysis for target_role=%s, level=%s", target_role, level)
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

        gemini_ranked = self.gemini_enhancer.prioritize_gaps(
            target_role=target_role,
            level=level,
            candidate_gaps=prioritized_gaps,
            strengths=base_result.strengths,
            limit=8,
        )
        if gemini_ranked:
            prioritized_gaps = gemini_ranked

        advanced_roadmap = self.roadmap_generator.generate(
            missing_skills=prioritized_gaps,
            target_role=target_role,
        )

        rewrites = self.rewrite_engine.analyze_and_rewrite(resume_text)
        gemini_rewrites = self.gemini_enhancer.improve_rewrites(
            target_role=target_role,
            bullets=rewrites,
            limit=6,
        )
        rewrite_source = "local"
        if gemini_rewrites:
            rewrites = gemini_rewrites
            rewrite_source = "gemini"

        ats = self.ats_checker.evaluate(resume_text=resume_text, target_role_skills=role_skills)
        gemini_ats = self.gemini_enhancer.enhance_ats_analysis(
            resume_text=resume_text,
            target_role=target_role,
            role_skills=role_skills,
            base_ats=ats,
        )
        ats_source = "local"
        if gemini_ats:
            ats = gemini_ats
            ats_source = "gemini"

        # Merge both detected (strength) and missing (gaps) skill cards.
        merged_insights = [item.__dict__ for item in detected_insights] + self._gap_insights(prioritized_gaps)

        parsed_resume = dict(base_result.parsed_resume)
        parsed_resume["advanced"] = {
            "skillInsightsCount": len(merged_insights),
            "rewriteSuggestionsCount": len(rewrites),
            "atsStatus": ats.get("status"),
            "rewriteSource": rewrite_source,
            "atsSource": ats_source,
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
        )
