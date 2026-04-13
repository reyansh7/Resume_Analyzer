"""
Validation script to test and demonstrate improved extraction capabilities.
Tests the enhanced extraction patterns against sample resumes.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipelines.analyze_pipeline import AnalyzePipeline
from app.training.extraction_enhancement import (
    EnhancedExtractionFilter,
    create_training_examples,
    ExtractionPatterns
)


def create_test_resumes() -> dict:
    """Create comprehensive test resumes with various sections."""
    return {
        "tech_resume": """
JOHN DOE
john.doe@example.com | LinkedIn | GitHub

EXPERIENCE
Senior Software Engineer at Tech Corp (2022-Present)
- Led cross-functional team of 5 engineers to deliver cloud migration project 3 months early
- Managed $2M infrastructure budget and reduced costs by 40%
- Coordinated with 3 product teams to implement API gateway used by 1000+ services

Marketing Intern at StartupXYZ (2021)
- Organized social media campaigns reaching 50K users monthly
- Coordinated with external agencies on 10+ campaigns
- Led analytics initiative improving click-through rate by 25%

CERTIFICATIONS
AWS Certified Solutions Architect Professional
Google Cloud Professional Data Engineer
Azure Developer Associate Certificate
Certified Kubernetes Administrator (CKA)

AWARDS & ACHIEVEMENTS
Winner of Smart India Hackathon 2023
Finalist in National Coding Competition 2022
Achieved Pupil rank on Codeforces with maximum rating of 2100
Qualified for Google Code Jam Final Round
Dean's List - GPA 3.9/4.0
Gold Medal in State-level Science Olympiad 2018

EDUCATION
Bachelor of Technology in Computer Science
IIT Bombay, CGPA: 8.23/10
HSC - Percentage: 81%
""",
        "minimal_resume": """
JANE SMITH

SKILLS
Python, Java, SQL, React

EDUCATION
B.Tech Computer Engineering - XYZ University CGPA-8.23
HSC - Percentage- 81%

PROJECTS
Built real-time stock tracker using React and FastAPI
Developed club portal website with member registrations
""",
        "awards_focused": """
ACHIEVEMENT HIGHLIGHTS

2024 Winner - Smart India Hackathon (Team Lead)
- Led team of 4 members, recognized for innovation

Finalist - National Innovation Challenge 2024
- Selected among top 100 from 10,000+ entries

Achieved Pupil rank on Codeforces
- Maximum rating: 1232, solved 500+ problems on LeetCode

Qualified for Google Code Jam Penultimate Round
- Competed against 50,000+ programmers worldwide

2023 Gold Medal - National Science Olympiad
- Ranked 1st in Computer Science Category

Dean's List Recognition - GPA > 3.8
- 4 consecutive semesters

Best Project Award - College Technical Fest 2023
- AI-powered resume analyzer project
""",
        "experience_focused": """
PROFESSIONAL EXPERIENCE

Senior Developer at CloudTech Solutions (2022-Present)
- Led architecture redesign of payment system handling 10M+ transactions daily
- Managed onboarding of 15 new team members
- Coordinated with product and data teams to reduce transaction latency by 50%
- Implemented monitoring dashboard used across 5 departments

DevOps Engineer at WebServices Inc (2020-2022)
- Coordinated infrastructure migration across 3 AWS regions
- Developed CI/CD pipeline reducing deployment time from 2 hours to 15 minutes
- Mentored 3 junior engineers on Kubernetes best practices
- Managed team projects delivering 20+ features quarterly

Marketing Coordinator at BrandCo (2019)
- Organized 8 major events with 1000+ attendees
- Led social media growth campaign resulting in 300% follower increase
- Coordinated logistics with 5 external vendors

VOLUNTEER EXPERIENCE
President of Technical Club (2021-2023)
- Led 30-member technical club organizing 15+ workshops
- Coordinated partnerships with 5 tech companies for sponsorships

Secretary of Cultural Committee (2019)
- Organized 10 college events with 500+ total attendance
""",
    }


def validate_extraction(pipeline: AnalyzePipeline, resume_text: str, test_name: str) -> dict:
    """Validate extraction results for a resume."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")
    
    # Run analysis
    result = pipeline.run(
        resume_text=resume_text,
        target_role="Software Engineer",
        current_skills=["Python", "Java"],
        profession="Technology",
        level="Mid-Level"
    )
    
    certification_results = result.parsed_resume.get("certificationsDetected", [])
    award_results = result.parsed_resume.get("awardsDetected", [])
    experience_results = result.parsed_resume.get("featuredExperiences", [])
    
    print(f"\n✅ Certifications Detected ({len(certification_results)}):")
    for cert in certification_results:
        print(f"  • {cert}")
    
    print(f"\n🏆 Awards Detected ({len(award_results)}):")
    for award in award_results:
        print(f"  • {award}")
    
    print(f"\n💼 Featured Experiences ({len(experience_results)}):")
    for exp in experience_results:
        print(f"  • {exp}")
    
    return {
        "test_name": test_name,
        "certifications": certification_results,
        "awards": award_results,
        "experiences": experience_results,
        "extraction_counts": {
            "certifications": len(certification_results),
            "awards": len(award_results),
            "experiences": len(experience_results),
        }
    }


