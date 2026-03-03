from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.config.scoring_config import DEFAULT_WEIGHTS
from app.services.embedding_service import EmbeddingService


EDUCATION_KEYWORDS = [
    "education",
    "b.tech",
    "b.e",
    "bachelor",
    "master",
    "m.tech",
    "phd",
    "university",
    "college",
    "school",
    "degree",
    "cgpa",
    "gpa",
    "hsc",
    "ssc",
]
EXPERIENCE_KEYWORDS = ["years", "experience", "engineer", "intern", "worked", "delivered", "built"]


@dataclass
class ScoreBreakdown:
    overall_score: float
    confidence: float
    breakdown: Dict[str, float]
    explanations: Dict[str, str]


class WeightedScorer:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    def _safe_similarity(self, a: str, b: str) -> float:
        try:
            embeddings = self.embedding_service.encode([a, b])
            sim = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])
            if np.isnan(sim):
                return 0.0
            return max(0.0, min(1.0, sim))
        except Exception:
            return 0.0

    def _technical_score(self, resume_text: str, role_skills: List[str], extracted_skills: List[str]) -> tuple[float, list[float]]:
        if not role_skills:
            return 0.0, []

        extracted = extracted_skills or []
        extracted_set = {skill.lower() for skill in extracted}
        coverage = sum(1 for skill in role_skills if skill.lower() in extracted_set) / max(len(role_skills), 1)

        # Embedding similarity distribution across role skills for confidence signal.
        sims: list[float] = []
        for role_skill in role_skills:
            if not extracted:
                sims.append(0.0)
                continue
            candidates = [self._safe_similarity(role_skill, extracted_skill) for extracted_skill in extracted]
            sims.append(max(candidates) if candidates else 0.0)

        semantic_fit = float(np.mean(sims)) if sims else 0.0
        score = (0.55 * coverage + 0.45 * semantic_fit) * 100
        return max(0.0, min(100.0, score)), sims

    def _experience_score(self, resume_text: str) -> float:
        lowered = resume_text.lower()
        hits = sum(1 for token in EXPERIENCE_KEYWORDS if token in lowered)
        quant_hits = len(list(filter(None, [part for part in lowered.split() if any(ch.isdigit() for ch in part)])))
        raw = min(1.0, (hits / len(EXPERIENCE_KEYWORDS)) + min(quant_hits, 8) * 0.04)
        return round(max(0.0, min(100.0, raw * 100)), 2)

    def _soft_skill_score(self, soft_skills: List[str]) -> float:
        return round(max(0.0, min(100.0, (len(soft_skills) / 6) * 100)), 2)

    def _normalize_gpa_to_percent(self, value: float, scale: float | None) -> float:
        if value <= 0:
            return 0.0

        if scale is not None and scale > 0:
            return max(0.0, min(100.0, (value / scale) * 100.0))

        if value <= 4.5:
            return max(0.0, min(100.0, (value / 4.0) * 100.0))
        if value <= 10.5:
            return max(0.0, min(100.0, (value / 10.0) * 100.0))
        return max(0.0, min(100.0, value))

    def _extract_gpa_percent(self, lowered: str) -> float | None:
        explicit_patterns = [
            r"(?:cgpa|gpa)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:/|out\s*of\s*)?\s*(10|4|100)?",
            r"(\d+(?:\.\d+)?)\s*(?:/|out\s*of\s*)\s*(10|4|100)\s*(?:cgpa|gpa)?",
            r"(\d+(?:\.\d+)?)\s*(?:cgpa|gpa)\b",
        ]

        for pattern in explicit_patterns:
            match = re.search(pattern, lowered)
            if not match:
                continue

            try:
                raw_value = float(match.group(1))
            except Exception:
                continue

            raw_scale = None
            if match.lastindex and match.lastindex >= 2:
                scale_text = match.group(2)
                if scale_text:
                    try:
                        raw_scale = float(scale_text)
                    except Exception:
                        raw_scale = None

            return self._normalize_gpa_to_percent(raw_value, raw_scale)

        return None

    def _education_score(self, resume_text: str) -> float:
        lowered = resume_text.lower()

        keyword_hits = sum(1 for token in EDUCATION_KEYWORDS if token in lowered)
        keyword_score = min(100.0, (keyword_hits / max(len(EDUCATION_KEYWORDS), 1)) * 100.0)

        has_year_range = bool(re.search(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)?\d{2}\b", lowered))
        has_degree_token = bool(re.search(r"\b(bachelor|master|b\.?tech|m\.?tech|degree|diploma|hsc|ssc)\b", lowered))
        has_institute_token = bool(re.search(r"\b(university|college|school|institute)\b", lowered))

        structure_bonus = 0.0
        if has_degree_token:
            structure_bonus += 15.0
        if has_institute_token:
            structure_bonus += 12.0
        if has_year_range:
            structure_bonus += 8.0

        gpa_percent = self._extract_gpa_percent(lowered)

        structure_score = max(0.0, min(100.0, keyword_score * 0.7 + structure_bonus))
        if gpa_percent is None:
            return round(structure_score, 2)

        combined = (0.45 * structure_score) + (0.55 * gpa_percent)
        if structure_score < 20:
            combined = max(combined, 0.75 * gpa_percent)

        return round(max(0.0, min(100.0, combined)), 2)

    def score(self, resume_text: str, role_skills: List[str], extracted_skills: List[str], soft_skills: List[str]) -> ScoreBreakdown:
        technical, similarity_distribution = self._technical_score(resume_text, role_skills, extracted_skills)
        experience = self._experience_score(resume_text)
        soft = self._soft_skill_score(soft_skills)
        education = self._education_score(resume_text)

        weighted_overall = (
            technical * DEFAULT_WEIGHTS.technical_skills
            + experience * DEFAULT_WEIGHTS.experience_match
            + soft * DEFAULT_WEIGHTS.soft_skills
            + education * DEFAULT_WEIGHTS.education_match
        )

        sims = np.array(similarity_distribution) if similarity_distribution else np.array([0.0])
        similarity_mean = float(np.mean(sims))
        similarity_std = float(np.std(sims))
        confidence = max(0.5, min(0.99, similarity_mean - (0.5 * similarity_std) + 0.35))

        explanations = {
            "technical_skills": (
                f"Technical score blends role-skill coverage and embedding similarity. Coverage={round(technical, 1)} on a 0-100 scale."
            ),
            "soft_skills": (
                f"Soft-skills score is inferred from leadership, collaboration, communication and impact language density."
            ),
            "experience_match": (
                "Experience score uses action verbs, measurable achievements and professional context cues."
            ),
            "education_match": (
                "Education score checks degree/academic markers and also factors GPA/CGPA performance when present."
            ),
        }

        return ScoreBreakdown(
            overall_score=round(max(0.0, min(100.0, weighted_overall)), 2),
            confidence=round(confidence, 2),
            breakdown={
                "technical_skills": round(technical, 2),
                "soft_skills": round(soft, 2),
                "experience_match": round(experience, 2),
                "education_match": round(education, 2),
            },
            explanations=explanations,
        )
