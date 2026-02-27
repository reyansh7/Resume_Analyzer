import re
from typing import List

try:
    import spacy
except Exception:
    spacy = None

from app.utils.skill_dictionary import ROLE_SKILL_MAP


SKILL_ALIASES = {
    "node.js": "node",
    "node js": "node",
    "nodejs": "node",
    "java script": "javascript",
    "powerbi": "power bi",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "ci cd": "ci/cd",
    "nextjs": "next.js",
    "next js": "next.js",
    "expressjs": "express",
    "express js": "express",
    "postgres": "postgresql",
}

EXTRA_SKILLS = {
    "java",
    "javascript",
    "c",
    "c++",
    "c#",
    "html",
    "css",
    "mongodb",
    "mysql",
    "git",
    "github",
    "flask",
    "fastapi",
    "tensorflow",
    "pytorch",
    "nlp",
    "machine learning",
    "deep learning",
    "rest api",
    "next.js",
    "express",
    "postgresql",
    "redis",
    "kubernetes",
    "docker",
}

ALL_KNOWN_SKILLS = sorted(
    {
        skill.strip().lower()
        for skills in ROLE_SKILL_MAP.values()
        for skill in skills
    }
    | EXTRA_SKILLS
)


class NlpService:
    def __init__(self) -> None:
        try:
            if spacy is not None:
                self.nlp = spacy.load("en_core_web_sm")
            else:
                self.nlp = None
        except Exception:
            self.nlp = spacy.blank("en") if spacy is not None else None

    def _normalize_skill(self, value: str) -> str:
        normalized = value.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return SKILL_ALIASES.get(normalized, normalized)

    def _normalize_text(self, value: str) -> str:
        normalized = value.lower().replace("\\n", " ")
        normalized = re.sub(r"[^a-z0-9+#./\-\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _skill_pattern(self, skill: str) -> str:
        parts = [part for part in re.split(r"\s+", skill) if part]
        if not parts:
            return r"$a"

        joined = r"(?:[\s\-/]+)".join(re.escape(part) for part in parts)
        return rf"(?<![a-z0-9+#]){joined}(?![a-z0-9+#])"

    def extract_skills(self, text: str, role: str) -> List[str]:
        role_key = role.lower().strip()
        role_skills = [self._normalize_skill(item) for item in ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])]
        candidate_skills = list(dict.fromkeys(role_skills + [self._normalize_skill(item) for item in ALL_KNOWN_SKILLS]))

        normalized_text = self._normalize_text(text)
        found: set[str] = set()
        for skill in candidate_skills:
            if re.search(self._skill_pattern(skill), normalized_text):
                found.add(skill)

        if self.nlp is None:
            return sorted(set(found))

        doc = self.nlp(text[:15000])
        noun_chunks = []
        if hasattr(doc, "noun_chunks"):
            try:
                noun_chunks = [chunk.text.lower().strip() for chunk in doc.noun_chunks][:30]
            except ValueError:
                noun_chunks = []

        candidate_skill_set = set(candidate_skills)
        for chunk in noun_chunks:
            normalized_chunk = self._normalize_skill(chunk)
            if len(normalized_chunk) < 3:
                continue
            if len(normalized_chunk.split()) > 4:
                continue
            if normalized_chunk in candidate_skill_set:
                found.add(normalized_chunk)

        return sorted(set(found))
