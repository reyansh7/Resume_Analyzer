from __future__ import annotations

import argparse
import json
import re
import statistics
import time
from dataclasses import dataclass
from typing import Any
from urllib import request


SYSTEM_PROMPT = (
    "You are an expert technical career coach. "
    "Create concise, practical roadmap steps with actionable milestones. "
    "Use only provided data and do not invent missing skills beyond supplied skill gaps."
)


@dataclass
class RunResult:
    model: str
    run_index: int
    latency_ms: float
    success: bool
    steps_count: int
    quality_score: float
    reason: str


def build_prompt(target_role: str, level: str, strengths: list[str], skill_gaps: list[str], max_steps: int) -> str:
    strengths_text = ", ".join(strengths[:12]) if strengths else "None provided"
    gaps_text = ", ".join(skill_gaps[:10])
    return (
        f"Target role: {target_role}\n"
        f"Experience level: {level}\n"
        f"Current strengths: {strengths_text}\n"
        f"Skill gaps to address: {gaps_text}\n"
        f"Required roadmap steps: up to {max_steps}\n\n"
        "Each step must include:\n"
        "- title: short and specific\n"
        "- description: 3-4 sentences with timeline, deliverable, and success criteria\n\n"
        "Return only strict JSON in this format:\n"
        "{\"roadmap\":[{\"title\":\"...\",\"description\":\"...\"}]}"
    )


def call_ollama(base_url: str, model: str, prompt: str, timeout_s: float) -> str:
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "options": {"temperature": 0.2},
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
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=timeout_s) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    output = parsed.get("response")
    if not isinstance(output, str) or not output.strip():
        raise ValueError("Empty or invalid model response")
    return output


def parse_roadmap(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return None
    return None


def score_roadmap(parsed: dict[str, Any], max_steps: int) -> tuple[bool, int, float, str]:
    steps = parsed.get("roadmap")
    if not isinstance(steps, list):
        return False, 0, 0.0, "missing roadmap array"

    if not steps:
        return False, 0, 0.0, "empty roadmap array"

    quality = 0.0
    valid_steps = 0
    timeline_keywords = {"week", "day", "month", "timeline", "sprint"}
    deliverable_keywords = {"deliverable", "build", "project", "portfolio", "ship"}
    criteria_keywords = {"success", "metric", "measure", "target", "kpi"}

    for item in steps[:max_steps]:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        description = item.get("description")
        if not isinstance(title, str) or not isinstance(description, str):
            continue

        t = title.strip()
        d = description.strip()
        if not t or not d:
            continue

        valid_steps += 1
        step_score = 0.0
        if 8 <= len(t) <= 120:
            step_score += 0.2
        if 70 <= len(d) <= 900:
            step_score += 0.2

        low = d.lower()
        if any(word in low for word in timeline_keywords):
            step_score += 0.2
        if any(word in low for word in deliverable_keywords):
            step_score += 0.2
        if any(word in low for word in criteria_keywords):
            step_score += 0.2

        quality += min(1.0, step_score)

    if valid_steps == 0:
        return False, 0, 0.0, "no valid title/description pairs"

    avg_step_quality = quality / valid_steps
    count_factor = min(1.0, valid_steps / max(1, min(max_steps, 5)))
    total_quality = (0.7 * avg_step_quality) + (0.3 * count_factor)
    return True, valid_steps, round(total_quality * 100.0, 2), "ok"


def benchmark_model(
    base_url: str,
    model: str,
    prompt: str,
    runs: int,
    timeout_s: float,
    max_steps: int,
) -> list[RunResult]:
    output: list[RunResult] = []
    for idx in range(1, runs + 1):
        start = time.perf_counter()
        try:
            raw = call_ollama(base_url=base_url, model=model, prompt=prompt, timeout_s=timeout_s)
            parsed = parse_roadmap(raw)
            if parsed is None:
                elapsed = (time.perf_counter() - start) * 1000
                output.append(
                    RunResult(
                        model=model,
                        run_index=idx,
                        latency_ms=elapsed,
                        success=False,
                        steps_count=0,
                        quality_score=0.0,
                        reason="invalid json",
                    )
                )
                continue

            success, steps_count, quality_score, reason = score_roadmap(parsed, max_steps=max_steps)
            elapsed = (time.perf_counter() - start) * 1000
            output.append(
                RunResult(
                    model=model,
                    run_index=idx,
                    latency_ms=elapsed,
                    success=success,
                    steps_count=steps_count,
                    quality_score=quality_score,
                    reason=reason,
                )
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            output.append(
                RunResult(
                    model=model,
                    run_index=idx,
                    latency_ms=elapsed,
                    success=False,
                    steps_count=0,
                    quality_score=0.0,
                    reason=f"error: {str(exc)[:120]}",
                )
            )
    return output


def print_summary(results: list[RunResult], model: str) -> None:
    subset = [row for row in results if row.model == model]
    latencies = [row.latency_ms for row in subset]
    qualities = [row.quality_score for row in subset if row.success]
    success_rate = (sum(1 for row in subset if row.success) / max(1, len(subset))) * 100.0
    avg_latency = statistics.mean(latencies) if latencies else 0.0
    p95_latency = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0
    avg_quality = statistics.mean(qualities) if qualities else 0.0

    print(f"\nModel: {model}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Avg Latency: {avg_latency:.0f} ms")
    print(f"  P95 Latency: {p95_latency:.0f} ms")
    print(f"  Avg Quality: {avg_quality:.1f}/100")
    print("  Runs:")
    for row in subset:
        print(
            f"    - run={row.run_index} latency={row.latency_ms:.0f}ms "
            f"success={row.success} steps={row.steps_count} quality={row.quality_score:.1f} reason={row.reason}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Ollama models for roadmap generation quality and latency.")
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--models", nargs="+", default=["deepseek-r1:8b", "llama3.1:8b"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--max-steps", type=int, default=5)
    args = parser.parse_args()

    prompt = build_prompt(
        target_role="Software Engineer",
        level="Mid",
        strengths=["Python", "REST APIs", "SQL"],
        skill_gaps=["System Design", "Kubernetes", "CI/CD", "Cloud Architecture", "Distributed Systems"],
        max_steps=args.max_steps,
    )

    all_results: list[RunResult] = []
    print("Starting benchmark...")
    print(f"Models: {', '.join(args.models)}")
    print(f"Runs per model: {args.runs}")
    print(f"Timeout: {args.timeout_seconds}s")

    for model in args.models:
        rows = benchmark_model(
            base_url=args.base_url,
            model=model,
            prompt=prompt,
            runs=max(1, args.runs),
            timeout_s=max(1.0, args.timeout_seconds),
            max_steps=max(1, args.max_steps),
        )
        all_results.extend(rows)

    print("\n=== Summary ===")
    for model in args.models:
        print_summary(all_results, model)

    best = None
    for model in args.models:
        rows = [r for r in all_results if r.model == model]
        if not rows:
            continue
        success = sum(1 for r in rows if r.success) / len(rows)
        avg_quality = statistics.mean([r.quality_score for r in rows if r.success]) if any(r.success for r in rows) else 0.0
        avg_latency = statistics.mean([r.latency_ms for r in rows])
        utility = (success * 100.0) + (0.4 * avg_quality) - (0.02 * avg_latency)
        score = (utility, model)
        if best is None or score[0] > best[0]:
            best = score

    if best is not None:
        print(f"\nRecommended model (balanced quality/latency): {best[1]}")


if __name__ == "__main__":
    main()
