from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.services.embedding_service import EmbeddingService
from app.services.nlp_service import NlpService
from app.utils.skill_dictionary import ROLE_SKILL_MAP, GENERIC_TRANSFERABLE_SKILLS, ROLE_CERTIFICATIONS

try:
    import joblib
except Exception:
    joblib = None


ROLE_CATEGORY_MAP = {
    "software engineer": "INFORMATION-TECHNOLOGY",
    "data analyst": "INFORMATION-TECHNOLOGY",
    "product manager": "BUSINESS-DEVELOPMENT",
    "devops engineer": "INFORMATION-TECHNOLOGY",
}


@dataclass
class AnalysisResult:
    parsed_resume: Dict[str, object]
    match_score: float
    strengths: List[str]
    skill_gaps: List[str]
    transferable_skills: List[str]
    roadmap: List[Dict[str, str]]
    certifications: List[str]


class AnalyzePipeline:
    def __init__(self) -> None:
        self.nlp_service = NlpService()
        self.embedding_service = EmbeddingService()
        self.classifier_bundle = self._load_classifier_bundle()

    def _load_classifier_bundle(self):
        if joblib is None:
            return None

        model_path = Path(__file__).resolve().parents[2] / "saved_models" / "resume_classifier.joblib"
        if not model_path.exists():
            return None

        try:
            bundle = joblib.load(model_path)
            if isinstance(bundle, dict) and bundle.get("pipeline") is not None:
                return bundle
            return None
        except Exception:
            return None

    def _predict_category(self, resume_text: str) -> tuple[str | None, float | None]:
        if not self.classifier_bundle:
            return None, None

        pipeline = self.classifier_bundle.get("pipeline")
        if pipeline is None:
            return None, None

        try:
            predicted = pipeline.predict([resume_text])[0]
            confidence = None
            if hasattr(pipeline, "predict_proba"):
                probs = pipeline.predict_proba([resume_text])[0]
                confidence = float(np.max(probs))
            return str(predicted), confidence
        except Exception:
            return None, None

    def _resolve_target_category(self, role_key: str) -> str | None:
        if role_key in ROLE_CATEGORY_MAP:
            return ROLE_CATEGORY_MAP[role_key]

        if any(keyword in role_key for keyword in ["engineer", "developer", "data", "analyst", "it", "qa", "devops"]):
            return "INFORMATION-TECHNOLOGY"

        if any(keyword in role_key for keyword in ["product", "business", "sales", "marketing", "consult"]):
            return "BUSINESS-DEVELOPMENT"

        if "finance" in role_key or "account" in role_key:
            return "FINANCE"

        if "teacher" in role_key or "education" in role_key:
            return "TEACHER"

        return None

    def _target_category_probability(self, resume_text: str, target_category: str | None) -> float | None:
        if not self.classifier_bundle or not target_category:
            return None

        pipeline = self.classifier_bundle.get("pipeline")
        if pipeline is None or not hasattr(pipeline, "predict_proba"):
            return None

        try:
            classes = getattr(pipeline, "classes_", None)
            if classes is None:
                return None

            classes_list = [str(label) for label in classes]
            if target_category not in classes_list:
                return None

            probs = pipeline.predict_proba([resume_text])[0]
            class_index = classes_list.index(target_category)
            return float(probs[class_index])
        except Exception:
            return None

    def _extract_resume_certifications(self, resume_text: str, role_key: str) -> List[str]:
        normalized = " ".join(resume_text.lower().split())
        role_certs = ROLE_CERTIFICATIONS.get(role_key, [])
        global_certs = sorted({cert for certs in ROLE_CERTIFICATIONS.values() for cert in certs})

        catalog = role_certs + [cert for cert in global_certs if cert not in role_certs]

        alias_map: Dict[str, List[str]] = {
            "AWS Developer Associate": ["aws developer associate", "developer associate"],
            "Azure Developer Associate": ["azure developer associate"],
            "CKA": ["cka", "certified kubernetes administrator"],
            "AWS SysOps Administrator": ["aws sysops administrator", "sysops administrator"],
            "Terraform Associate": ["terraform associate", "hashicorp terraform"],
            "Google Data Analytics": ["google data analytics", "google data analyst"],
            "Microsoft Power BI Data Analyst": ["power bi data analyst", "microsoft power bi"],
            "PSPO": ["pspo", "professional scrum product owner"],
            "Pragmatic Product Management": ["pragmatic product management"],
        }

        detected: List[str] = []
        for cert in catalog:
            aliases = alias_map.get(cert, [cert.lower()])
            found = False
            for alias in aliases:
                alias_normalized = alias.strip().lower()
                if len(alias_normalized) <= 5 and alias_normalized.isalpha():
                    if re.search(rf"\b{re.escape(alias_normalized)}\b", normalized):
                        found = True
                        break
                elif alias_normalized in normalized:
                    found = True
                    break

            if found and cert not in detected:
                detected.append(cert)

        return detected

    def _build_roadmap(self, missing_skills: List[str], target_role: str, level: str) -> List[Dict[str, str]]:
        level_key = level.lower().strip()
        if "entry" in level_key or "junior" in level_key:
            prefix = "Build foundations"
        elif "senior" in level_key or "lead" in level_key:
            prefix = "Demonstrate advanced ownership"
        else:
            prefix = "Build production readiness"

        steps: List[Dict[str, str]] = []
        for index, skill in enumerate(missing_skills[:5]):
            steps.append(
                {
                    "title": f"{prefix} in {skill.title()}",
                    "description": f"Create 1 measurable project milestone focused on {skill} for {target_role}. Priority {index + 1}."
                }
            )
        return steps

    def run(self, resume_text: str, target_role: str, current_skills: List[str], profession: str, level: str) -> AnalysisResult:
        normalized_resume_text = " ".join(resume_text.split())

        # Resolve role-specific benchmark skills from our curated dictionary.
        role_key = target_role.lower().strip()
        role_skills = ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])
        target_category = self._resolve_target_category(role_key)

        extracted_skills = self.nlp_service.extract_skills(resume_text, role_key)
        resume_skills = sorted(set([s.lower() for s in extracted_skills]))
        profile_skills = sorted(set([s.lower() for s in current_skills]))
        known_skills = sorted(set(resume_skills + profile_skills))

        role_skill_set = set(role_skills)
        resume_role_strengths = [skill for skill in resume_skills if skill in role_skill_set]
        profile_role_strengths = [skill for skill in profile_skills if skill in role_skill_set and skill not in resume_role_strengths]

        strengths = (resume_role_strengths + profile_role_strengths)[:8]
        missing_skills = [skill for skill in role_skills if skill not in resume_role_strengths]

        # Semantic similarity compares full resume context against target role skill profile.
        embeddings = self.embedding_service.encode([resume_text, " ".join(role_skills)])
        similarity = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])

        # Final score emphasizes resume evidence, then semantic fit.
        resume_role_coverage = len(resume_role_strengths) / max(len(role_skills), 1)
        heuristic_score = max(0.0, min(100.0, (0.55 * similarity + 0.45 * resume_role_coverage) * 100))

        predicted_category, predicted_confidence = self._predict_category(resume_text)
        target_probability = self._target_category_probability(resume_text, target_category)

        if target_probability is not None:
            ml_component = 100.0 * target_probability
            match_score = (0.82 * heuristic_score) + (0.18 * ml_component)
        else:
            match_score = heuristic_score

        transferable = [skill for skill in GENERIC_TRANSFERABLE_SKILLS if skill in resume_text.lower()]
        if not transferable:
            transferable = GENERIC_TRANSFERABLE_SKILLS[:3]

        roadmap = self._build_roadmap(missing_skills, target_role, level)

        certs = self._extract_resume_certifications(resume_text, role_key)

        # Parsed structure is persisted in PostgreSQL JSONB for dashboard rendering.
        parsed_resume = {
            "profession": profession,
            "experienceLevel": level,
            "skillsExtracted": extracted_skills,
            "skillsFromResumeCount": len(resume_role_strengths),
            "skillsFromProfileCount": len(profile_role_strengths),
            "wordCount": len(resume_text.split()),
            "resumePreview": normalized_resume_text[:450],
            "predictedCategory": predicted_category,
            "predictionConfidence": round(predicted_confidence, 4) if predicted_confidence is not None else None,
            "targetCategory": target_category,
            "targetCategoryProbability": round(target_probability, 4) if target_probability is not None else None,
            "certificationsDetected": certs,
            "modelUsed": "resume_classifier.joblib" if self.classifier_bundle else "heuristic"
        }

        return AnalysisResult(
            parsed_resume=parsed_resume,
            match_score=round(match_score, 2),
            strengths=strengths,
            skill_gaps=missing_skills,
            transferable_skills=transferable,
            roadmap=roadmap,
            certifications=certs,
        )
