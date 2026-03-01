from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Dict, List
from urllib import request


class GeminiEnhancementService:
    def __init__(self) -> None:
        self._load_local_env_file()
        self.enabled = os.getenv("USE_GEMINI_ENHANCEMENTS", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"
        self.timeout_ms = int(os.getenv("GEMINI_TIMEOUT_MS", "8000") or "8000")
        self._cache: Dict[str, object] = {}
        self._lock = threading.Lock()

        if self.enabled and not self.api_key:
            self.enabled = False

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

    def _call_json(self, prompt: str) -> dict | None:
        if not self.enabled:
            return None

        cache_key = f"{self.model}:{hash(prompt)}"
        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                return cached if isinstance(cached, dict) else None

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.9,
                "maxOutputTokens": 1200,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=max(1, self.timeout_ms / 1000.0)) as response:
                raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            candidates = parsed.get("candidates")
            if not isinstance(candidates, list) or not candidates:
                return None
            content = candidates[0].get("content", {})
            parts = content.get("parts", []) if isinstance(content, dict) else []
            text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
            if not text:
                return None

            try:
                result = json.loads(text)
            except Exception:
                match = re.search(r"\{[\s\S]*\}", text)
                result = json.loads(match.group(0)) if match else None
            if isinstance(result, dict):
                with self._lock:
                    self._cache[cache_key] = result
                return result
        except Exception:
            return None

        return None

    def prioritize_gaps(self, target_role: str, level: str, candidate_gaps: List[str], strengths: List[str], limit: int = 8) -> List[str] | None:
        if not self.enabled or not candidate_gaps:
            return None

        prompt = (
            "You are a resume skill-gap prioritization engine.\n"
            f"Target role: {target_role}\n"
            f"Level: {level}\n"
            f"Candidate gaps: {candidate_gaps}\n"
            f"Strengths: {strengths}\n"
            f"Return strict JSON: {{\"prioritized_gaps\":[...]}} with top {limit} items only from candidate_gaps."
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
            if item.lower() in allowed and item not in clean:
                clean.append(item)
            if len(clean) >= limit:
                break
        return clean or None

    def improve_rewrites(self, target_role: str, bullets: List[dict], limit: int = 6) -> List[dict] | None:
        if not self.enabled or not bullets:
            return None

        condensed = [
            {"section": item.get("section", "Experience/Projects"), "before": item.get("before", "")}
            for item in bullets[:limit]
            if isinstance(item, dict)
        ]

        prompt = (
            "You are an ATS-safe resume rewriting assistant.\n"
            f"Target role: {target_role}\n"
            f"Bullets: {condensed}\n"
            "Rewrite concisely with strong action verbs and measurable impact.\n"
            "Return strict JSON: {\"rewrites\":[{\"section\":\"...\",\"before\":\"...\",\"after\":\"...\",\"improvement_type\":\"...\"}]}."
        )

        result = self._call_json(prompt)
        if not result:
            return None
        rewrites = result.get("rewrites")
        if not isinstance(rewrites, list):
            return None

        valid: List[dict] = []
        for item in rewrites:
            if not isinstance(item, dict):
                continue
            before = item.get("before")
            after = item.get("after")
            if not isinstance(before, str) or not isinstance(after, str):
                continue
            valid.append(
                {
                    "section": str(item.get("section", "Experience/Projects")),
                    "before": before.strip(),
                    "after": after.strip(),
                    "improvement_type": str(item.get("improvement_type", "impact_quantification")),
                }
            )
            if len(valid) >= limit:
                break

        return valid or None

    def enhance_ats_analysis(
        self,
        resume_text: str,
        target_role: str,
        role_skills: List[str],
        base_ats: dict,
    ) -> dict | None:
        if not self.enabled:
            return None

        prompt = (
            "You are an ATS analysis quality enhancer.\n"
            "Refine ATS results but stay realistic and conservative.\n"
            f"Target role: {target_role}\n"
            f"Role skills: {role_skills}\n"
            f"Base ATS result: {base_ats}\n"
            f"Resume text (first 7000 chars): {resume_text[:7000]}\n"
            "Return strict JSON only: "
            "{\"ats_score\": number, \"status\": \"ATS Safe\"|\"Needs Optimization\"|\"High Rejection Risk\", \"issues\": [string,...]}\n"
            "Rules: score must be 0-100, issues max 6, concise and actionable."
        )

        result = self._call_json(prompt)
        if not isinstance(result, dict):
            return None

        raw_score = result.get("ats_score")
        raw_status = result.get("status")
        raw_issues = result.get("issues")

        try:
            score = float(raw_score)
        except Exception:
            return None

        score = max(0.0, min(100.0, round(score, 2)))

        allowed_status = {"ATS Safe", "Needs Optimization", "High Rejection Risk"}
        status = raw_status if isinstance(raw_status, str) and raw_status in allowed_status else base_ats.get("status")
        if status not in allowed_status:
            if score >= 85:
                status = "ATS Safe"
            elif score >= 70:
                status = "Needs Optimization"
            else:
                status = "High Rejection Risk"

        issues: List[str] = []
        if isinstance(raw_issues, list):
            for item in raw_issues:
                if isinstance(item, str):
                    clean = item.strip()
                    if clean and clean not in issues:
                        issues.append(clean)
                if len(issues) >= 6:
                    break

        if not issues:
            base_issues = base_ats.get("issues", [])
            if isinstance(base_issues, list):
                issues = [str(item).strip() for item in base_issues if str(item).strip()][:6]

        return {
            "ats_score": score,
            "status": status,
            "issues": issues,
        }
