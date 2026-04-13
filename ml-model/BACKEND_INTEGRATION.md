# Backend Integration Guide - ML Training Module

## Overview

This guide shows how to integrate the new production ML training module with your Express.js backend API.

---

## 🎯 Integration Points

Your backend can use the ML training module in two ways:

### 1. **Direct Integration** (Recommended for Start)
- Call ML Service endpoints directly
- Use computed embeddings in backend

### 2. **Embedded Python** (Advanced)
- Import Python modules from backend
- Requires Python subprocess calls

We recommend **Direct Integration** using HTTP calls to the ML Service.

---

## Option 1: Direct Integration (Recommended)

### Architecture

```
Frontend
   ↓
Express Backend (Port 8080)
   ↓
ML Service (Port 8000)  ← Using new training modules
```

### Backend Endpoint Example

File: `backend/src/services/ml-service.ts`

```typescript
import axios from 'axios';

interface MatchConfig {
  resume_text: string;
  jd_text: string;
  similarity_weight?: number;
  skill_weight?: number;
}

interface MatchResult {
  match_score: number;
  semantic_similarity: number;
  skill_overlap: number;
  confidence: number;
}

class MLService {
  private mlServiceUrl: string;

  constructor() {
    this.mlServiceUrl = process.env.ML_SERVICE_URL || 'http://localhost:8000';
  }

  /**
   * Match resume to job description using trained model
   */
  async matchResumeToJD(
    resume_text: string,
    jd_text: string
  ): Promise<MatchResult> {
    try {
      // Call new ML endpoint (to be created)
      const response = await axios.post(
        `${this.mlServiceUrl}/match`,
        {
          resume_text,
          jd_text,
          similarity_weight: 0.7,
          skill_weight: 0.3,
        },
        { timeout: 30000 }
      );

      return {
        match_score: response.data.match_score,
        semantic_similarity: response.data.semantic_similarity,
        skill_overlap: response.data.skill_overlap,
        confidence: response.data.confidence || 0.85,
      };
    } catch (error) {
      console.error('ML Service error:', error);
      throw new Error('Failed to compute matching score');
    }
  }

  /**
   * Extract skills from text
   */
  async extractSkills(text: string): Promise<Record<string, string[]>> {
    try {
      const response = await axios.post(
        `${this.mlServiceUrl}/extract-skills`,
        { text },
        { timeout: 10000 }
      );

      return response.data.skills;
    } catch (error) {
      console.error('Skill extraction error:', error);
      return {};
    }
  }

  /**
   * Generate embeddings for batch texts
   */
  async encodeTexts(texts: string[]): Promise<number[][]> {
    try {
      const response = await axios.post(
        `${this.mlServiceUrl}/encode`,
        { texts },
        { timeout: 30000 }
      );

      return response.data.embeddings;
    } catch (error) {
      console.error('Encoding error:', error);
      throw error;
    }
  }
}

export default new MLService();
```

### Use in Controller

File: `backend/src/controllers/resume.controller.ts`

```typescript
import MLService from '../services/ml-service';

// ... existing code ...

export async function analyzeResume(
  req: Request,
  res: Response
): Promise<void> {
  try {
    const { resumeText, jobDescription, targetRole } = req.body;

    // 1. Use existing analysis
    const analysis = await performExistingAnalysis(resumeText, targetRole);

    // 2. NEW: Compute ML-based matching score
    if (jobDescription) {
      const matchResult = await MLService.matchResumeToJD(
        resumeText,
        jobDescription
      );

      analysis.mlMatchScore = {
        overall: matchResult.match_score,
        semanticSimilarity: matchResult.semantic_similarity,
        skillOverlap: matchResult.skill_overlap,
        confidence: matchResult.confidence,
      };
    }

    // 3. NEW: Extract skills using ML
    const extractedSkills = await MLService.extractSkills(resumeText);
    analysis.mlExtractedSkills = extractedSkills;

    res.json({
      status: 'success',
      data: analysis,
    });
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ status: 'error', message: error.message });
  }
}
```

---

## Adding New ML Endpoints to FastAPI

File: `ml-model/app/main.py`

Add these new endpoints:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import training modules
from app.training import (
    EmbeddingService,
    FeatureEngineering,
    TextPreprocessor,
)

app = FastAPI()

# Initialize services at startup
embedding_service = None
feature_engineering = None
preprocessor = None

@app.on_event("startup")
async def startup_event():
    global embedding_service, feature_engineering, preprocessor
    embedding_service = EmbeddingService()
    feature_engineering = FeatureEngineering(embedding_service)
    preprocessor = TextPreprocessor(use_lemmatization=True)
    print("✓ ML services initialized")

# ============= NEW ENDPOINTS =============

class MatchRequest(BaseModel):
    resume_text: str
    jd_text: str
    similarity_weight: float = 0.7
    skill_weight: float = 0.3

