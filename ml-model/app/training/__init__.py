"""
Production ML Training Module
Modular pipeline for training resume matching models
"""

from .config import (
    TrainingConfig,
    DataConfig,
    EmbeddingConfig,
    ModelConfig,
    SkillExtractionConfig,
    DEFAULT_CONFIG
)
from .preprocessing import TextPreprocessor, preprocess_text
from .data_loader import DataLoader, ResumeRecord, JobDescriptionRecord
from .feature_engineering import EmbeddingService, FeatureEngineering
from .evaluate import MetricsCalculator, EvaluationMetrics, PerformanceTracker
from .utils import (
    set_random_seed,
    split_data,
    stratified_split,
    save_checkpoint,
    load_checkpoint,
    save_metrics,
    print_class_distribution,
    batch_generator,
)

__all__ = [
    'TrainingConfig',
    'DataConfig',
    'EmbeddingConfig',
    'ModelConfig',
    'SkillExtractionConfig',
    'DEFAULT_CONFIG',
    'TextPreprocessor',
    'preprocess_text',
    'DataLoader',
    'ResumeRecord',
    'JobDescriptionRecord',
    'EmbeddingService',
    'FeatureEngineering',
    'MetricsCalculator',
    'EvaluationMetrics',
    'PerformanceTracker',
    'set_random_seed',
    'split_data',
    'stratified_split',
    'save_checkpoint',
    'load_checkpoint',
    'save_metrics',
    'print_class_distribution',
    'batch_generator',
]
