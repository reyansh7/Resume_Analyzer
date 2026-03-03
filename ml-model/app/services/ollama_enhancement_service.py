from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Dict, List
from urllib import request


class OllamaEnhancementService:
    def __init__(self) -> None:
        self._load_local_env_file()
        self.enabled = os.getenv("USE_OLLAMA_ENHANCEMENTS", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.base_url = (os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip() or "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b").strip() or "deepseek-r1:8b"
        self.timeout_ms = self._parse_int_env("OLLAMA_TIMEOUT_MS", default_value=20000)
        self.max_retries = self._parse_int_env("OLLAMA_MAX_RETRIES", default_value=1)
        self._cache: Dict[str, object] = {}
        self._lock = threading.Lock()

    def _load_local_env_file(self) -> None:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if not env_path.exists():
            return

        for line in env_path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    def _parse_int_env(self, env_key: str, default_value: int) -> int:
        raw_value = os.getenv(env_key, str(default_value)).strip()
        try:
            return max(0, int(raw_value))
        except Exception:
            return default_value

    def _call_json(self, prompt: str) -> dict | None:
        if not self.enabled:
            return None

        cache_key = f"{self.model}:{hash(prompt)}"
        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                return cached if isinstance(cached, dict) else None

        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
            "format": {
                "type": "object",
                "properties": {
                    "prioritized_gaps": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["prioritized_gaps"],
            },
        }

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        attempts = max(1, self.max_retries + 1)
        for _ in range(attempts):
            try:
                with request.urlopen(req, timeout=max(1, self.timeout_ms / 1000.0)) as response:
                    raw = response.read().decode("utf-8")

                parsed = json.loads(raw)
                content = parsed.get("response")
                if not isinstance(content, str) or not content.strip():
                    continue

                try:
                    result = json.loads(content)
                except Exception:
                    match = re.search(r"\{[\s\S]*\}", content)
                    result = json.loads(match.group(0)) if match else None

                if isinstance(result, dict):
                    with self._lock:
                        self._cache[cache_key] = result
                    return result
            except Exception:
                continue

        return None

    def _call_json_with_schema(self, prompt: str, schema: dict) -> dict | None:
        if not self.enabled:
            return None

        cache_key = f"{self.model}:{hash(prompt + json.dumps(schema, sort_keys=True))}"
        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                return cached if isinstance(cached, dict) else None

        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
            "format": schema,
        }

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        attempts = max(1, self.max_retries + 1)
        for _ in range(attempts):
            try:
                with request.urlopen(req, timeout=max(1, self.timeout_ms / 1000.0)) as response:
                    raw = response.read().decode("utf-8")

                parsed = json.loads(raw)
                content = parsed.get("response")
                if not isinstance(content, str) or not content.strip():
                    continue

                try:
                    result = json.loads(content)
                except Exception:
                    match = re.search(r"\{[\s\S]*\}", content)
                    result = json.loads(match.group(0)) if match else None

                if isinstance(result, dict):
                    with self._lock:
                        self._cache[cache_key] = result
                    return result
            except Exception:
                continue

        return None

    def prioritize_gaps(
        self,
        target_role: str,
        level: str,
        candidate_gaps: List[str],
        strengths: List[str],
        limit: int = 8,
    ) -> List[str] | None:
        if not self.enabled or not candidate_gaps:
            return None

        prompt = (
            "You are a resume skill-gap prioritization engine.\n"
            f"Target role: {target_role}\n"
            f"Level: {level}\n"
            f"Candidate gaps: {candidate_gaps}\n"
            f"Strengths: {strengths}\n"
            f"Return strict JSON only: {{\"prioritized_gaps\":[...]}} with top {limit} items, "
            "and use only items from candidate_gaps."
        )

        result = self._call_json(prompt)
        if not result:
            return None

        raw = result.get("prioritized_gaps")
        if not isinstance(raw, list):
            return None

        allowed = {item.lower() for item in candidate_gaps}
        clean: List[str] = []
        for item in raw:
            if not isinstance(item, str):
                continue
            normalized = item.strip()
            if not normalized:
                continue
            if normalized.lower() in allowed and normalized not in clean:
                clean.append(normalized)
            if len(clean) >= limit:
                break

        return clean or None

    def generate_overview_highlights(
        self,
        resume_text: str,
        target_role: str,
        level: str,
        experience_candidates: List[str],
        soft_skill_candidates: List[str],
        education_candidates: List[str],
    ) -> dict | None:
        if not self.enabled:
            return None

        prompt = (
            "You are an expert resume overview summarizer for a dashboard.\n"
            "Return concise, factual highlights in strict JSON only.\n"
            "Do not invent facts. Use only provided resume text and candidate lists.\n"
            "Critical rules:\n"
            "1) experience_highlights must include ONLY clubs, committees, internships, jobs, roles, organizations, work history.\n"
            "2) experience_highlights must NEVER include education lines (degree, school, college, university, HSC/SSC/CGPA/GPA).\n"
            "3) soft_skills_highlights should be short phrases (2-8 words) like Communication, Leadership, Team Collaboration.\n"
            "4) education_highlights should contain education credentials only.\n"
            "5) Keep each list max 5 items; each item under 140 chars.\n\n"
            f"Target role: {target_role}\n"
            f"Experience level: {level}\n"
            f"Experience candidates: {experience_candidates}\n"
            f"Soft skill candidates: {soft_skill_candidates}\n"
            f"Education candidates: {education_candidates}\n"
            f"Resume text (first 7000 chars): {resume_text[:7000]}"
        )

        schema = {
            "type": "object",
            "properties": {
                "experience_highlights": {"type": "array", "items": {"type": "string"}},
                "soft_skills_highlights": {"type": "array", "items": {"type": "string"}},
                "education_highlights": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["experience_highlights", "soft_skills_highlights", "education_highlights"],
        }

        result = self._call_json_with_schema(prompt=prompt, schema=schema)
        if not isinstance(result, dict):
            return None

        def _clean_list(value: object, limit: int) -> List[str]:
            if not isinstance(value, list):
                return []
            out: List[str] = []
            for item in value:
                if not isinstance(item, str):
                    continue
                text = item.strip()
                if not text:
                    continue
                if text not in out:
                    out.append(text[:140])
                if len(out) >= limit:
                    break
            return out

        return {
            "experience_highlights": _clean_list(result.get("experience_highlights"), limit=5),
            "soft_skills_highlights": _clean_list(result.get("soft_skills_highlights"), limit=5),
            "education_highlights": _clean_list(result.get("education_highlights"), limit=5),
        }
