from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class RoadmapTask:
    skill: str
    title: str
    difficulty: str
    estimated_hours: int
    priority_score: float
    suggested_courses: List[str]
    youtube_links: List[str]
    leetcode_problems: List[str]
    details: str


class ProgressiveRoadmapGenerator:
    def _difficulty_for_index(self, idx: int) -> str:
        if idx < 3:
            return "Beginner"
        if idx < 7:
            return "Intermediate"
        return "Advanced"

    def _phase_for_index(self, idx: int) -> str:
        if idx < 4:
            return "30_day_plan"
        if idx < 8:
            return "60_day_plan"
        return "90_day_plan"

    def _make_task(self, skill: str, idx: int, role: str) -> RoadmapTask:
        difficulty = self._difficulty_for_index(idx)
        base_hours = 6 if difficulty == "Beginner" else 9 if difficulty == "Intermediate" else 12
        priority = round(max(0.4, 1.0 - (idx * 0.07)), 2)
        slug = skill.lower().replace(" ", "+")
        is_tech_role = any(token in role.lower() for token in ["engineer", "developer", "devops", "data", "software"])

        return RoadmapTask(
            skill=skill,
            title=f"Master {skill}",
            difficulty=difficulty,
            estimated_hours=base_hours,
            priority_score=priority,
            suggested_courses=[
                f"{skill} Fundamentals",
                f"{skill} Applied Project Workshop",
            ],
            youtube_links=[
                f"https://www.youtube.com/results?search_query={slug}+tutorial",
            ],
            leetcode_problems=(
                [
                    "https://leetcode.com/problemset/",
                ]
                if is_tech_role
                else []
            ),
            details=f"Build one portfolio artifact using {skill} and quantify impact in your resume.",
        )

    def generate(self, missing_skills: List[str], target_role: str) -> dict:
        ordered = [skill for skill in missing_skills if skill.strip()][:12]
        tasks = [self._make_task(skill, idx, target_role) for idx, skill in enumerate(ordered)]

        by_phase = {"30_day_plan": [], "60_day_plan": [], "90_day_plan": []}
        for idx, task in enumerate(tasks):
            by_phase[self._phase_for_index(idx)].append(task)

        return {
            "30_day_plan": [task.__dict__ for task in by_phase["30_day_plan"]],
            "60_day_plan": [task.__dict__ for task in by_phase["60_day_plan"]],
            "90_day_plan": [task.__dict__ for task in by_phase["90_day_plan"]],
        }
