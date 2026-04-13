# Production ML Training Pipeline Documentation

## Overview

This is a **production-grade ML training pipeline** for resume-job description matching using modern NLP techniques. It implements best practices for data handling, preprocessing, feature engineering, and evaluation.

### Key Features

- ✅ **Modular Architecture**: Separate, reusable components for each step
- ✅ **Sentence-Transformers Embeddings**: State-of-the-art semantic embeddings
- ✅ **Comprehensive Data Loading**: CSV + PDF data sources with deduplication
- ✅ **Production Preprocessing**: HTML tag removal, tokenization, lemmatization
- ✅ **Stratified Splitting**: Maintains class distribution (70-15-15 split)
- ✅ **Advanced Metrics**: Accuracy, precision, recall, F1, ROC-AUC, MRR
- ✅ **Weighted Scoring**: Combines semantic similarity + skill matching
- ✅ **Resume-JD Pair Training**: Creates positive/negative training samples

---

## Architecture

### Module Structure

```
app/training/
├── __init__.py              # Package exports
├── config.py               # Configuration classes
├── preprocessing.py        # Text cleaning & preprocessing
├── data_loader.py         # Data loading from multiple sources
├── feature_engineering.py # Embeddings & feature computation
├── evaluate.py            # Metrics calculation
└── utils.py               # Utility functions

scripts/
└── train_matching_model.py # Main training script
```

### Data Flow

```
Raw Data (CSV, PDF)
    ↓
DataLoader: Load & Deduplicate
    ↓
TextPreprocessor: Clean & Normalize
    ↓
EmbeddingService: Generate Embeddings
    ↓
FeatureEngineering: Create Training Pairs
    ↓
Model Training & Evaluation
    ↓
Metrics & Results
```

---

## Quick Start

### 1. Run Training with Default Settings

```bash
cd ml-model/
python scripts/train_matching_model.py
```

### 2. Custom Configuration

```bash
# High-quality model training
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-mpnet-base-v2 \
  --batch-size 32 \
  --learning-rate 0.0001 \
  --epochs 10

# Save metrics to custom location
python scripts/train_matching_model.py \
  --metrics-out saved_models/my_model_metrics.json
```

### 3. Configuration Options

```bash
# Data options
--csv                Path to Resume CSV (default: Resume/Resume.csv)
--pdf-root           Root directory for PDF resumes (default: data)
--min-text-length    Minimum resume length (default: 100)

# Embedding options
--embedding-model    HuggingFace model (default: all-MiniLM-L6-v2)

# Model options
--model-type        'similarity' or 'classifier' (default: similarity)
--loss-fn          'cosine', 'mse', or 'triplet' (default: cosine)
--learning-rate    Learning rate (default: 0.0001)
--batch-size       Batch size (default: 32)
--epochs           Number of epochs (default: 10)

# Other options
--random-seed      Random seed (default: 42)
--metrics-out      Output metrics file
```

---

## Module Usage Examples

### 1. Text Preprocessing

```python
from app.training import TextPreprocessor

# Initialize preprocessor
preprocessor = TextPreprocessor(use_lemmatization=True)

# Preprocess single text
cleaned = preprocessor.preprocess(
    text="Your resume text here...",
    lemmatize=True,
    remove_duplicates=True
)

# Or use convenience function
from app.training import preprocess_text

cleaned = preprocess_text(
    text="Your text",
    min_length=100,
    max_length=10000,
    use_lemmatization=False
)
```

### 2. Data Loading

```python
from app.training import DataLoader
from pathlib import Path

loader = DataLoader(project_root=Path("."))

# Load from all sources
records = loader.load_all_resumes(
    include_csv=True,
    include_pdf=True,
    csv_path=Path("Resume/Resume.csv"),
    pdf_root=Path("data")
)

# Get category distribution
distribution = loader.get_category_distribution(records)
print(distribution)

# Deduplicate
unique_records, stats = loader.deduplicate_records(records)

# Filter by length
filtered_records, stats = loader.filter_by_length(
    records,
    min_length=100,
    max_length=10000
)
```

