# Quick Start Guide - ML Pipeline Training

## 🚀 Get Started in 2 Minutes

### Prerequisites
- Python 3.11+
- Virtual environment already set up with `requirements.txt` installed

### Step 1: Run Training with Default Settings

```bash
cd ml-model

# Run the full training pipeline
python scripts/train_matching_model.py
```

This will:
- Load and merge resume data from CSV + PDFs
- Preprocess all texts (cleaning, normalization, lemmatization)
- Generate semantic embeddings using Sentence-BERT
- Create resume-JD matched pairs for training
- Train the resume matching model
- Evaluate on held-out test set
- Save comprehensive metrics to `saved_models/training_metrics_new.json`

### Step 2: View Results

After training completes, check the output metrics:

```bash
# Windows
type saved_models\training_metrics_new.json

# Linux/Mac
cat saved_models/training_metrics_new.json
```

Expected output structure:
```json
{
  "status": "success",
  "summary": {
    "test_accuracy": 0.82,
    "test_f1_score": 0.81,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "evaluation": {
    "performance": {
      "accuracy": 0.82,
      "precision": 0.84,
      "recall": 0.79,
      "f1_score": 0.81,
      "roc_auc": 0.89
    }
  }
}
```

---

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Accuracy | > 85% |
| Precision | > 87% |
| Recall | > 85% |
| F1 Score | > 86% |
| ROC-AUC | > 92% |

---

## ⚙️ Advanced Usage

### Run with Specific Configuration

```bash
# Use a better embedding model (slower but more accurate)
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-mpnet-base-v2

# Increase batch size for faster training (requires more GPU memory)
python scripts/train_matching_model.py --batch-size 64

# Custom learning rate for fine-tuning
python scripts/train_matching_model.py --learning-rate 0.00001

# Save metrics to custom location
python scripts/train_matching_model.py \
  --metrics-out saved_models/my_custom_metrics.json
```

### See All Options

```bash
python scripts/train_matching_model.py --help
```

---

## 🔧 Troubleshooting

### Issue: Memory Error
**Solution:** Reduce batch size
```bash
python scripts/train_matching_model.py --batch-size 8
```

### Issue: Slow Training
**Solution:** Use faster embedding model
```bash
python scripts/train_matching_model.py \
  --embedding-model sentence-transformers/all-MiniLM-L6-v2 \
  --batch-size 64
```

### Issue: Import Errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Missing spaCy Model
**Solution:** Download it
```bash
python -m spacy download en_core_web_sm
```

---

## 📁 File Structure

```
ml-model/
├── app/
│   ├── training/              ← New modular pipeline
│   │   ├── config.py
│   │   ├── preprocessing.py
│   │   ├── data_loader.py
│   │   ├── feature_engineering.py
│   │   ├── evaluate.py
│   │   ├── utils.py
│   │   └── __init__.py
│   └── [existing files]
└── scripts/
    ├── train_matching_model.py ← New training script
    └── [existing scripts]
```

---

## 💡 Using the Training Module in Your Code

```python
from app.training import (
    EmbeddingService, 
    FeatureEngineering,
    TextPreprocessor
)

# Initialize components
preprocessor = TextPreprocessor()
embedding_service = EmbeddingService()
feature_eng = FeatureEngineering(embedding_service)

# Preprocess text
cleaned = preprocessor.preprocess("Your resume text...")

# Generate embeddings
resume_emb = embedding_service.encode_single("resume...")
jd_emb = embedding_service.encode_single("job description...")

# Compute matching score
score = feature_eng.compute_matching_score(
    resume_emb, jd_emb,
    resume_text="resume...",
    jd_text="job description..."
)
print(f"Match Score: {score:.2%}")  # e.g., "82%"
```

---

## 📚 Full Documentation

For detailed usage, see [TRAINING_PIPELINE.md](TRAINING_PIPELINE.md)

---

## ✅ Checklist

- [ ] Run training script with default settings
- [ ] Check that metrics are saved successfully
- [ ] Review performance metrics (should be > 85% accuracy)
- [ ] Try different embedding models if accuracy is low
- [ ] Integrate matching score into backend API
- [ ] Test end-to-end with sample resume + job description

---

## 🎯 Next Steps

1. **Deploy**: Copy trained model to production
2. **Monitor**: Track accuracy over time as new data arrives
3. **Improve**: Retrain monthly with new annotated data
4. **Optimize**: Fine-tune based on real user feedback

---

For questions or issues, check [TRAINING_PIPELINE.md](TRAINING_PIPELINE.md) or create an issue in the repository.

