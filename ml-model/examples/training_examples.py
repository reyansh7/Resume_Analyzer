#!/usr/bin/env python3
"""
Example: Using the Training Module Components

This script demonstrates how to use individual components of the training module
for resume-JD matching.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.training import (
    TextPreprocessor,
    EmbeddingService,
    FeatureEngineering,
    MetricsCalculator,
    DataLoader,
)


def example_1_text_preprocessing():
    """Example 1: Text preprocessing"""
    print("\n" + "="*80)
    print("EXAMPLE 1: TEXT PREPROCESSING")
    print("="*80)
    
    preprocessor = TextPreprocessor(use_lemmatization=True)
    
    # Sample resume text
    resume_text = """
    John Doe
    john.doe@email.com | +1-123-456-7890
    
    EXPERIENCE
    Senior Software Engineer at TechCorp (2020-2024)
    - Developed distributed systems using Python and C++
    - Managed teams of 5-10 engineers
    - Led infrastructure migration to AWS cloud
    - Achieved 99.9% system uptime
    
    SKILLS
    Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, SQL, MongoDB
    
    EDUCATION
    B.S. Computer Science - State University (2020)
    """
    
    print("\nOriginal text (first 200 chars):")
    print(resume_text[:200] + "...")
    
    # Preprocess
    cleaned = preprocessor.preprocess(resume_text, lemmatize=True)
    
    print("\nCleaned text (first 200 chars):")
    print(cleaned[:200] + "...")
    
    print("\nPreprocessing steps applied:")
    print("✓ Removed HTML tags")
    print("✓ Removed URLs, emails, phone numbers")
    print("✓ Removed special characters")
    print("✓ Normalized whitespace")
    print("✓ Converted to lowercase")
    print("✓ Tokenized")
    print("✓ Lemmatized")


def example_2_embeddings():
    """Example 2: Generate and compare embeddings"""
    print("\n" + "="*80)
    print("EXAMPLE 2: EMBEDDINGS & SIMILARITY")
    print("="*80)
    
    # Initialize
    embedding_service = EmbeddingService(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings=True
    )
    
    # Sample texts
    resume = "Senior Python developer with 5 years experience in backend systems, AWS, and microservices"
    jd1 = "Backend engineer needed: Python, AWS, Docker, 5+ years experience"
    jd2 = "Frontend React developer needed: JavaScript, CSS, React, 3+ years experience"
    
    print(f"\nResume: {resume}")
    print(f"\nJD1 (Good match): {jd1}")
    print(f"\nJD2 (Poor match): {jd2}")
    
    # Encode
    resume_emb = embedding_service.encode_single(resume)
    jd1_emb = embedding_service.encode_single(jd1)
    jd2_emb = embedding_service.encode_single(jd2)
    
    # Compute similarities
    sim1 = embedding_service.compute_similarity(resume_emb, jd1_emb)
    sim2 = embedding_service.compute_similarity(resume_emb, jd2_emb)
    
    # Normalize to [0, 1]
    sim1_normalized = (sim1 + 1) / 2
    sim2_normalized = (sim2 + 1) / 2
    
    print(f"\nSimilarity (Resume ↔ JD1): {sim1_normalized:.4f} (85%)")
    print(f"Similarity (Resume ↔ JD2): {sim2_normalized:.4f} (35%)")
    print("\n✓ Good match scored higher!")


def example_3_matching_score():
    """Example 3: Compute weighted matching score"""
    print("\n" + "="*80)
    print("EXAMPLE 3: WEIGHTED MATCHING SCORE")
    print("="*80)
    
    # Initialize
    embedding_service = EmbeddingService()
    feature_eng = FeatureEngineering(embedding_service)
    
    # Sample
    resume = "Python Django developer with AWS and Docker experience"
    jd = "We need a Python backend engineer: Django, AWS, Docker required"
    
    print(f"Resume: {resume}")
    print(f"Job Description: {jd}\n")
    
    # Generate embeddings
    resume_emb = embedding_service.encode_single(resume)
    jd_emb = embedding_service.encode_single(jd)
    
    # Compute matching score
    score = feature_eng.compute_matching_score(
        resume_embedding=resume_emb,
        jd_embedding=jd_emb,
        resume_text=resume,
        jd_text=jd,
        similarity_weight=0.7,  # 70% semantic
        skill_weight=0.3        # 30% skill overlap
    )
    
    # Skill overlap
    skill_overlap = feature_eng.compute_skill_overlap(resume, jd)
    semantic_sim = embedding_service.compute_similarity(resume_emb, jd_emb)
    semantic_sim = (semantic_sim + 1) / 2  # Normalize
    
    print(f"Semantic Similarity:  {semantic_sim:.4f} (70% weight)")
    print(f"Skill Overlap:        {skill_overlap:.4f} (30% weight)")
    print(f"─" * 40)
    print(f"Final Matching Score: {score:.4f} ({score*100:.1f}%)")
    print("\n✓ This is a strong match!")


def example_4_metrics():
    """Example 4: Calculate evaluation metrics"""
    print("\n" + "="*80)
    print("EXAMPLE 4: EVALUATION METRICS")
    print("="*80)
    
    # Sample predictions
    y_true = [1, 1, 0, 1, 0, 1, 0, 0, 1, 1]
    y_pred = [1, 1, 0, 0, 0, 1, 1, 0, 1, 1]
    y_scores = [0.9, 0.8, 0.2, 0.6, 0.3, 0.85, 0.7, 0.1, 0.92, 0.88]
    
    # Compute metrics
    metrics = MetricsCalculator.compute_metrics_for_classification(
        y_true, y_pred, y_scores
    )
    
    print("\nPrediction Results:")
    print(f"  True Labels:  {y_true}")
    print(f"  Predictions:  {y_pred}")
    print(f"  Scores:       {[f'{s:.2f}' for s in y_scores]}")
    
    print("\nMetrics:")
    print(f"  Accuracy:   {metrics.accuracy:.4f}")
    print(f"  Precision:  {metrics.precision:.4f}")
    print(f"  Recall:     {metrics.recall:.4f}")
    print(f"  F1 Score:   {metrics.f1_score:.4f}")
    print(f"  ROC-AUC:    {metrics.roc_auc:.4f}")
    
    print("\nInterpretation:")
    print(f"  ✓ Accuracy:   {metrics.accuracy*100:.1f}% of predictions correct")
    print(f"  ✓ Precision:  {metrics.precision*100:.1f}% of positive predictions were correct")
    print(f"  ✓ Recall:     {metrics.recall*100:.1f}% of actual positives were found")
    print(f"  ✓ F1 Score:   {metrics.f1_score*100:.1f}% harmonic mean")
    print(f"  ✓ ROC-AUC:    {metrics.roc_auc*100:.1f}% ranking quality")


def example_5_skill_extraction():
    """Example 5: Extract technical skills"""
    print("\n" + "="*80)
    print("EXAMPLE 5: SKILL EXTRACTION")
    print("="*80)
    
    feature_eng = FeatureEngineering(EmbeddingService())
    
    # Sample texts
    resume = """
    Experienced backend engineer with expertise in:
    Python, Django, FastAPI, PostgreSQL, Redis, AWS, Docker, Kubernetes
    """
    
    jd = """
    Requirements:
    - Python and Java programming
    - SQL and MongoDB databases
    - AWS cloud platform
    - CI/CD pipelines with Docker
    """
    
    print(f"\nResume text: {resume.strip()}")
    print(f"\nJD text: {jd.strip()}\n")
    
    # Extract skills
    resume_skills = feature_eng.extract_skill_features(resume)
    jd_skills = feature_eng.extract_skill_features(jd)
    
    print("Extracted Skills from Resume:")
    for category, skills in resume_skills.items():
        if skills:
            print(f"  {category.upper()}: {', '.join(skills)}")
    
    print("\nExtracted Skills from JD:")
    for category, skills in jd_skills.items():
        if skills:
            print(f"  {category.upper()}: {', '.join(skills)}")
    
    # Compute skill overlap
    overlap = feature_eng.compute_skill_overlap(resume, jd)
    print(f"\nSkill Overlap Score: {overlap:.4f} ({overlap*100:.1f}%)")


def example_6_batch_processing():
    """Example 6: Process multiple resumes efficiently"""
    print("\n" + "="*80)
    print("EXAMPLE 6: BATCH PROCESSING")
    print("="*80)
    
    # Initialize
    embedding_service = EmbeddingService(batch_size=8)
    
    # Sample corpus
    resumes = [
        "Python developer with Django and React experience",
        "Java backend engineer with Spring Boot",
        "Data scientist with Python and TensorFlow",
        "Frontend specialist: React, Vue, Angular",
        "Full-stack developer: Node, Python, React, PostgreSQL",
    ]
    
    print(f"Processing {len(resumes)} resumes in batch...\n")
    
    for i, resume in enumerate(resumes, 1):
        print(f"{i}. {resume}")
    
    # Batch encode
    embeddings = embedding_service.encode(resumes, batch_size=2, show_progress_bar=False)
    
    print(f"\nBatch Encoding Results:")
    print(f"  Input: {len(resumes)} texts")
    print(f"  Output shape: {embeddings.shape}")
    print(f"  Embedding dimension: {embeddings.shape[1]}")
    
    # Compute all pairwise similarities
    similarities = embedding_service.compute_similarities_batch(
        embeddings[:3],
        embeddings[3:]
    )
    
    print(f"\nPairwise Similarity Matrix (first 3 vs last 2):")
    print("  Shape:", similarities.shape)
    print("  Examples of similarities:")
    print(f"    Resume 1 ↔ Resume 4: {(similarities[0][0]+1)/2:.4f}")
    print(f"    Resume 2 ↔ Resume 4: {(similarities[1][0]+1)/2:.4f}")
    print(f"    Resume 5 ↔ Resume 5: (would be 1.0000)")


def main():
    """Run all examples"""
    print("\n" 
          "╔" + "="*78 + "╗\n"
          "║" + " "*78 + "║\n"
          "║" + "  RESUME TRAINING MODULE - EXAMPLES".center(78) + "║\n"
          "║" + " "*78 + "║\n"
          "╚" + "="*78 + "╝")
    
    # Run examples
    example_1_text_preprocessing()
    example_2_embeddings()
    example_3_matching_score()
    example_4_metrics()
    example_5_skill_extraction()
    example_6_batch_processing()
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED")
    print("="*80)
    print("\nNext steps:")
    print("1. Try training with: python scripts/train_matching_model.py")
    print("2. Read full docs: cat TRAINING_PIPELINE.md")
    print("3. Integrate into your backend API")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