### 3. Embeddings & Similarity

```python
from app.training import EmbeddingService
import numpy as np

# Initialize service
embedding_service = EmbeddingService(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    device="cpu",
    normalize_embeddings=True
)

# Encode texts
texts = ["Resume text 1", "Resume text 2"]
embeddings = embedding_service.encode(texts, batch_size=32)

# Compute similarity between two embeddings
sim = embedding_service.compute_similarity(embeddings[0], embeddings[1])
print(f"Similarity: {sim:.4f}")  # Range: [0, 1]

# Compute pairwise similarities
similarities = embedding_service.compute_similarities_batch(
    embeddings[:10], 
    embeddings[10:20]
)
print(f"Shape: {similarities.shape}")  # (10, 10)
```

### 4. Feature Engineering

```python
from app.training import FeatureEngineering, EmbeddingService

# Initialize
embedding_service = EmbeddingService()
feature_eng = FeatureEngineering(embedding_service)

# Compute weighted matching score
resume_emb = embedding_service.encode_single("resume text...")
jd_emb = embedding_service.encode_single("job description...")

score = feature_eng.compute_matching_score(
    resume_embedding=resume_emb,
    jd_embedding=jd_emb,
    resume_text="resume text...",
    jd_text="job description...",
    similarity_weight=0.7,
    skill_weight=0.3
)
print(f"Match Score: {score:.4f}")  # Range: [0, 1]

# Extract skills
skills = feature_eng.extract_skill_features("Your text with Python and Java skills")
print(skills)
```

### 5. Metrics & Evaluation

```python
from app.training import MetricsCalculator, EvaluationMetrics

# Compute classification metrics
y_true = [0, 1, 1, 0, 1]
y_pred = [0, 1, 0, 0, 1]
y_scores = [0.2, 0.8, 0.4, 0.1, 0.9]

metrics = MetricsCalculator.compute_metrics_for_classification(
    y_true, y_pred, y_scores
)

print(f"Accuracy: {metrics.accuracy:.4f}")
print(f"Precision: {metrics.precision:.4f}")
print(f"Recall: {metrics.recall:.4f}")
print(f"F1 Score: {metrics.f1_score:.4f}")
print(f"ROC-AUC: {metrics.roc_auc:.4f}")

# Compute ranking metrics
similarities = [0.9, 0.7, 0.3, 0.8]
labels = [1, 1, 0, 1]

metrics = MetricsCalculator.compute_metrics_for_ranking(
    similarities, labels
)
print(f"MRR: {metrics.mean_reciprocal_rank:.4f}")
```

### 6. Data Splitting

```python
from app.training import stratified_split, split_data

data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
labels = ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B']

# Stratified split (maintains label distribution)
train, val, test = stratified_split(
    data, labels,
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
    random_state=42
)

print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
```

---

## Training Pipeline Steps

### Step 1: Load Data ✅
- Load from CSV (Resume.csv)
- Load from PDF folders (organized by category)
- Handle missing values safely
- Remove duplicates

### Step 2: Preprocess ✅
- Remove HTML tags
- Remove URLs, emails, phone numbers
- Remove special characters
- Normalize whitespace
- Convert to lowercase
- Tokenization
- Lemmatization (spaCy)

### Step 3: Generate Embeddings ✅
- Use Sentence-BERT (all-MiniLM-L6-v2)
- Batch processing for efficiency
- Normalize to unit vectors

### Step 4: Create Training Pairs ✅
- **Positive pairs**: Same category resumes
- **Negative pairs**: Different category pairs
- Balance positive/negative ratio

### Step 5: Train ✅
- Implement similarity-based matching
- Weighted combination of:
  - Semantic similarity (70%)
  - Skill overlap (30%)

### Step 6: Evaluate ✅
- Compute matching accuracy
- Evaluate on held-out test set
- Report metrics

---

## Output Files

### Training Metrics

```
saved_models/training_metrics_new.json
```

