from __future__ import annotations

from app.pipelines.analyze_pipeline import AnalyzePipeline


BASE_RESUME_SECTIONS = {
    "EXPERIENCE": [
        "Marketing Intern at ABC Org (2024) - Led public opinion research campaigns.",
        "Coordinated outreach strategy with cross-functional teams.",
    ],
    "PROJECTS": [
        "Signalist: Built a real-time stock tracker web app using React and FastAPI.",
        "Astrophysics Club Portal: Developed SPIT club website with registrations and updates.",
    ],
    "CERTIFICATIONS": [
        "AWS Certified Cloud Practitioner",
        "Google Data Analytics Professional Certificate",
    ],
    "AWARDS": [
        "Winner, Smart India Hackathon 2025",
        "Finalist, National Innovation Challenge 2024",
        "Achieved Pupil rank on Codeforces (Maximum rating of 1232)",
        "Qualified for the penultimate round at Mumbai Hacks out of 20000+ innovators",
        "Solved 500+ problems on competitive programming platforms like Leetcode and Codeforces",
    ],
    "EDUCATION": [
        "SPIT CGPA 8.37",
    ],
}


def build_resume(order: list[str]) -> str:
    lines: list[str] = []
    for header in order:
        lines.append(header)
        lines.extend(BASE_RESUME_SECTIONS[header])
    return "\n".join(lines)


def assert_non_contamination(pipeline: AnalyzePipeline, resume_text: str) -> None:
    normalized = pipeline._normalize_resume_text(resume_text)
    sections = pipeline._extract_resume_sections(normalized)

    certs = pipeline._extract_certifications_from_section(sections["certifications"])
    awards = pipeline._extract_awards(sections["awards"])
    projects = pipeline._extract_top_projects(sections["projects"], limit=3)
    experiences = pipeline._extract_best_experiences(sections["experience"])

    cert_blob = " ".join(certs).lower()
    award_blob = " ".join(awards).lower()

    assert "signalist" not in cert_blob, "Project leaked into certifications"
    assert "marketing intern" not in cert_blob, "Experience leaked into certifications"
    assert "signalist" not in award_blob, "Project leaked into awards"
    assert "marketing intern" not in award_blob, "Experience leaked into awards"

    assert any("aws" in item.lower() for item in certs), "Expected certification missing"
    assert any("winner" in item.lower() for item in awards), "Expected award missing"
    assert any("signalist" in item.lower() for item in projects), "Expected project missing"
    assert any("marketing intern" in item.lower() for item in experiences), "Expected experience missing"


def main() -> None:
    pipeline = AnalyzePipeline()

    test_orders = [
        ["EXPERIENCE", "PROJECTS", "CERTIFICATIONS", "AWARDS", "EDUCATION"],
        ["CERTIFICATIONS", "PROJECTS", "EXPERIENCE", "AWARDS", "EDUCATION"],
        ["AWARDS", "CERTIFICATIONS", "EXPERIENCE", "PROJECTS", "EDUCATION"],
        ["PROJECTS", "EXPERIENCE", "AWARDS", "CERTIFICATIONS", "EDUCATION"],
    ]

    combined_header_resume = "\n".join(
        [
            "AWARDS & CERTIFICATIONS",
            *BASE_RESUME_SECTIONS["AWARDS"],
            *BASE_RESUME_SECTIONS["CERTIFICATIONS"],
            "PROJECTS",
            *BASE_RESUME_SECTIONS["PROJECTS"],
            "EXPERIENCE",
            *BASE_RESUME_SECTIONS["EXPERIENCE"],
            "EDUCATION",
            *BASE_RESUME_SECTIONS["EDUCATION"],
        ]
    )

    for index, order in enumerate(test_orders, start=1):
        text = build_resume(order)
        assert_non_contamination(pipeline, text)
        print(f"[PASS] permutation_{index}: {' > '.join(order)}")

    assert_non_contamination(pipeline, combined_header_resume)
    print("[PASS] combined awards+certifications header")

    achievements_header_resume = "\n".join(
        [
            "CERTIFICATIONS & ACHIEVEMENTS",
            *BASE_RESUME_SECTIONS["AWARDS"],
            *BASE_RESUME_SECTIONS["CERTIFICATIONS"],
            "PROJECTS",
            *BASE_RESUME_SECTIONS["PROJECTS"],
            "EXPERIENCE",
            *BASE_RESUME_SECTIONS["EXPERIENCE"],
        ]
    )
    assert_non_contamination(pipeline, achievements_header_resume)
    print("[PASS] combined certifications+achievements header")
    print("Section regression checks passed.")


if __name__ == "__main__":
    main()
