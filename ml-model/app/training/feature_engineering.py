"""
Feature Engineering and Embeddings
Handles sentence embeddings and similarity computation using sentence-transformers
"""
import logging
import numpy as np
from typing import List, Tuple, Dict, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 device: str = "cpu",
                 normalize_embeddings: bool = True):
        """
        Initialize embedding service
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to run model on (cpu or cuda)
            normalize_embeddings: Whether to normalize embeddings to unit vectors
        """
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers")
        
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"Loaded embedding model: {model_name} on device: {device}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise
    
    def encode(self, texts: List[str], 
              batch_size: int = 32,
              convert_to_numpy: bool = True,
              show_progress_bar: bool = False) -> np.ndarray:
        """
        Encode texts to embeddings
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            convert_to_numpy: Return as numpy array
            show_progress_bar: Show progress bar
            
        Returns:
            Embeddings as numpy array of shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=convert_to_numpy,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=self.normalize_embeddings
        )
        
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding as 1D numpy array
        """
        if not text:
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings
        )
        
        return embedding
    
    def compute_similarity(self, embedding1: np.ndarray, 
                          embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1 for normalized embeddings, -1 to 1 for unnormalized)
        """
        if util is None:
            # Fallback: simple cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        
        # Use sentence-transformers utility
        similarity = util.pytorch_cos_sim(embedding1, embedding2)
        return float(similarity[0][0])
    
    def compute_similarities_batch(self, embeddings1: np.ndarray,
                                  embeddings2: np.ndarray) -> np.ndarray:
        """
        Compute pairwise similarities between two sets of embeddings
        
        Args:
            embeddings1: Array of shape (n1, embedding_dim)
            embeddings2: Array of shape (n2, embedding_dim)
            
        Returns:
            Similarity matrix of shape (n1, n2)
        """
        if util is None:
            # Fallback: numpy cosine similarity
            similarity = embeddings1 @ embeddings2.T
            return similarity
        
        # Use sentence-transformers utility
        similarity_matrix = util.pytorch_cos_sim(embeddings1, embeddings2)
        return similarity_matrix.cpu().numpy() if hasattr(similarity_matrix, 'cpu') else np.array(similarity_matrix)
    
    def get_embedding_dimension(self) -> int:
        """Get dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()
    
    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Static method for cosine similarity computation
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Cosine similarity
        """
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


class FeatureEngineering:
    """Feature engineering for resume matching"""
    
    def __init__(self, embedding_service: EmbeddingService):
        """
        Initialize feature engineering
        
        Args:
            embedding_service: EmbeddingService instance
        """
        self.embedding_service = embedding_service
    
    def create_resume_jd_pairs(self, resumes: List[str], 
                              jds: List[str],
                              category_mapping: Dict[str, int] = None) -> Tuple[List[str], List[str], List[float]]:
        """
        Create positive and negative pairs from resumes and job descriptions
        
        Strategy:
        - Positive: Same category resumes paired with same category JDs
        - Negative: Different category pairs
        
        Args:
            resumes: List of resume texts
            jds: List of job description texts
            category_mapping: Mapping of category to index
            
        Returns:
            Tuple of (resume_texts, jd_texts, labels) where labels are 0 or 1
        """
        # Placeholder: in production, would use actual category labels
        resume_texts = []
        jd_texts = []
        labels = []
        
        # For now, create simple pairs (would need proper category mapping in practice)
        for i, resume in enumerate(resumes[:len(jds)]):
            resume_texts.append(resume)
            jd_texts.append(jds[i])
            labels.append(1.0)  # Positive pair
        
        return resume_texts, jd_texts, labels
    
    def extract_skill_features(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skill-related features from text
        
        Args:
            text: Resume or JD text
            
        Returns:
            Dictionary with skill categories
        """
        # Simple skill extraction (would use spaCy NER in production)
        common_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'typescript'],
            'frameworks': ['django', 'flask', 'fastapi', 'react', 'angular', 'vue', 'express'],
            'databases': ['sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'tools': ['git', 'docker', 'jenkins', 'ci/cd', 'agile', 'scrum']
        }
        
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in common_skills.items():
            found_skills[category] = [s for s in skills if s in text_lower]
        
        return found_skills
    
    def compute_skill_overlap(self, resume_text: str, jd_text: str) -> float:
        """
        Compute skill overlap between resume and JD
        
        Args:
            resume_text: Resume text
            jd_text: Job description text
            
        Returns:
            Skill overlap score (0-1)
        """
        resume_skills = self.extract_skill_features(resume_text)
        jd_skills = self.extract_skill_features(jd_text)
        
        total_jd_skills = sum(len(skills) for skills in jd_skills.values())
        if total_jd_skills == 0:
            return 0.5  # Neutral score
        
        matched_skills = 0
        for category in resume_skills:
            matched_skills += len(set(resume_skills[category]) & set(jd_skills[category]))
        
        return min(1.0, matched_skills / total_jd_skills)
    
    def compute_matching_score(self, resume_embedding: np.ndarray,
                              jd_embedding: np.ndarray,
                              resume_text: str = None,
                              jd_text: str = None,
                              similarity_weight: float = 0.7,
                              skill_weight: float = 0.3) -> float:
        """
        Compute weighted matching score
        
        Args:
            resume_embedding: Resume embedding
            jd_embedding: JD embedding
            resume_text: Resume text (for skill extraction)
            jd_text: JD text (for skill extraction)
            similarity_weight: Weight for semantic similarity
            skill_weight: Weight for skill overlap
            
        Returns:
            Weighted matching score (0-1)
        """
        # Compute semantic similarity
        semantic_sim = self.embedding_service.compute_similarity(resume_embedding, jd_embedding)
        semantic_sim = (semantic_sim + 1) / 2  # Convert from [-1, 1] to [0, 1]
        
        # Compute skill overlap
        if resume_text and jd_text:
            skill_overlap = self.compute_skill_overlap(resume_text, jd_text)
        else:
            skill_overlap = 0.5
        
        # Compute weighted score
        score = (semantic_sim * similarity_weight) + (skill_overlap * skill_weight)
        
        return min(1.0, max(0.0, score))
