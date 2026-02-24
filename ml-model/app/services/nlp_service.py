import re
from typing import List

try:
    import spacy
except Exception:
    spacy = None

from app.utils.skill_dictionary import ROLE_SKILL_MAP


class NlpService:
    def __init__(self) -> None:
        try:
            if spacy is not None:
                self.nlp = spacy.load("en_core_web_sm")
            else:
                self.nlp = None
        except Exception:
            self.nlp = spacy.blank("en") if spacy is not None else None

    def extract_skills(self, text: str, role: str) -> List[str]:
        role_key = role.lower().strip()
        role_skills = ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])

        normalized_text = text.lower()
        found = [skill for skill in role_skills if re.search(rf"\b{re.escape(skill)}\b", normalized_text)]

        if self.nlp is None:
            return sorted(set(found))

        doc = self.nlp(text[:15000])
        noun_chunks = []
        if hasattr(doc, "noun_chunks"):
            noun_chunks = [chunk.text.lower().strip() for chunk in doc.noun_chunks][:30]

        for chunk in noun_chunks:
            if chunk in role_skills and chunk not in found:
                found.append(chunk)

        return sorted(set(found))