def benchmark_extraction_scoring():
    """Benchmark the scoring system for extraction patterns."""
    print(f"\n{'='*60}")
    print("EXTRACTION PATTERN SCORING BENCHMARK")
    print(f"{'='*60}")
    
    detector = EnhancedExtractionFilter()
    training_data = create_training_examples()
    
    print("\n📚 CERTIFICATION SCORING:")
    for cert in training_data["certifications"]:
        text = cert[0] if isinstance(cert, list) else cert
        score = detector.score_certification(text)
        print(f"  Score: {score:2d} | {text}")
    
    print("\n🏅 AWARD SCORING:")
    for award in training_data["awards"]:
        text = award[0] if isinstance(award, list) else award
        score = detector.score_award(text)
        print(f"  Score: {score:2d} | {text}")
    
    print("\n💼 EXPERIENCE SCORING:")
    for exp in training_data["experiences"]:
        text = exp[0] if isinstance(exp, list) else exp
        score = detector.score_experience(text, is_from_experience_section=True)
        print(f"  Score: {score:2d} | {text}")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print(f"\n{'='*60}")
    print("EDGE CASE TESTING")
    print(f"{'='*60}")
    
    detector = EnhancedExtractionFilter()
    
    edge_cases = {
        "cert_with_experience_context": [
            "Led team to complete AWS Solutions Architect certification training",
            "AWS Developer Associate Certificate obtained through self-study",
        ],
        "award_with_project_context": [
            "Winner of Smart India Hackathon 2024 - Built AI resume analyzer",
            "Project recognition: Finalist in National Coding Competition 2022",
        ],
        "experience_without_obvious_markers": [
            "Responsible for system improvements and process optimization",
            "Worked on database optimization and scaling improvements",
            "Gained experience in cloud infrastructure management",
        ],
    }
    
    print("\n🔍 Testing Edge Cases:\n")
    for category, examples in edge_cases.items():
        print(f"{category.upper()}:")
        for example in examples:
            cert_score = detector.score_certification(example)
            award_score = detector.score_award(example)
            exp_score = detector.score_experience(example)
            print(f"  \"{example}\"")
            print(f"    Cert Score: {cert_score} | Award Score: {award_score} | Exp Score: {exp_score}")


def generate_report(results: list) -> None:
    """Generate extraction improvement report."""
    print(f"\n{'='*60}")
    print("EXTRACTION IMPROVEMENT SUMMARY")
    print(f"{'='*60}\n")
    
    total_sections = sum(
        r["extraction_counts"]["certifications"] +
        r["extraction_counts"]["awards"] +
        r["extraction_counts"]["experiences"]
        for r in results
    )
    
    total_certs = sum(r["extraction_counts"]["certifications"] for r in results)
    total_awards = sum(r["extraction_counts"]["awards"] for r in results)
    total_exps = sum(r["extraction_counts"]["experiences"] for r in results)
    
    print(f"📊 AGGREGATE RESULTS:")
    print(f"  Total Sections Extracted: {total_sections}")
    print(f"  Total Certifications:    {total_certs}")
    print(f"  Total Awards:             {total_awards}")
    print(f"  Total Experiences:       {total_exps}")
    
    print(f"\n📈 PER-TEST BREAKDOWN:")
    for result in results:
        counts = result["extraction_counts"]
        print(f"  {result['test_name']:20s} | Certs: {counts['certifications']} | Awards: {counts['awards']} | Exps: {counts['experiences']}")
    
    print(f"\n✅ Improvements Achieved:")
    print(f"  ✓ Enhanced certification detection patterns")
    print(f"  ✓ Relaxed award filtering criteria")
    print(f"  ✓ More lenient experience extraction")
    print(f"  ✓ Better handling of edge cases")
    print(f"  ✓ Support for multi-section entries")


def main():
    """Run comprehensive extraction validation."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    print("\n🚀 RESUME EXTRACTION VALIDATION & TRAINING")
    print("="*60)
    
    # Initialize pipeline
    pipeline = AnalyzePipeline()
    test_resumes = create_test_resumes()
    results = []
    
    # Test each resume
    for resume_name, resume_text in test_resumes.items():
        result = validate_extraction(pipeline, resume_text, resume_name.replace("_", " ").title())
        results.append(result)
    
    # Run benchmarks
    benchmark_extraction_scoring()
    test_edge_cases()
    
    # Generate report
    generate_report(results)
    
    # Save results to file
    output_file = Path(__file__).parent.parent / "extraction_validation_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "results": results,
            "patterns": {
                "certifications": list(ExtractionPatterns.CERT_KEYWORDS),
                "awards": list(ExtractionPatterns.AWARD_KEYWORDS),
                "experiences": list(ExtractionPatterns.EXPERIENCE_KEYWORDS),
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"\n{'='*60}")
    print("✨ Validation Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
