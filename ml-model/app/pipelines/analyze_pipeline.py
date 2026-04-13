from dataclasses import dataclass
from pathlib import Path
import os
import re
import unicodedata
import logging
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

logger = logging.getLogger(__name__)


ROLE_CATEGORY_MAP = {
    "software engineer": "INFORMATION-TECHNOLOGY",
    "data analyst": "INFORMATION-TECHNOLOGY",
    "product manager": "BUSINESS-DEVELOPMENT",
    "devops engineer": "INFORMATION-TECHNOLOGY",
    "financial analyst": "FINANCE",
    "investment analyst": "FINANCE",
    "accountant": "FINANCE",
    "risk analyst": "FINANCE",
    "mechanical engineer": "ENGINEERING",
    "civil engineer": "ENGINEERING",
    "electrical engineer": "ENGINEERING",
    "industrial engineer": "ENGINEERING",
}

ROLE_ALIASES = {
    "software developer": "software engineer",
    "full stack developer": "software engineer",
    "fullstack developer": "software engineer",
    "frontend developer": "software engineer",
    "front end developer": "software engineer",
    "backend developer": "software engineer",
    "back end developer": "software engineer",
    "sde": "software engineer",
    "data scientist": "data analyst",
    "business analyst": "data analyst",
    "site reliability engineer": "devops engineer",
    "sre": "devops engineer",
    "platform engineer": "devops engineer",
    "finance analyst": "financial analyst",
    "fp&a analyst": "financial analyst",
    "fp and a analyst": "financial analyst",
    "equity analyst": "investment analyst",
    "research analyst": "investment analyst",
    "chartered accountant": "accountant",
    "tax accountant": "accountant",
    "credit risk analyst": "risk analyst",
    "market risk analyst": "risk analyst",
    "mech engineer": "mechanical engineer",
    "mechanical design engineer": "mechanical engineer",
    "civil site engineer": "civil engineer",
    "structural engineer": "civil engineer",
    "ee engineer": "electrical engineer",
    "electrical design engineer": "electrical engineer",
    "production engineer": "industrial engineer",
    "manufacturing engineer": "industrial engineer",
}

SKILL_ALIASES = {
    "nodejs": "node",
    "node.js": "node",
    "node js": "node",
    "java script": "javascript",
    "my sql": "sql",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "powerbi": "power bi",
    "ci cd": "ci/cd",
}

SECTION_HEADER_HINTS = [
    "skills",
    "technical skills",
    "projects",
    "project",
    "experience",
    "work experience",
    "employment",
    "internship",
    "certification",
    "certifications",
    "awards",
    "achievements",
    "honors",
    "education",
    "summary",
    "objective",
    "profile",
]

ACTION_STARTERS = {
    "led",
    "built",
    "developed",
    "implemented",
    "managed",
    "created",
    "contributed",
    "solved",
    "won",
    "qualified",
    "reached",
    "organized",
    "deployed",
}

SECTION_SIGNAL_PATTERNS = {
    "projects": [
        r"\bprojects?\b",
        r"\bportfolio\b",
        r"\bcapstone\b",
        r"\bhackathon\b",
        r"\bgithub\b",
        r"\bdeployed\b",
        r"\bbuilt\b",
        r"\bdeveloped\b",
        r"\bimplemented\b",
        r"\bwebsite\b",
        r"\bweb app\b",
        r"\bapplication\b",
        r"\bapi\b",
        r"\bstreamlit\b",
        r"\bfastapi\b",
        r"\bflask\b",
        r"\breact\b",
        r"\bnext\s*js\b",
    ],
    "experience": [
        r"\bexperience\b",
        r"\bwork history\b",
        r"\bemployment\b",
        r"\bintern(ship)?\b",
        r"\bworked\b",
        r"\bled\b",
        r"\bmanaged\b",
        r"\bcoordinated\b",
        r"\bresponsible\b",
        r"\brole\b",
        r"\bcompany\b",
        r"\bteam\b",
        r"\borganization\b",
    ],
    "certifications": [
        r"\bcertification(s)?\b",
        r"\bcertified\b",
        r"\bcertificate\b",
        r"\blicense(d)?\b",
        r"\baws\b",
        r"\bazure\b",
        r"\bgoogle cloud\b",
        r"\boracle\b",
        r"\bscrum\b",
        r"\bkubernetes\b",
        r"\bfoundation\b",
        r"\bassociate\b",
        r"\bprofessional\b",
    ],
    "awards": [
        r"\bawards?\b",
        r"\bachievement(s)?\b",
        r"\bachieved\b",
        r"\bqualified\b",
        r"\bhonou?rs?\b",
        r"\bwinner\b",
        r"\brank(ed)?\b",
        r"\bfinalist\b",
        r"\bscholar(ship)?\b",
        r"\brecognition\b",
        r"\bcodeforces\b",
        r"\bleetcode\b",
        r"\brating\b",
        r"\bcontest\b",
    ],
    "skills": [
        r"\bskills?\b",
        r"\btechnologies\b",
        r"\btools?\b",
        r"\bframeworks?\b",
        r"\blanguages?\b",
    ],
    "other": [
        r"\beducation\b",
        r"\bcgpa\b",
        r"\bgpa\b",
        r"\bpercentage\b",
        r"\buniversity\b",
        r"\bcollege\b",
        r"\bschool\b",
        r"\bclass\s*x\b",
        r"\bclass\s*xii\b",
        r"\bcontact\b",
        r"\bemail\b",
        r"\bphone\b",
        r"\blinkedin\b",
    ],
}

CERTIFICATION_ENTRY_PATTERNS = [
    r"\bcertification(s)?\b",
    r"\bcertified\b",
    r"\bcertificate\b",
    r"\blicense(d)?\b",
    r"\baws\b",
    r"\bazure\b",
    r"\bgoogle cloud\b",
    r"\boracle\b",
    r"\bscrum\b",
    r"\bkubernetes\b",
    r"\bterraform\b",
    r"\bfoundation\b",
    r"\bassociate\b",
    r"\bprofessional\b",
    r"\bnptel\b",
    r"\bcoursera\b",
    r"\budemy\b",
]

