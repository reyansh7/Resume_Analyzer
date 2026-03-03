import json
import os
import re
import threading
from pathlib import Path
from typing import Dict, List
from urllib import request


class OllamaRoadmapService:
    def __init__(self) -> None:
        self._load_local_env_file()
        self.enabled = os.getenv("USE_OLLAMA_ROADMAP", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.base_url = (os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip() or "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b").strip() or "deepseek-r1:8b"
        self.timeout_ms = self._parse_int_env("OLLAMA_TIMEOUT_MS", default_value=20000)
        self.max_retries = self._parse_int_env("OLLAMA_MAX_RETRIES", default_value=1)
        self._cache: Dict[str, List[Dict[str, str]]] = {}
        self._cache_lock = threading.Lock()

    def _load_local_env_file(self) -> None:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if not env_path.exists():
            return

        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                raw = line.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue

                key, value = raw.split("=", 1)
                env_key = key.strip()
                env_value = value.strip().strip('"').strip("'")
                if not env_key:
                    continue

                if env_key.startswith("OLLAMA_") or env_key == "USE_OLLAMA_ROADMAP":
                    os.environ[env_key] = env_value
                elif env_key not in os.environ:
                    os.environ[env_key] = env_value
        except Exception:
            return

    def _parse_int_env(self, env_key: str, default_value: int) -> int:
        raw_value = os.getenv(env_key, str(default_value)).strip()
        try:
            return max(0, int(raw_value))
        except Exception:
            return default_value

    def generate_roadmap(
        self,
        target_role: str,
        level: str,
        strengths: List[str],
        skill_gaps: List[str],
        max_steps: int = 5,
    ) -> List[Dict[str, str]] | None:
        if not self.enabled:
            return None

        if not skill_gaps:
            return []

        cache_key = self._build_cache_key(
            target_role=target_role,
            level=level,
            strengths=strengths,
            skill_gaps=skill_gaps,
            max_steps=max_steps,
        )

        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        roadmap = self._request_with_retry(
            target_role=target_role,
            level=level,
            strengths=strengths,
            skill_gaps=skill_gaps,
            max_steps=max_steps,
        )

        if roadmap is None:
            return None

        with self._cache_lock:
            self._cache[cache_key] = roadmap

        return roadmap

    def _build_cache_key(
        self,
        target_role: str,
        level: str,
        strengths: List[str],
        skill_gaps: List[str],
        max_steps: int,
    ) -> str:
        payload = {
            "targetRole": target_role.strip().lower(),
            "level": level.strip().lower(),
            "strengths": [item.strip().lower() for item in strengths if item.strip()],
            "skillGaps": [item.strip().lower() for item in skill_gaps if item.strip()],
            "maxSteps": max_steps,
            "model": self.model,
        }
        return json.dumps(payload, sort_keys=True)

    def _request_with_retry(
        self,
        target_role: str,
        level: str,
        strengths: List[str],
        skill_gaps: List[str],
        max_steps: int,
    ) -> List[Dict[str, str]] | None:
        attempts = max(1, self.max_retries + 1)
        for _ in range(attempts):
            try:
                generated = self._request_once(
                    target_role=target_role,
                    level=level,
                    strengths=strengths,
                    skill_gaps=skill_gaps,
                    max_steps=max_steps,
                )
                if generated is not None:
                    return generated
            except Exception:
                continue
        return None

    def _request_once(
        self,
        target_role: str,
        level: str,
        strengths: List[str],
        skill_gaps: List[str],
        max_steps: int,
    ) -> List[Dict[str, str]] | None:
        endpoint = f"{self.base_url}/api/generate"
        prompt = self._build_prompt(
            target_role=target_role,
            level=level,
            strengths=strengths,
            skill_gaps=skill_gaps,
            max_steps=max_steps,
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
            "format": {
                "type": "object",
                "properties": {
                    "roadmap": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["title", "description"],
                        },
                    }
                },
                "required": ["roadmap"],
            },
        }

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with request.urlopen(req, timeout=max(1, self.timeout_ms / 1000.0)) as response:
            raw = response.read().decode("utf-8")

        parsed = json.loads(raw)
        content = parsed.get("response")
        if not isinstance(content, str) or not content.strip():
            return None

        roadmap = self._extract_valid_roadmap(content, max_steps=max_steps)
        return roadmap if roadmap else None

    def _extract_valid_roadmap(self, content: str, max_steps: int) -> List[Dict[str, str]]:
        payload: Dict[str, object] | None = None

        try:
            loaded = json.loads(content)
            if isinstance(loaded, dict):
                payload = loaded
        except Exception:
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                try:
                    loaded = json.loads(json_match.group(0))
                    if isinstance(loaded, dict):
                        payload = loaded
                except Exception:
                    payload = None

        if payload is None:
            return []

        steps = payload.get("roadmap")
        if not isinstance(steps, list):
            return []

        cleaned: List[Dict[str, str]] = []
        for item in steps:
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            description = item.get("description")
            if not isinstance(title, str) or not isinstance(description, str):
                continue

            title_clean = title.strip()
            description_clean = description.strip()
            if not title_clean or not description_clean:
                continue

            cleaned.append(
                {
                    "title": title_clean[:120],
                    "description": description_clean[:900],
                }
            )
            if len(cleaned) >= max_steps:
                break

        return cleaned

    def _build_prompt(
        self,
        target_role: str,
        level: str,
        strengths: List[str],
        skill_gaps: List[str],
        max_steps: int,
    ) -> str:
        strengths_text = ", ".join(strengths[:12]) if strengths else "None provided"
        gaps_text = ", ".join(skill_gaps[:10])

        return (
            "You are an expert technical career coach. "
            "Create a concise, practical roadmap with actionable milestones. "
            "Use only provided data and do not invent missing skills beyond the supplied skill gaps.\n\n"
            f"Target role: {target_role}\n"
            f"Experience level: {level}\n"
            f"Current strengths: {strengths_text}\n"
            f"Skill gaps to address: {gaps_text}\n"
            f"Required number of roadmap steps: up to {max_steps}\n\n"
            "Each step must include:\n"
            "- title: short and specific\n"
            "- description: 3-4 sentences with timeline, deliverable, and success criteria\n\n"
            "Return only strict JSON in this format:\n"
            "{\"roadmap\":[{\"title\":\"...\",\"description\":\"...\"}]}"
        )