@app.post("/match")
async def match_resume_to_jd(request: MatchRequest):
    """Match resume to job description using trained embeddings"""
    try:
        # Preprocess texts
        resume_clean = preprocessor.preprocess(request.resume_text)
        jd_clean = preprocessor.preprocess(request.jd_text)
        
        # Generate embeddings
        resume_emb = embedding_service.encode_single(resume_clean)
        jd_emb = embedding_service.encode_single(jd_clean)
        
        # Compute matching score
        match_score = feature_engineering.compute_matching_score(
            resume_embedding=resume_emb,
            jd_embedding=jd_emb,
            resume_text=request.resume_text,
            jd_text=request.jd_text,
            similarity_weight=request.similarity_weight,
            skill_weight=request.skill_weight,
        )
        
        # Compute individual components
        semantic_sim = embedding_service.compute_similarity(resume_emb, jd_emb)
        semantic_sim = (semantic_sim + 1) / 2  # Normalize to [0, 1]
        
        skill_overlap = feature_engineering.compute_skill_overlap(
            request.resume_text,
            request.jd_text
        )
        
        return {
            "match_score": float(match_score),
            "semantic_similarity": float(semantic_sim),
            "skill_overlap": float(skill_overlap),
            "confidence": 0.85,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SkillExtractionRequest(BaseModel):
    text: str

@app.post("/extract-skills")
async def extract_skills(request: SkillExtractionRequest):
    """Extract technical skills from text"""
    try:
        skills = feature_engineering.extract_skill_features(request.text)
        return {"skills": skills}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EncodingRequest(BaseModel):
    texts: list

@app.post("/encode")
async def encode_texts(request: EncodingRequest):
    """Generate embeddings for texts"""
    try:
        embeddings = embedding_service.encode(
            request.texts,
            batch_size=32,
            show_progress_bar=False
        )
        return {
            "embeddings": embeddings.tolist(),
            "dimension": len(embeddings[0]) if embeddings.shape[0] > 0 else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Database for caching embeddings (optional)
_embedding_cache = {}

@app.post("/encode-cached")
async def encode_texts_cached(request: EncodingRequest):
    """Encode texts with caching to avoid redundant computation"""
    import hashlib
    
    embeddings = []
    for text in request.texts:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash not in _embedding_cache:
            emb = embedding_service.encode_single(text)
            _embedding_cache[text_hash] = emb.tolist()
        
        embeddings.append(_embedding_cache[text_hash])
    
    return {
        "embeddings": embeddings,
        "cached": len(_embedding_cache),
    }
```

---

## Environment Configuration

Update `ml-model/.env`:

```dotenv
# Existing config
USE_RESUME_CLASSIFIER=true
PYTHONUNBUFFERED=1

# New ML service config
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32
EMBEDDING_DEVICE=cpu
SKILL_EXTRACTION_ENABLED=true
```

---

## Backend Environment Variables

File: `backend/.env`

```dotenv
# Existing config
ML_SERVICE_URL=http://localhost:8000

# New ML features
ML_MATCHING_ENABLED=true
ML_SKILL_EXTRACTION_ENABLED=true
ML_SIMILARITY_WEIGHT=0.7
ML_SKILL_WEIGHT=0.3
ML_CACHE_EMBEDDINGS=true
```

---

## Using in Backend Routes

File: `backend/src/routes/resume.routes.ts`

```typescript
import express from 'express';
import { Router } from 'express';
import MLService from '../services/ml-service';

const router = Router();

/**
 * POST /api/resume/match
 * Match resume to job description
 */
router.post('/match', async (req, res) => {
  try {
    const { resume_text, jd_text } = req.body;

    if (!resume_text || !jd_text) {
      return res.status(400).json({
        status: 'error',
        message: 'resume_text and jd_text are required',
      });
    }

    const result = await MLService.matchResumeToJD(resume_text, jd_text);

    res.json({
      status: 'success',
      data: result,
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: error.message,
    });
  }
});

/**
 * POST /api/resume/extract-skills
 * Extract skills from text
 */
router.post('/extract-skills', async (req, res) => {
  try {
    const { text } = req.body;

    if (!text) {
      return res.status(400).json({
        status: 'error',
        message: 'text is required',
      });
    }

    const skills = await MLService.extractSkills(text);

    res.json({
      status: 'success',
      data: { skills },
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: error.message,
    });
  }
});

export default router;
```

---

## Testing the Integration

### Test Script

Create `backend/test-ml-integration.ts`:

```typescript
import axios from 'axios';

const ML_SERVICE_URL = 'http://localhost:8000';

async function testMLIntegration() {
  console.log('Testing ML Service Integration...\\n');

  const resumeText = `
    Senior Python developer with 8 years experience.
    Skills: Python, Django, FastAPI, PostgreSQL, AWS, Docker, Kubernetes.
    Experience with microservices and cloud architecture.
  `;

  const jdText = `
    Backend Engineer Position
    Requirements:
    - 5+ years Python development
    - Django or FastAPI experience
    - AWS cloud platform
    - Database design (PostgreSQL)
    Preferred: Docker, Kubernetes, Microservices
  `;

  try {
    // Test 1: Match endpoint
    console.log('Test 1: Resume-JD Matching');
    const matchResponse = await axios.post(
      `${ML_SERVICE_URL}/match`,
      {
        resume_text: resumeText,
        jd_text: jdText,
        similarity_weight: 0.7,
        skill_weight: 0.3,
      }
    );
    console.log('✓ Match Score:', matchResponse.data.match_score);
    console.log('✓ Similarity:', matchResponse.data.semantic_similarity);
    console.log('✓ Skill Overlap:', matchResponse.data.skill_overlap);

    // Test 2: Skill extraction
    console.log('\\nTest 2: Skill Extraction');
    const skillResponse = await axios.post(
      `${ML_SERVICE_URL}/extract-skills`,
      { text: resumeText }
    );
    console.log('✓ Extracted Skills:', skillResponse.data.skills);

    // Test 3: Encoding
    console.log('\\nTest 3: Text Encoding');
    const texts = ['Python developer', 'JavaScript expert', 'Data scientist'];
    const encodeResponse = await axios.post(
      `${ML_SERVICE_URL}/encode`,
      { texts }
    );
    console.log(
      `✓ Generated ${encodeResponse.data.embeddings.length} embeddings`
    );
    console.log(`✓ Embedding dimension: ${encodeResponse.data.dimension}`);

    console.log('\\n✅ All tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testMLIntegration();
```

Run:
```bash
npx ts-node test-ml-integration.ts
```

---

## Performance Optimization

### 1. Caching Embeddings

```typescript
// Cache computed embeddings to avoid redundant computation
const embeddingCache = new Map<string, number[]>();

async function getOrComputeEmbedding(text: string): Promise<number[]> {
  const hash = hashText(text);

  if (embeddingCache.has(hash)) {
    return embeddingCache.get(hash)!;
  }

  const response = await axios.post(`${ML_SERVICE_URL}/encode-cached`, { texts: [text] });
  const embedding = response.data.embeddings[0];

  embeddingCache.set(hash, embedding);
  return embedding;
}
```

### 2. Batch Processing

```typescript
// Batch multiple requests
async function batchMatch(
  resumeJDPairs: Array<{ resume: string; jd: string }>
): Promise<Array<{ score: number }>> {
  const results = await Promise.all(
    resumeJDPairs.map((pair) =>
      MLService.matchResumeToJD(pair.resume, pair.jd)
    )
  );

  return results.map((r) => ({ score: r.match_score }));
}
```

### 3. Rate Limiting

```typescript
import rateLimit from 'express-rate-limit';

const mlLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 60, // 60 requests per minute per IP
  message: 'Too many ML requests, please try again later',
});

router.post('/match', mlLimiter, async (req, res) => {
  // ... implementation ...
});
```

---

## Monitoring & Logging

```typescript
// Log ML service calls
async function matchWithLogging(resumeText: string, jdText: string) {
  const startTime = Date.now();

  try {
    const result = await MLService.matchResumeToJD(resumeText, jdText);
    const duration = Date.now() - startTime;

    console.log({
      event: 'ml_match_success',
      duration_ms: duration,
      match_score: result.match_score,
      timestamp: new Date().toISOString(),
    });

    return result;
  } catch (error) {
    const duration = Date.now() - startTime;

    console.error({
      event: 'ml_match_error',
      duration_ms: duration,
      error: error.message,
      timestamp: new Date().toISOString(),
    });

    throw error;
  }
}
```

---

## Deployment Checklist

- [ ] ML training module installed and tested
- [ ] New FastAPI endpoints added
- [ ] Backend TypeScript/JavaScript updated
- [ ] Environment variables configured
- [ ] Tests passing
- [ ] ML service running on production
- [ ] Backend can successfully call ML endpoints
- [ ] Monitoring/logging in place
- [ ] Performance benchmarks met
- [ ] Documentation updated

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure ML service is running on port 8000 |
| Timeout errors | Increase timeout in axios, reduce batch size |
| Memory errors | Reduce batch size, use smaller embedding model |
| Slow responses | Cache embeddings, use streaming for large batches |

---

## What's Next?

1. ✅ Add new ML endpoints to FastAPI
2. ✅ Update backend to call new endpoints
3. ✅ Test integration end-to-end
4. ✅ Monitor performance in production
5. ⏭️ Fine-tune based on real user data
6. ⏭️ Implement retraining pipeline

---

**Ready to integrate? Start with adding the 3 new endpoints to your FastAPI app!**