AWARD_ENTRY_PATTERNS = [
    r"\baward(s)?\b",
    r"\bachievement(s)?\b",
    r"\bachieved\b",
    r"\bqualified\b",
    r"\bhonou?rs?\b",
    r"\bwinner\b",
    r"\brunner\s*-?\s*up\b",
    r"\bfinalist\b",
    r"\brank(ed)?\b",
    r"\bscholar(ship)?\b",
    r"\bmedal\b",
    r"\bdean'?s list\b",
    r"\brecognition\b",
    r"\bcodeforces\b",
    r"\bleetcode\b",
    r"\brating\b",
    r"\bcontest\b",
]

SKILL_DISPLAY_NAMES = {
    "aws": "AWS",
    "sql": "SQL",
    "ci/cd": "CI/CD",
    "power bi": "Power BI",
}

KNOWN_SKILL_CANONICAL = {
    re.sub(r"\s+", " ", skill.lower().strip())
    for skills in ROLE_SKILL_MAP.values()
    for skill in skills
}
KNOWN_SKILL_CANONICAL.update({
    re.sub(r"\s+", " ", skill.lower().strip()) for skill in GENERIC_TRANSFERABLE_SKILLS
})

SKILL_HINT_TOKENS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "sql",
    "database",
    "data",
    "analytics",
    "analysis",
    "visualization",
    "excel",
    "tableau",
    "power",
    "docker",
    "kubernetes",
    "terraform",
    "linux",
    "cloud",
    "aws",
    "azure",
    "gcp",
    "devops",
    "monitoring",
    "system",
    "design",
    "agile",
    "stakeholder",
    "communication",
    "collaboration",
    "leadership",
    "management",
    "problem",
    "solving",
    "ownership",
    "programming",
    "technology",
    "technologies",
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
    predicted_category: str | None = None
    predicted_confidence: float | None = None


