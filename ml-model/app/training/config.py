"""
Production ML Training Configuration
Centralized settings for data, model, and training parameters
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DataConfig:
    """Data loading and preprocessing configuration"""
    
    # Data sources
    csv_path: Path = Path("Resume/Resume.csv")
    pdf_root: Path = Path("data")
    resumes_pdf_root: Path = Path("Resumes PDF")  # For new training data
    
    # Preprocessing
    min_text_length: int = 100  # Minimum normalized text length
    max_text_length: int = 10000  # Maximum text length (truncate if needed)
    
    # Train-test split (70-15-15)
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # Data handling
    random_state: int = 42
    stratified: bool = True
    remove_duplicates: bool = True
    handle_missing: str = "drop"  # drop or fill
    

@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    
    # Sentence-BERT model
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Embedding parameters
    embedding_dim: int = 384
    batch_size: int = 32
    device: str = "cpu"  # cpu or cuda
    normalize_embeddings: bool = True


@dataclass
class ModelConfig:
    """Model training configuration"""
    
    # Model selection
    model_type: str = "similarity"  # similarity or classifier
    use_similarity_score: bool = True
    use_classification: bool = False
    
    # Training hyperparameters
    learning_rate: float = 0.0001
    batch_size: int = 32
    epochs: int = 10
    validation_split: float = 0.2
    
    # Loss functions
    loss_fn: str = "cosine"  # cosine, mse, triplet, or cross_entropy
    
    # Regularization
    dropout_rate: float = 0.1
    l2_regularization: float = 0.001
    
    # Early stopping
    patience: int = 3
    min_delta: float = 0.001


@dataclass
class SkillExtractionConfig:
    """Skill extraction configuration"""
    
    enable_skill_extraction: bool = True
    spacy_model: str = "en_core_web_sm"
    
    # Skill categories for weighted scoring
    technical_skills_weight: float = 0.4
    experience_weight: float = 0.3
    semantic_similarity_weight: float = 0.3


@dataclass
class TrainingConfig:
    """Combined training configuration"""
    
    data: DataConfig = field(default_factory=DataConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    skill_extraction: SkillExtractionConfig = field(default_factory=SkillExtractionConfig)
    
    # Output paths
    model_save_dir: Path = Path("saved_models")
    metrics_save_path: Path = Path("saved_models/training_metrics.json")
    checkpoint_dir: Path = Path("saved_models/checkpoints")
    
    # Logging
    verbose: bool = True
    log_frequency: int = 100
    
    def __post_init__(self):
        """Create necessary directories"""
        self.model_save_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)


# Default global config
DEFAULT_CONFIG = TrainingConfig()