Example output:
```json
{
  "status": "success",
  "timestamp": "2024-04-13T10:30:00",
  "duration_seconds": 125.4,
  "summary": {
    "train_samples": 1740,
    "val_samples": 372,
    "test_samples": 372,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "test_accuracy": 0.8234,
    "test_f1_score": 0.8145
  },
  "evaluation": {
    "performance": {
      "accuracy": 0.8234,
      "precision": 0.8456,
      "recall": 0.7891,
      "f1_score": 0.8145,
      "roc_auc": 0.8934
    }
  }
}
```

---

## Performance Benchmarks

### Expected Results (with your data)

| Metric | Baseline | Target |
|--------|----------|--------|
| Accuracy | ~82% | >85% |
| Precision | ~84% | >87% |
| Recall | ~79% | >85% |
| F1 Score | ~81% | >86% |
| ROC-AUC | ~89% | >92% |

*Actual results depend on data quality and volume*

---

## Integration with Backend

### FastAPI Integration

```python
from app.training import EmbeddingService, FeatureEngineering
from pathlib import Path

# Initialize once on startup
embedding_service = EmbeddingService(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
feature_eng = FeatureEngineering(embedding_service)

@app.post("/analyze/match")
def match_resume_to_jd(resume_text: str, jd_text: str):
    """Match resume to job description"""
    
    # Generate embeddings
    resume_emb = embedding_service.encode_single(resume_text)
    jd_emb = embedding_service.encode_single(jd_text)
    
    # Compute matching score
    score = feature_eng.compute_matching_score(
        resume_embedding=resume_emb,
        jd_embedding=jd_emb,
        resume_text=resume_text,
        jd_text=jd_text,
        similarity_weight=0.7,
        skill_weight=0.3
    )
    
    return {
        "match_score": score,
        "semantic_similarity": float(embedding_service.compute_similarity(resume_emb, jd_emb)),
        "status": "success"
    }
```

---

## Advanced Configuration

### Using Different Embedding Models

```bash
# Larger, more powerful model
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-mpnet-base-v2

# Multilingual support
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/multilingual-MiniLM-L6-v2

# Domain-specific (if available)
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-distilroberta-v1
```

### Hyperparameter Tuning

```bash
# For faster training (small dataset)
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-MiniLM-L6-v2 \
  --batch-size 16 \
  --learning-rate 0.001

# For production model (large dataset)
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-mpnet-base-v2 \
  --batch-size 64 \
  --learning-rate 0.00001 \
  --epochs 20
```

---

## Troubleshooting

### Issue: Out of Memory
**Solution**: Reduce batch size
```bash
python scripts/train_matching_model.py --batch-size 8
```

### Issue: Slow Embedding Generation
**Solution**: Use smaller embedding model
```bash
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-MiniLM-L6-v2
```

### Issue: Low Accuracy
**Solution**: 
1. Increase data volume
2. Use better embedding model
3. Adjust similarity weights:
```python
score = feature_eng.compute_matching_score(
    ...,
    similarity_weight=0.8,  # Increase
    skill_weight=0.2        # Decrease
)
```

### Issue: Missing spaCy Model
**Solution**: Download spaCy model
```bash
python -m spacy download en_core_web_sm
```

---

## Future Enhancements

### Phase 2: Fine-tuning
- [ ] Fine-tune BERT on resume-JD pairs
- [ ] Use HuggingFace Trainer API
- [ ] Implement contrastive learning

### Phase 3: Advanced Features
- [ ] Named Entity Recognition for skill extraction
- [ ] Experience level matching
- [ ] Industry/domain-specific scoring

### Phase 4: Production Optimization
- [ ] Model quantization for inference speed
- [ ] Caching for common resumes
- [ ] A/B testing framework
- [ ] Real-time model updates

---

## References

- [Sentence-Transformers](https://www.sbert.net/)
- [spaCy](https://spacy.io/)
- [scikit-learn](https://scikit-learn.org/)
- [MLOps Best Practices](https://ml-ops.systems/)

---

## Author Notes

This pipeline is designed for:
- ✓ Production deployment
- ✓ Easy maintenance and updates
- ✓ Scalability (large datasets)
- ✓ Integration with existing systems

All components are modular and can be used independently or as part of the full pipeline.