class AnalyzePipeline:
    def __init__(self) -> None:
        self.nlp_service = NlpService()
        self.embedding_service = EmbeddingService()
        self.use_classifier_model = os.getenv("USE_RESUME_CLASSIFIER", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.classifier_bundle = self._load_classifier_bundle()

    def _load_classifier_bundle(self):
        if not self.use_classifier_model:
            logger.info("Custom resume classifier disabled via USE_RESUME_CLASSIFIER")
            return None

        if joblib is None:
            logger.warning("joblib not available - cannot load custom classifier")
            return None

        model_path = Path(__file__).resolve().parents[2] / "saved_models" / "resume_classifier.joblib"
        if not model_path.exists():
            logger.warning(f"Custom classifier model not found at {model_path}")
            return None

        try:
            bundle = joblib.load(model_path)
            if isinstance(bundle, dict) and bundle.get("pipeline") is not None:
                logger.info(f"✅ Custom resume classifier loaded successfully from {model_path}")
                return bundle
            logger.warning(f"Loaded model from {model_path} but it's not a valid bundle")
            return None
        except Exception as e:
            logger.error(f"Failed to load custom classifier: {e}")
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
            
            # Try to get confidence from predict_proba (ideal for probabilistic classifiers)
            if hasattr(pipeline, "predict_proba"):
                probs = pipeline.predict_proba([resume_text])[0]
                confidence = float(np.max(probs))
            # Fall back to decision_function for SVM-like classifiers (LinearSVC, SVC)
            elif hasattr(pipeline, "decision_function"):
                try:
                    decisions = pipeline.decision_function([resume_text])[0]
                    # For multi-class, get the decision score for the predicted class
                    if isinstance(decisions, np.ndarray):
                        # Multi-class case: get score for predicted class
                        class_idx = list(pipeline.classes_).index(predicted)
                        confidence = float(decisions[class_idx])
                    else:
                        # Binary case: use decision value directly
                        confidence = float(decisions)
                    # Normalize decision function to [0, 1] using sigmoid
                    confidence = 1.0 / (1.0 + np.exp(-confidence))
                except Exception as e:
                    logger.debug(f"Could not extract decision function confidence: {e}")
                    confidence = None
            
            if confidence is not None:
                logger.info(f"🎯 Custom model prediction: category={predicted}, confidence={confidence:.2%}")
            else:
                logger.info(f"🎯 Custom model prediction: category={predicted}, confidence=unavailable")
            return str(predicted), confidence
        except Exception as e:
            logger.warning(f"Custom model prediction failed, falling back: {e}")
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

    def _normalize_role_key(self, target_role: str) -> str:
        normalized = re.sub(r"[^a-z0-9 ]+", " ", target_role.lower())
        normalized = " ".join(normalized.split())
        return ROLE_ALIASES.get(normalized, normalized)

    def _target_category_probability(self, resume_text: str, target_category: str | None) -> float | None:
        if not self.classifier_bundle or not target_category:
            return None

        pipeline = self.classifier_bundle.get("pipeline")
        if pipeline is None:
            return None

        try:
            # Try predict_proba first (ideal for probabilistic classifiers)
            if hasattr(pipeline, "predict_proba"):
                classes = getattr(pipeline, "classes_", None)
                if classes is None:
                    return None

                classes_list = [str(label) for label in classes]
                if target_category not in classes_list:
                    return None

                probs = pipeline.predict_proba([resume_text])[0]
                class_index = classes_list.index(target_category)
                return float(probs[class_index])
            
            # Fall back to decision_function for SVM classifiers
            elif hasattr(pipeline, "decision_function"):
                classes = getattr(pipeline, "classes_", None)
                if classes is None:
                    return None

                classes_list = [str(label) for label in classes]
                if target_category not in classes_list:
                    return None

                decisions = pipeline.decision_function([resume_text])[0]
                class_index = classes_list.index(target_category)
                
                # Get decision score for target class
                if isinstance(decisions, np.ndarray):
                    score = float(decisions[class_index])
                else:
                    score = float(decisions)
                
                # Normalize to [0, 1] using sigmoid
                probability = 1.0 / (1.0 + np.exp(-score))
                logger.debug(f"Target category '{target_category}' probability: {probability:.2%}")
                return probability
            
            logger.debug(f"No probability method available for target category '{target_category}'")
            return None
            
        except Exception as e:
            logger.debug(f"Could not compute target category probability: {e}")
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
            timeline = "2 weeks"
            effort = "5-7 hrs/week"
        elif "senior" in level_key or "lead" in level_key:
            prefix = "Demonstrate advanced ownership"
            timeline = "3 weeks"
            effort = "6-8 hrs/week"
        else:
            prefix = "Build production readiness"
            timeline = "2-3 weeks"
            effort = "5-8 hrs/week"

        steps: List[Dict[str, str]] = []
        for index, skill in enumerate(missing_skills[:5]):
            title_skill = self._display_skill(self._canonicalize_skill(skill))
            priority = index + 1
            steps.append(
                {
                    "title": f"{prefix} in {title_skill}",
                    "description": (
                        f"Priority {priority} • Timebox: {timeline} • Effort: {effort}. "
                        f"Week 1: revise core concepts of {title_skill} and complete 3 targeted exercises. "
                        f"Week 2: implement a production-style mini project in {title_skill} aligned to {target_role}. "
                        f"Deliverable: publish code + README with trade-offs, metrics, and test evidence. "
                        f"Success criteria: demonstrate {title_skill} in at least one project bullet and one interview-ready story."
                    )
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

    def _normalize_skill_list(self, values: List[str]) -> List[str]:
        cleaned: List[str] = []
        for raw in values:
            canonical = self._canonicalize_skill(raw)
            if not canonical or not self._is_skill_like_canonical(canonical):
                continue
            cleaned.append(self._display_skill(canonical))
        return list(dict.fromkeys(cleaned))

    def _resume_mentions_skill(self, resume_text: str, skill: str) -> bool:
        normalized_resume = re.sub(r"[^a-z0-9+/\. ]+", " ", resume_text.lower())
        normalized_resume = f" {' '.join(normalized_resume.split())} "

        canonical_skill = self._canonicalize_skill(skill)
        if not canonical_skill:
            return False

        escaped = re.escape(canonical_skill).replace("\\ ", r"\s+")
        if re.search(rf"\b{escaped}\b", normalized_resume):
            return True

        compact_resume = normalized_resume.replace(" ", "")
        compact_skill = canonical_skill.replace(" ", "")
        if len(compact_skill) >= 4 and compact_skill in compact_resume:
            return True

        return False

    def _is_skill_like_canonical(self, canonical: str) -> bool:
        candidate = canonical.lower().strip()
        if not candidate:
            return False

        if "@" in candidate or "http://" in candidate or "https://" in candidate or "www." in candidate:
            return False

        if re.search(r"\b\d{7,}\b", candidate):
            return False

        if re.search(r"\+?\d[\d\s\-()]{7,}\d", candidate):
            return False

        if re.match(r"^[a-z]+\s+[a-z]+$", candidate):
            token_a, token_b = candidate.split(" ", 1)
            if token_a not in SKILL_HINT_TOKENS and token_b not in SKILL_HINT_TOKENS:
                return False

        normalized = re.sub(r"\s+", " ", candidate)
        if normalized in KNOWN_SKILL_CANONICAL:
            return True

        tokens = set(re.findall(r"[a-zA-Z+#./-]+", normalized))
        if not tokens:
            return False

        matched = len(tokens & SKILL_HINT_TOKENS)
        return matched >= 1

    def _detect_section_key(self, line: str) -> str | None:
        normalized = re.sub(r"[^a-z& ]+", " ", line.lower())
        normalized = " ".join(normalized.split())

        if not normalized:
            return None

        provider_tokens = {"aws", "azure", "google", "oracle", "coursera", "udemy", "nptel", "kubernetes", "scrum"}
        has_cert = (
            any(key in normalized for key in ["certification", "certifications"])
            or normalized in {"certificate", "certificates"}
        )
        has_award = any(key in normalized for key in ["honors", "awards", "achievements", "accomplishments"])

        if has_cert and any(token in normalized for token in provider_tokens) and normalized not in {
            "certification",
            "certifications",
            "certificate",
            "certificates",
            "certifications achievements",
            "certifications & achievements",
        }:
            has_cert = False
        if has_cert and has_award:
            return "awards_certifications"

        if (
            "technical skills" in normalized
            or normalized == "skills"
            or "tools and technologies" in normalized
            or "key skills" in normalized
            or "core competencies" in normalized
        ):
            return "skills"

        if normalized in {"projects", "project", "academic projects"} or "projects" in normalized:
            return "projects"

        if (
            "experience" in normalized
            or "work history" in normalized
            or "employment" in normalized
            or "internship" in normalized
        ):
            return "experience"

        if has_cert:
            return "certifications"

        if has_award:
            return "awards"

        if normalized in {"education", "summary", "objective", "contact", "profile", "academics"}:
            return "other"

        return None

    def _repair_fragmented_letters(self, text: str) -> str:
        def _compact(match: re.Match[str]) -> str:
            token = match.group(0)
            compact = re.sub(r"\s+", "", token)
            return compact if len(compact) >= 4 else token

        repaired = re.sub(r"\b(?:[A-Za-z]\s+){2,}[A-Za-z+#]+\b", _compact, text)

        # Join common PDF-fragmented tokens like "Develop ers" -> "Developers".
        def _join_pair(match: re.Match[str]) -> str:
            left = match.group(1)
            right = match.group(2)
            right_lower = right.lower()
            if right_lower in {"and", "or", "for", "with", "the", "to", "in", "on", "of", "out", "form", "data", "rank", "like", "than", "at", "by"}:
                return match.group(0)

            if len(left) >= 3 and len(right) <= 4 and (len(left) + len(right)) <= 18:
                return f"{left}{right}"
            return match.group(0)

        for _ in range(2):
            repaired = re.sub(r"\b([A-Za-z]{2,})\s([A-Za-z]{1,4})\b", _join_pair, repaired)

        return repaired

    def _split_candidate_line(self, value: str) -> List[str]:
        text = value.strip()
        if not text:
            return []

        candidates = [text]

        if len(text) > 150:
            split_by_period = []
            for candidate in candidates:
                split_by_period.extend(re.split(r"(?<=[.!?])\s+(?=[A-Z])", candidate))
            candidates = split_by_period

        if len(" ".join(candidates)) > 150:
            split_by_pipe = []
            for candidate in candidates:
                split_by_pipe.extend(re.split(r"\s*\|\s*", candidate))
            candidates = split_by_pipe

        refined: List[str] = []
        for candidate in candidates:
            piece = candidate.strip(" -")
            if not piece:
                continue
            # Insert line boundaries before likely bullet-style action starts.
            piece = re.sub(
                r"\s+(?=(?:Led|Built|Developed|Implemented|Managed|Created|Contributed|Solved|Won|Qualified|Reached|Organized|Deployed)\b)",
                "\n",
                piece,
                flags=re.IGNORECASE,
            )
            for segment in piece.split("\n"):
                segment_clean = segment.strip(" -")
                if segment_clean:
                    refined.append(segment_clean)

        return refined or [text]

    def _normalize_resume_text(self, resume_text: str) -> str:
        text = resume_text or ""
        text = text.replace("\\r\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
        if "\\n" in text:
            text = text.replace("\\n", "\n")

        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
        text = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219■▪●□▣◆◇◦]", "\n- ", text)

        for header in SECTION_HEADER_HINTS:
            pattern = rf"(?<!\n)\b{re.escape(header)}\b\s*[:\-]?"
            text = re.sub(pattern, lambda m: f"\n{m.group(0).strip()}\n", text, flags=re.IGNORECASE)

        normalized_lines: List[str] = []
        for raw_line in text.split("\n"):
            candidate = self._repair_fragmented_letters(raw_line.strip())
            candidate = re.sub(r"\s+", " ", candidate).strip()
            if not candidate:
                continue

            for segment in self._split_candidate_line(candidate):
                segment_clean = re.sub(r"\s+", " ", segment).strip()
                if segment_clean:
                    normalized_lines.append(segment_clean)

        return "\n".join(normalized_lines)

    def _clean_display_line(self, line: str) -> str:
        text = line.replace("\u2022", "-").replace("•", "-").strip()
        replacements = {
            "Ledthe": "Led the",
            "Builtan": "Built an",
            "Createdan": "Created an",
            "Createdanew": "Created a new",
            "Developedan": "Developed an",
            "ofthe": "of the",
            "formorethan": "for more than",
            "andtechnical": "and technical",
            "operationsand": "operations and",
            "TechnicalHead": "Technical Head",
            "GoogleData": "Google Data",
            "Pupilrank": "Pupil rank",
            "roundat": "round at",
            "Hacksout": "Hacks out",
            "platformslike": "platforms like",
            "systemby": "system by",
            "optimizingform": "optimizing form",
            "accuratedata": "accurate data",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)

        text = re.sub(r"\bHacksout\b", "Hacks out", text, flags=re.IGNORECASE)
        text = re.sub(r"\boptimizingform\b", "optimizing form", text, flags=re.IGNORECASE)

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        text = re.sub(r",(?=\S)", ", ", text)
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", text)
        text = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", text)
        text = re.sub(r"([a-z]{4,})(that|this|these|those)\b", r"\1 \2", text, flags=re.IGNORECASE)

        if re.search(r"[a-z]{20,}", text.lower()):
            for chunk in [
                "technical", "development", "official", "website", "architecture", "design",
                "ensuring", "accurate", "collection", "registrants", "registration", "integrating",
                "optimizing", "handling", "processes", "management", "analysis", "classifier",
                "streamlit", "kaggle", "project", "experience",
            ]:
                text = re.sub(rf"(?<=[a-z])({chunk})(?=[a-z])", r" \1 ", text, flags=re.IGNORECASE)
            text = re.sub(r"\s+", " ", text)

        text = re.sub(r"\b([A-Za-z]{3,})(than|like|with|from|into|onto|over|under|about|around|between|through|before|after|during|without|within|above|below|inside|outside|against|across|behind|beyond|towards|among|beside|underneath|at|by|for)\b", r"\1 \2", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(a)(new)\b", r"\1 \2", text, flags=re.IGNORECASE)

        text = self._repair_split_words(text)
        return text.strip(" -")

    def _repair_split_words(self, text: str) -> str:
        tokens = text.split()
        if not tokens:
            return text

        stop_tokens = {
            "and", "or", "for", "with", "the", "to", "in", "on", "of", "by", "at", "is", "a", "an",
            "out", "form", "data", "rank", "like", "than",
        }
        suffix_tokens = {
            "ing", "ion", "ions", "tion", "tions", "ed", "er", "ers", "ly", "ment", "ments",
            "ship", "ships", "able", "ance", "ence", "ary", "ory", "ents", "ized", "izer",
            "izers", "ality", "ities", "sion", "sions", "gform", "gdata", "dary", "lity",
        }

        repaired: List[str] = []
        index = 0
        while index < len(tokens):
            current = tokens[index]

            if index + 2 < len(tokens):
                middle = tokens[index + 1]
                right = tokens[index + 2]
                if (
                    current.isalpha()
                    and middle.isalpha()
                    and right.isalpha()
                    and len(current) >= 3
                    and middle.lower() in {"on", "in"}
                    and (right.lower() in suffix_tokens or re.match(r"^g[a-z]{2,}$", right.lower()))
                ):
                    repaired.append(f"{current}{middle}{right}")
                    index += 3
                    continue

            if index + 1 < len(tokens):
                right = tokens[index + 1]
                if (
                    current.isalpha()
                    and right.isalpha()
                    and len(current) >= 4
                    and right.lower() not in stop_tokens
                    and (
                        right.lower() in suffix_tokens
                        or (len(right) <= 3 and right.lower() not in {"api", "sql", "aws"})
                    )
                ):
                    repaired.append(f"{current}{right}")
                    index += 2
                    continue

            repaired.append(current)
            index += 1

        return " ".join(repaired)

    def _is_education_or_year_noise(self, text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return True

        if re.search(r"\b(aws|azure|google|oracle|kubernetes|scrum|nptel|coursera|udemy|certificate of completion|certified)\b", lowered):
            return False

        education_markers = [
            r"\bschool\b", r"\bcollege\b", r"\buniversity\b", r"\bclass\s*(x|xii|10|12)\b",
            r"\bsecondary\b", r"\bhigher secondary\b", r"\bssc\b", r"\bhsc\b",
            r"\bcgpa\b", r"\bgpa\b", r"\bpercentage\b", r"\bboard\b"
        ]

        if any(re.search(pattern, lowered) for pattern in education_markers):
            return True

        if re.fullmatch(r"(?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)\d{2})?", lowered):
            return True

        if re.search(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b", lowered):
            lexical = re.findall(r"[a-zA-Z]+", lowered)
            if len(lexical) <= 4:
                return True

        return False

    def _resume_mentions_phrase(self, resume_text: str, phrase: str) -> bool:
        normalized_resume = re.sub(r"[^a-z0-9+#./ ]+", " ", resume_text.lower())
        normalized_resume = " ".join(normalized_resume.split())

        normalized_phrase = re.sub(r"[^a-z0-9+#./ ]+", " ", phrase.lower())
        normalized_phrase = " ".join(normalized_phrase.split())
        if not normalized_phrase:
            return False

        escaped = r"\b" + r"\s+".join(re.escape(part) for part in normalized_phrase.split()) + r"\b"
        return bool(re.search(escaped, normalized_resume))

    def _is_readable_entry(self, value: str) -> bool:
        text = self._clean_display_line(value)
        if len(text) < 10:
            return False

        tokens = re.findall(r"[A-Za-z0-9+#./-]+", text)
        if len(tokens) < 2:
            return False

        very_long_tokens = [token for token in tokens if len(token) > 26]
        if len(very_long_tokens) >= 2:
            return False

        letters = [char.lower() for char in text if char.isalpha()]
        if not letters:
            return False

        vowels = sum(char in {"a", "e", "i", "o", "u"} for char in letters)
        vowel_ratio = vowels / max(len(letters), 1)
        return vowel_ratio >= 0.18

    def _compress_entry(self, value: str, max_len: int = 220) -> str:
        text = self._clean_display_line(value)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= max_len:
            return text

        clauses = [chunk.strip() for chunk in re.split(r"(?<=[.!?])\s+|\s*\|\s*", text) if chunk.strip()]
        if clauses:
            assembled = clauses[0]
            for clause in clauses[1:]:
                if len(assembled) + len(clause) + 2 > max_len:
                    break
                assembled = f"{assembled}. {clause}" if not assembled.endswith(".") else f"{assembled} {clause}"
            text = assembled

        return (text[: max_len - 1].rstrip() + "…") if len(text) > max_len else text

    def _merge_section_entries(self, lines: List[str]) -> List[str]:
        entries: List[str] = []
        for raw in lines:
            cleaned = self._clean_display_line(re.sub(r"^[•\-]\s*", "", raw).strip())
            if not cleaned:
                continue

            starts_new = bool(re.match(r"^[A-Z].{0,90}$", cleaned)) or bool(re.search(r"\b(led|built|developed|created|implemented|managed|organized)\b", cleaned.lower()))

            if not entries or starts_new:
                entries.append(cleaned)
            else:
                entries[-1] = f"{entries[-1]} {cleaned}".strip()

        return list(dict.fromkeys(entry.strip() for entry in entries if entry.strip()))

    def _infer_line_section(self, line: str, current_section: str | None = None) -> str | None:
        lowered = self._clean_display_line(line).lower()
        if not lowered:
            return None

        scores = {key: 0 for key in ["skills", "projects", "experience", "awards", "certifications", "other"]}

        for section_key, patterns in SECTION_SIGNAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, lowered):
                    scores[section_key] += 1

        if re.search(r"\b(19|20)\d{2}\b", lowered):
            scores["experience"] += 1

        if re.search(r"\b(gpa|cgpa|class x|class xii|b\.?tech|b\.?e\.?|m\.?tech|bachelor|master)\b", lowered):
            scores["other"] += 2

        if re.search(r"\b(certificate|certification|certified)\b", lowered):
            scores["certifications"] += 2

        if re.search(r"\b(project|portfolio|app|application|api|model|dataset|github)\b", lowered):
            scores["projects"] += 1

        if re.search(r"\b(intern|internship|worked|employment|organization|company|role)\b", lowered):
            scores["experience"] += 1

        if re.search(r"\b(awarded|winner|finalist|rank|recognition)\b", lowered):
            scores["awards"] += 1

        if re.search(r"\b(skills?|tools?|technologies|frameworks?)\b", lowered):
            scores["skills"] += 1

        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_section, top_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

        if top_score <= 0:
            return current_section

        # Require stronger signal before overriding an active section context.
        if current_section and top_section != current_section and top_score <= second_score:
            return current_section

        if current_section and top_section != current_section and (top_score - second_score) < 1:
            return current_section

        return top_section

    def _extract_resume_sections(self, resume_text: str) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {
            "skills": [],
            "projects": [],
            "experience": [],
            "awards": [],
            "certifications": [],
        }

        current_section: str | None = None
        for raw_line in resume_text.splitlines():
            line = self._clean_display_line(raw_line)
            if not line:
                continue

            detected = self._detect_section_key(line)
            if detected == "other":
                current_section = None
                continue

            if detected == "awards_certifications":
                current_section = "awards_certifications"
                continue

            if detected in sections:
                current_section = detected
                continue

            if current_section == "awards_certifications":
                if self._is_likely_certification_entry(line):
                    sections["certifications"].append(line)
                    continue

                if self._is_likely_award_entry(line):
                    sections["awards"].append(line)
                    continue

                inferred_combined = self._infer_line_section(line, current_section=None)
                if inferred_combined in {"awards", "certifications"}:
                    sections[inferred_combined].append(line)
                    continue

                if self._is_readable_entry(line) and not self._is_education_or_year_noise(line):
                    sections["awards"].append(line)
                continue

            inferred = self._infer_line_section(line, current_section=current_section)
            if inferred == "other":
                continue

            if current_section in {"awards", "certifications"} and inferred in {"awards", "certifications"}:
                target_section = inferred
            else:
                target_section = inferred if inferred in sections else current_section

            if target_section in sections:
                sections[target_section].append(line)

        if not any(sections.values()):
            fallback_lines = [self._clean_display_line(line) for line in resume_text.splitlines()]
            fallback_lines = [line for line in fallback_lines if line]
            sections["experience"] = [line for line in fallback_lines if self._infer_line_section(line) == "experience"][:10]
            sections["projects"] = [line for line in fallback_lines if self._infer_line_section(line) == "projects"][:10]
            sections["skills"] = [line for line in fallback_lines if re.search(r"\b(skills?|technologies|tools|frameworks?)\b", line.lower())][:6]
            sections["certifications"] = [line for line in fallback_lines if self._infer_line_section(line) == "certifications"][:8]
            sections["awards"] = [line for line in fallback_lines if self._infer_line_section(line) == "awards"][:8]

        for section_key in sections:
            deduped: List[str] = []
            seen: set[str] = set()
            for line in sections[section_key]:
                canonical = self._clean_display_line(line).lower()
                if canonical in seen:
                    continue
                seen.add(canonical)
                deduped.append(line)
            sections[section_key] = deduped

        return sections

    def _line_matches_any(self, text: str, patterns: List[str]) -> bool:
        lowered = text.lower()
        return any(re.search(pattern, lowered) for pattern in patterns)

    def _is_likely_certification_entry(self, text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return False

        if self._is_education_or_year_noise(lowered):
            return False

        if self._line_matches_any(lowered, AWARD_ENTRY_PATTERNS):
            return False

        if self._line_matches_any(lowered, CERTIFICATION_ENTRY_PATTERNS):
            return True

        # Enhanced detection for common cert patterns
        if re.search(r"\b(?:aws|gcp|azure|oracle|google cloud)\b", lowered):
            return True
        
        if re.search(r"\b(?:certified|certified?|certification)\b", lowered):
            return True

        if len(lowered) <= 90 and re.search(r"\b(associate|professional|foundation|practitioner|specialist|expert)\b", lowered):
            return True

        return False

    def _is_likely_award_entry(self, text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return False

        if self._line_matches_any(lowered, CERTIFICATION_ENTRY_PATTERNS):
            return False

        if self._line_matches_any(lowered, AWARD_ENTRY_PATTERNS):
            return True
        
        # Enhanced detection for common award patterns
        if re.search(r"\b(?:winner|finalist|ranked?|rank\s+\d+|top\s+\d+)\b", lowered):
            return True
        
        if re.search(r"\b(?:gold|silver|bronze)\s+(?:medal|award)\b", lowered):
            return True
        
        if re.search(r"\b(?:smart india|hackathon|competition|contest|challenge)\b", lowered):
            return True
        
        if re.search(r"\b(?:achievement|recognized|recognition|honor|distinction)\b", lowered):
            return True

        return False

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
        """Extract awards with improved detection logic."""
        awards: List[str] = []
        for line in self._merge_section_entries(award_lines):
            cleaned = self._clean_display_line(line)
            if len(cleaned) < 6:
                continue
            if self._is_education_or_year_noise(cleaned):
                continue
            if not self._is_readable_entry(cleaned):
                continue
            if cleaned.lower() in {"honors & awards", "awards", "honors"}:
                continue
            inferred = self._infer_line_section(cleaned)
            # Relaxed filtering - only skip if clearly not an award
            if inferred in {"other", "skills"}:
                continue
            # Don't exclude projects/experience if they're marked as awards
            if inferred in {"projects", "experience"} and not self._is_likely_award_entry(cleaned):
                continue
            # Relaxed cert exclusion - only exclude if it's ONLY a certification
            if re.search(r"\b(aws|azure|google|oracle|scrum|kubernetes)\b", cleaned.lower()):
                if not re.search(r"\b(winner|finalist|award|achievement|recognition|honor)\b", cleaned.lower()):
                    continue
            if not self._is_likely_award_entry(cleaned):
                # Even if not marked as award, include if reasonably looks like one
                if not re.search(r"\b(won|winner|finalist|achievement|recognized|recognition)\b", cleaned.lower()):
                    continue

            awards.append(self._compress_entry(cleaned, max_len=180))

        return list(dict.fromkeys(awards))[:8]

    def _extract_certifications_from_section(self, certification_lines: List[str]) -> List[str]:
        """Extract certifications with improved detection logic."""
        certs: List[str] = []
        for line in self._merge_section_entries(certification_lines):
            cleaned = self._clean_display_line(line)
            if len(cleaned) < 4:
                continue
            if self._is_education_or_year_noise(cleaned):
                continue
            if not self._is_readable_entry(cleaned):
                continue
            if cleaned.lower() in {"certifications", "certification"}:
                continue
            inferred = self._infer_line_section(cleaned)
            # Relaxed filtering - include if from cert/award section
            if inferred in {"other", "skills"}:
                continue
            if inferred in {"projects", "experience"} and not self._is_likely_certification_entry(cleaned):
                continue
            if not self._is_likely_certification_entry(cleaned):
                # Even if not marked as cert, include if has cert-like patterns
                if not re.search(r"\b(?:aws|azure|google|oracle|certified|certification|associate|professional)\b", cleaned.lower()):
                    continue
            certs.append(self._compress_entry(cleaned, max_len=180))

        ordered = list(dict.fromkeys(certs))
        filtered: List[str] = []
        for item in ordered:
            item_lower = item.lower()
            if any(item_lower != other.lower() and item_lower in other.lower() for other in ordered):
                continue
            filtered.append(item)

        return filtered[:10]

    def _extract_top_projects(self, project_lines: List[str], limit: int = 3) -> List[str]:
        if not project_lines:
            return []

        merged_lines = self._merge_section_entries(project_lines)
        blocks: List[Dict[str, object]] = []
        current_title: str | None = None
        current_points: List[str] = []

        for line in merged_lines:
            cleaned = self._clean_display_line(line)
            is_title_like = (
                len(cleaned) <= 100
                and not re.match(r"^(built|developed|created|implemented|led|managed|using|worked)\b", cleaned.lower())
            )

            if is_title_like:
                if current_title:
                    blocks.append({"title": current_title, "points": current_points.copy()})
                current_title = cleaned
                current_points = []
            else:
                if current_title:
                    current_points.append(cleaned)
                else:
                    current_title = cleaned

        if current_title:
            blocks.append({"title": current_title, "points": current_points.copy()})

        if not blocks:
            fallback = self._clean_display_line(project_lines[0])
            return [fallback] if fallback else []

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

        project_hint_tokens = {
            "project", "model", "nlp", "ml", "ai", "dataset", "api", "app", "application",
            "system", "classification", "prediction", "analysis", "accuracy", "tensorflow", "keras",
            "pytorch", "react", "python", "sql", "docker", "kubernetes", "github", "streamlit",
            "flask", "fastapi", "lstm", "gru"
        }
        experience_role_tokens = {
            "intern", "manager", "lead", "head", "coordinator", "volunteer", "president",
            "secretary", "chair", "associate", "executive", "member", "officer", "captain"
        }
        experience_org_tokens = {
            "ieee", "club", "college", "university", "company", "team", "society", "committee"
        }

        ranked: List[tuple[int, str]] = []
        for block in blocks:
            title = str(block["title"])
            points = [str(item) for item in block["points"]]
            joined = f"{title} {' '.join(points)}".lower()
            score = sum(weight for key, weight in keyword_weights.items() if key in joined)
            score += len(re.findall(r"\b\d+(?:\.\d+)?%?\b", joined))
            score += min(len(points), 3)

            summary_point = points[0] if points else ""
            summary = f"{title} — {summary_point}".strip(" —")
            if summary and not self._is_readable_entry(summary):
                continue
            summary = self._compress_entry(summary, max_len=220)

            summary_lower = summary.lower()
            summary_tokens = set(re.findall(r"[a-zA-Z+#./-]+", summary_lower))

            role_like = any(token in summary_tokens for token in experience_role_tokens)
            org_like = any(token in summary_tokens for token in experience_org_tokens)
            project_like = any(token in summary_tokens for token in project_hint_tokens)

            if role_like and org_like:
                continue

            if not project_like and score < 3:
                continue

            if summary:
                ranked.append((score, summary))

        ranked.sort(key=lambda item: item[0], reverse=True)
        ordered = [summary for _, summary in ranked[:limit]]

        if len(ordered) < limit:
            fallback_candidates: List[str] = []
            for line in merged_lines:
                cleaned = self._clean_display_line(line)
                if not self._is_readable_entry(cleaned):
                    continue
                lowered = cleaned.lower()
                if len(cleaned) < 18:
                    continue
                if self._infer_line_section(cleaned) == "other":
                    continue
                if re.search(r"\b(intern|lead|manager|coordinator|volunteer|member|club|committee)\b", lowered):
                    continue
                if not re.search(r"\b(project|app|system|model|classifier|dataset|nlp|ml|ai|streamlit|kaggle|python|react|api)\b", lowered):
                    continue
                fallback_candidates.append(self._compress_entry(cleaned, max_len=220))

            for candidate in fallback_candidates:
                if candidate not in ordered:
                    ordered.append(candidate)
                if len(ordered) >= limit:
                    break

        return list(dict.fromkeys(ordered[:limit]))

    def _extract_best_project(self, project_lines: List[str]) -> str | None:
        top_projects = self._extract_top_projects(project_lines, limit=1)
        return top_projects[0] if top_projects else None

    def _extract_best_experiences(self, experience_lines: List[str]) -> List[str]:
        """Extract best experiences with improved and relaxed filtering."""
        if not experience_lines:
            return []

        cleaned_lines = self._merge_section_entries(experience_lines)
        cleaned_lines = [self._clean_display_line(line) for line in cleaned_lines if len(line) >= 6]

        keyword_weights = {
            "led": 3,
            "managed": 3,
            "coordinated": 3,
            "delivered": 2,
            "built": 2,
            "improved": 3,
            "organized": 2,
            "achieved": 2,
            "supported": 1,
            "assessed": 1,
            "mentored": 2,
            "guided": 1,
            "created": 2,
            "developed": 2,
            "implemented": 2,
        }

        scored: List[tuple[int, str]] = []
        for line in cleaned_lines:
            if not self._is_readable_entry(line):
                continue
            text = line.lower()
            if self._is_education_or_year_noise(line):
                continue
            # Relaxed filtering - don't exclude projects/certifications if they have experience markers
            inferred = self._infer_line_section(line)
            if inferred == "other":
                continue
            if inferred == "certifications" and not re.search(r"\b(led|managed|worked|coordinated|team|organization|company)\b", text):
                continue
            
            # More lenient on project-experience overlap
            has_action_verb = bool(re.search(r"\b(led|managed|coordinated|delivered|built|improved|organized|achieved|supported|assessed|created|developed|implemented|mentored|worked|guided|spearheaded|pioneered)\b", text))
            
            # Check for role/context indicators but don't require them
            has_role_context = bool(
                re.search(
                    r"\b(intern|internship|job|worked|work experience|employment|company|organization|club|committee|chapter|member|coordinator|lead|head|president|secretary|volunteer|executive|associate|officer|team)\b",
                    text,
                )
            )
            
            # Score based on action verbs and context
            score = 0
            if has_action_verb:
                score += 3
            if has_role_context:
                score += 2
            
            # Skip only if no action verb AND no role context (very generic)
            if score == 0:
                if len(line) < 40:  # Very short lines without context
                    continue
                score = 1  # Give minimal credit to longer generic lines
            
            # Education/year noise check
            if re.search(r"\b(hsc|ssc|cgpa|gpa|bachelor|master|degree|education|school|college|university|xii|x)\b", text):
                if not has_action_verb and not has_role_context:
                    continue
                score = max(0, score - 2)  # Penalize but don't exclude if has other markers

            score += sum(weight for key, weight in keyword_weights.items() if key in text)
            score += len(re.findall(r"\b\d+(?:,\d{3})*\s*(?:%|million|thousand|people|team|members?)?\b", text))
            if len(line) > 60:
                score += 1
            if len(line) > 100:
                score += 1
            
            if score > 0:
                scored.append((score, self._compress_entry(line, max_len=220)))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = [line for _, line in scored[:3]]
        return list(dict.fromkeys(top))

    def _extract_education_highlights(self, resume_text: str) -> List[str]:
        highlights: List[str] = []
        for raw_line in resume_text.splitlines():
            line = self._clean_display_line(raw_line)
            if not line:
                continue
            lowered = line.lower()
            if not re.search(r"\b(education|bachelor|master|degree|diploma|college|university|school|hsc|ssc|cgpa|gpa|xii|x)\b", lowered):
                continue
            if len(line) < 4:
                continue
            entry = self._compress_entry(line, max_len=180)
            if entry not in highlights:
                highlights.append(entry)
            if len(highlights) >= 5:
                break
        return highlights

    def _extract_soft_skills_highlights(self, resume_text: str, transferable_skills: List[str]) -> List[str]:
        canonical = [item.strip().title() for item in transferable_skills if item.strip()]
        if canonical:
            return list(dict.fromkeys(canonical))[:5]

        soft_skill_tokens = [
            "Communication",
            "Leadership",
            "Team Collaboration",
            "Problem Solving",
            "Time Management",
            "Stakeholder Management",
            "Ownership",
            "Adaptability",
            "Critical Thinking",
        ]
        lowered = resume_text.lower()
        detected = [token for token in soft_skill_tokens if token.lower().split()[0] in lowered]
        return detected[:5]

    def run(self, resume_text: str, target_role: str, current_skills: List[str], profession: str, level: str) -> AnalysisResult:
        resume_text = self._normalize_resume_text(resume_text)
        
        classifier_status = "🎯 ENABLED" if self.classifier_bundle else "⚠️ DISABLED"
        logger.info(f"Starting analysis with custom model: {classifier_status}")

        normalized_resume_text = " ".join(resume_text.split())
        sections = self._extract_resume_sections(resume_text)

        # Resolve role-specific benchmark skills from our curated dictionary.
        role_key = self._normalize_role_key(target_role)
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

        for role_skill in role_skills:
            if self._resume_mentions_skill(resume_text, role_skill):
                canonical = self._canonicalize_skill(role_skill)
                if canonical and canonical not in resume_skill_display_by_canonical:
                    resume_skill_display_by_canonical[canonical] = role_skill

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

        transferable = [skill for skill in GENERIC_TRANSFERABLE_SKILLS if self._resume_mentions_phrase(resume_text, skill)]
        transferable_display = list(dict.fromkeys(self._clean_display_line(skill.title()) for skill in transferable if skill.strip()))[:6]
        transferable_canonical = {self._canonicalize_skill(skill) for skill in transferable}

        strengths: List[str] = []
        for canonical in resume_role_strengths:
            strengths.append(self._display_skill(canonical))

        for canonical in additional_resume_strengths[:6]:
            if not self._is_skill_like_canonical(canonical):
                continue
            if canonical in transferable_canonical:
                continue
            strengths.append(self._display_skill(canonical))

        strengths = list(
            dict.fromkeys(
                [
                    item.strip()
                    for item in strengths
                    if item.strip() and self._is_skill_like_canonical(self._canonicalize_skill(item))
                ]
            )
        )[:14]

        resume_strength_set = set(resume_role_strengths)
        missing_skills = [
            role_skill
            for role_skill in role_skills
            if self._canonicalize_skill(role_skill) not in resume_strength_set
        ]

        # Semantic similarity compares full resume context against target role skill profile.
        similarity = 0.0
        try:
            embeddings = self.embedding_service.encode([resume_text, " ".join(role_skills)])
            similarity = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])
            if np.isnan(similarity):
                similarity = 0.0
        except Exception:
            similarity = 0.0
        similarity = max(0.0, min(1.0, similarity))

        # Final score emphasizes resume evidence, then semantic fit.
        resume_role_coverage = len(resume_role_strengths) / max(len(role_skills), 1)
        combined_role_coverage = len(set(resume_role_strengths + profile_role_strengths)) / max(len(role_skills), 1)
        heuristic_score = max(0.0, min(100.0, (0.5 * similarity + 0.2 * resume_role_coverage + 0.3 * combined_role_coverage) * 100))

        predicted_category, predicted_confidence = self._predict_category(resume_text)
        target_probability = self._target_category_probability(resume_text, target_category)

        if target_probability is not None:
            ml_component = 100.0 * target_probability
            match_score = (0.82 * heuristic_score) + (0.18 * ml_component)
            logger.info(f"📊 Custom model contribution: heuristic={heuristic_score:.2f}, ml_component={ml_component:.2f}, final_match_score={match_score:.2f}")
        else:
            match_score = heuristic_score
            logger.info(f"ℹ️ Custom model unavailable, using heuristic score: {heuristic_score:.2f}")
        match_score = max(0.0, min(100.0, match_score))
        logger.info(f"✨ Final analysis: category={predicted_category if predicted_category else 'unknown'}, confidence={predicted_confidence:.2%}" if predicted_confidence else f"✨ Final analysis: category={predicted_category if predicted_category else 'unknown'}")

        local_roadmap = self._build_roadmap(missing_skills, target_role, level)
        roadmap = local_roadmap
        roadmap_source = "local"
        roadmap_model = None

        section_certs = self._extract_certifications_from_section(sections["certifications"])
        detected_certs = self._extract_resume_certifications(resume_text, role_key)
        certs_raw = list(dict.fromkeys(section_certs + detected_certs))
        certs: List[str] = []
        for item in certs_raw:
            lowered = item.lower().strip()
            if any(lowered != other.lower().strip() and lowered in other.lower().strip() for other in certs_raw):
                continue
            certs.append(item)
        awards = self._extract_awards(sections["awards"])
        cert_tokens = {token.lower() for cert in certs for token in re.findall(r"[a-zA-Z0-9+#./-]+", cert)}
        filtered_awards: List[str] = []
        for item in awards:
            item_tokens = {token.lower() for token in re.findall(r"[a-zA-Z0-9+#./-]+", item)}
            overlap = len(item_tokens & cert_tokens)
            if overlap >= 2:
                continue
            filtered_awards.append(item)
        awards = filtered_awards
        featured_projects = self._extract_top_projects(sections["projects"], limit=3)
        featured_project = featured_projects[0] if featured_projects else None
        featured_experiences = self._extract_best_experiences(sections["experience"])
        education_highlights = self._extract_education_highlights(resume_text)
        soft_skills_highlights = self._extract_soft_skills_highlights(resume_text, transferable_display)

        overview_source = "local"
        overview_model = None

        # Parsed structure is persisted in MongoDB for dashboard rendering.
        parsed_resume = {
            "profession": profession,
            "targetRole": target_role,
            "experienceLevel": level,
            "skillsExtracted": self._normalize_skill_list(section_skills + extracted_skills),
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
            "featuredProjects": featured_projects,
            "featuredExperiences": featured_experiences,
            "educationHighlights": education_highlights,
            "softSkillsHighlights": soft_skills_highlights,
            "overviewSource": overview_source,
            "overviewModel": overview_model,
            "roadmapSource": roadmap_source,
            "roadmapModel": roadmap_model,
            "modelUsed": "resume_classifier.joblib" if self.classifier_bundle else "heuristic"
        }

        return AnalysisResult(
            parsed_resume=parsed_resume,
            match_score=round(match_score, 2),
            strengths=strengths,
            skill_gaps=missing_skills,
            transferable_skills=transferable_display,
            roadmap=roadmap,
            certifications=certs,
            predicted_category=predicted_category,
            predicted_confidence=predicted_confidence,
        )
