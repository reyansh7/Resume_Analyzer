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

SKILL_ALIASES = {
    "nodejs": "node",
    "node.js": "node",
    "node js": "node",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "powerbi": "power bi",
    "ci cd": "ci/cd",
}

SKILL_DISPLAY_NAMES = {
    "aws": "AWS",
    "sql": "SQL",
    "ci/cd": "CI/CD",
    "power bi": "Power BI",
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

    def _canonicalize_skill(self, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9+/\. ]+", " ", value.lower())
        normalized = " ".join(normalized.split())
        normalized = SKILL_ALIASES.get(normalized, normalized)
        return normalized

    def _display_skill(self, canonical: str) -> str:
        if canonical in SKILL_DISPLAY_NAMES:
            return SKILL_DISPLAY_NAMES[canonical]

        return " ".join(part.upper() if len(part) <= 3 else part.title() for part in canonical.split(" "))

    def _detect_section_key(self, line: str) -> str | None:
        normalized = re.sub(r"[^a-z& ]+", " ", line.lower())
        normalized = " ".join(normalized.split())

        if not normalized:
            return None

        if "technical skills" in normalized or normalized == "skills":
            return "skills"

        if normalized in {"projects", "project", "academic projects"} or "projects" in normalized:
            return "projects"

        if "experience" in normalized or "work history" in normalized or "employment" in normalized:
            return "experience"

        if any(key in normalized for key in ["honors", "awards", "certifications", "achievements"]):
            return "awards"

        if normalized in {"education", "summary", "objective", "contact", "profile"}:
            return "other"

        return None

    def _extract_resume_sections(self, resume_text: str) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {
            "skills": [],
            "projects": [],
            "experience": [],
            "awards": [],
        }

        current_section: str | None = None
        for raw_line in resume_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            detected = self._detect_section_key(line)
            if detected == "other":
                current_section = None
                continue

            if detected in sections:
                current_section = detected
                continue

            if current_section in sections:
                sections[current_section].append(line)

        return sections

    def _extract_skills_from_section(self, section_lines: List[str]) -> List[str]:
        detected: List[str] = []
        for line in section_lines:
            cleaned = re.sub(r"^[•\-]\s*", "", line).strip()
            if ":" in cleaned:
                cleaned = cleaned.split(":", 1)[1]

            parts = re.split(r"[,/;|]", cleaned)
            for part in parts:
                candidate = part.strip()
                if len(candidate) < 2:
                    continue
                if candidate.lower() in {"and", "or", "with"}:
                    continue
                detected.append(candidate)

        return list(dict.fromkeys(detected))

    def _extract_awards(self, award_lines: List[str]) -> List[str]:
        awards: List[str] = []
        for line in award_lines:
            cleaned = re.sub(r"^[•\-]\s*", "", line).strip()
            if len(cleaned) < 6:
                continue
            if cleaned.lower() in {"honors & awards", "awards", "honors"}:
                continue
            awards.append(cleaned)

        return list(dict.fromkeys(awards))[:8]

    def _extract_best_project(self, project_lines: List[str]) -> str | None:
        if not project_lines:
            return None

        blocks: List[Dict[str, object]] = []
        current_title: str | None = None
        current_points: List[str] = []

        for line in project_lines:
            cleaned = re.sub(r"^[•\-]\s*", "", line).strip()
            is_bullet = bool(re.match(r"^[•\-]", line))

            is_title_like = (
                not is_bullet
                and len(cleaned) <= 100
                and not re.match(r"^(built|developed|created|implemented|led|tech|using)\b", cleaned.lower())
            )

            if is_title_like:
                if current_title:
                    blocks.append({"title": current_title, "points": current_points.copy()})
                current_title = cleaned
                current_points = []
                continue

            if current_title:
                current_points.append(cleaned)

        if current_title:
            blocks.append({"title": current_title, "points": current_points.copy()})

        if not blocks:
            return re.sub(r"^[•\-]\s*", "", project_lines[0]).strip()

        keyword_weights = {
            "built": 2,
            "developed": 2,
            "implemented": 2,
            "deployed": 2,
            "model": 1,
            "nlp": 1,
            "ai": 1,
            "accuracy": 2,
            "api": 1,
            "app": 1,
        }

        best_score = -1
        best_summary: str | None = None
        for block in blocks:
            title = str(block["title"])
            points = [str(item) for item in block["points"]]
            joined = f"{title} {' '.join(points)}".lower()
            score = sum(weight for key, weight in keyword_weights.items() if key in joined)
            score += len(re.findall(r"\b\d+(?:\.\d+)?%?\b", joined))
            score += min(len(points), 3)

            summary_point = points[0] if points else ""
            summary = f"{title} — {summary_point}".strip(" —")

            if score > best_score:
                best_score = score
                best_summary = summary

        return best_summary

    def _extract_best_experiences(self, experience_lines: List[str]) -> List[str]:
        if not experience_lines:
            return []

        cleaned_lines = [re.sub(r"^[•\-]\s*", "", line).strip() for line in experience_lines]
        cleaned_lines = [line for line in cleaned_lines if len(line) >= 6]

        keyword_weights = {
            "led": 2,
            "managed": 2,
            "coordinated": 2,
            "delivered": 2,
            "built": 1,
            "improved": 2,
            "organized": 1,
            "achieved": 2,
            "supported": 1,
            "assessed": 1,
        }

        scored: List[tuple[int, str]] = []
        for line in cleaned_lines:
            text = line.lower()
            score = sum(weight for key, weight in keyword_weights.items() if key in text)
            score += len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))
            if len(line) > 60:
                score += 1
            scored.append((score, line))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = [line for _, line in scored[:3]]
        return list(dict.fromkeys(top))

    def run(self, resume_text: str, target_role: str, current_skills: List[str], profession: str, level: str) -> AnalysisResult:
        normalized_resume_text = " ".join(resume_text.split())
        sections = self._extract_resume_sections(resume_text)

        # Resolve role-specific benchmark skills from our curated dictionary.
        role_key = target_role.lower().strip()
        role_skills = ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])
        target_category = self._resolve_target_category(role_key)

        extracted_skills = self.nlp_service.extract_skills(resume_text, role_key)
        section_skills = self._extract_skills_from_section(sections["skills"])

        role_skill_by_canonical: Dict[str, str] = {}
        for role_skill in role_skills:
            role_skill_by_canonical[self._canonicalize_skill(role_skill)] = role_skill

        role_skill_set = set(role_skill_by_canonical.keys())

        resume_skill_display_by_canonical: Dict[str, str] = {}
        for raw_skill in section_skills:
            canonical = self._canonicalize_skill(raw_skill)
            if canonical and canonical not in resume_skill_display_by_canonical:
                resume_skill_display_by_canonical[canonical] = raw_skill

        for raw_skill in extracted_skills:
            canonical = self._canonicalize_skill(raw_skill)
            if canonical and canonical not in resume_skill_display_by_canonical:
                resume_skill_display_by_canonical[canonical] = raw_skill

        profile_skill_display_by_canonical: Dict[str, str] = {}
        for raw_skill in current_skills:
            canonical = self._canonicalize_skill(raw_skill)
            if canonical and canonical not in profile_skill_display_by_canonical:
                profile_skill_display_by_canonical[canonical] = raw_skill

        resume_skill_keys = list(resume_skill_display_by_canonical.keys())
        profile_skill_keys = list(profile_skill_display_by_canonical.keys())

        resume_role_strengths = [skill for skill in resume_skill_keys if skill in role_skill_set]
        profile_role_strengths = [
            skill for skill in profile_skill_keys if skill in role_skill_set and skill not in resume_role_strengths
        ]

        additional_resume_strengths = [
            skill for skill in resume_skill_keys if skill not in role_skill_set and skill not in profile_role_strengths
        ]

        transferable = [skill for skill in GENERIC_TRANSFERABLE_SKILLS if skill in resume_text.lower()]
        if not transferable:
            transferable = GENERIC_TRANSFERABLE_SKILLS[:3]

        strengths: List[str] = []
        for canonical in resume_role_strengths + profile_role_strengths:
            strengths.append(role_skill_by_canonical.get(canonical, self._display_skill(canonical)))

        for canonical in additional_resume_strengths[:6]:
            strengths.append(
                resume_skill_display_by_canonical.get(canonical)
                or profile_skill_display_by_canonical.get(canonical)
                or self._display_skill(canonical)
            )

        strengths.extend(skill.title() for skill in transferable)
        strengths = list(dict.fromkeys([item.strip() for item in strengths if item.strip()]))[:14]

        missing_skills = [
            role_skill_by_canonical[skill]
            for skill in role_skill_set
            if skill not in resume_role_strengths and skill not in profile_role_strengths
        ]

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

        roadmap = self._build_roadmap(missing_skills, target_role, level)

        certs = self._extract_resume_certifications(resume_text, role_key)
        awards = self._extract_awards(sections["awards"])
        featured_project = self._extract_best_project(sections["projects"])
        featured_experiences = self._extract_best_experiences(sections["experience"])

        # Parsed structure is persisted in PostgreSQL JSONB for dashboard rendering.
        parsed_resume = {
            "profession": profession,
            "experienceLevel": level,
            "skillsExtracted": list(dict.fromkeys(section_skills + extracted_skills)),
            "skillsFromResumeCount": len(resume_role_strengths),
            "skillsFromProfileCount": len(profile_role_strengths),
            "wordCount": len(resume_text.split()),
            "resumePreview": normalized_resume_text[:450],
            "predictedCategory": predicted_category,
            "predictionConfidence": round(predicted_confidence, 4) if predicted_confidence is not None else None,
            "targetCategory": target_category,
            "targetCategoryProbability": round(target_probability, 4) if target_probability is not None else None,
            "certificationsDetected": certs,
            "awardsDetected": awards,
            "featuredProject": featured_project,
            "featuredExperiences": featured_experiences,
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
