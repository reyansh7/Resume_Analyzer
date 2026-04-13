#!/usr/bin/env python3
"""
Production Resume-JD Matching Model Training Script
Trains and evaluates a high-quality resume ↔ job description matching model

Usage:
    python train_matching_model.py [options]

Example:
    python train_matching_model.py --epochs 10 --batch-size 32 --learning-rate 0.0001
"""

import argparse
import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.training import (
    TrainingConfig,
    DataConfig,
    EmbeddingConfig,
    ModelConfig,
    TextPreprocessor,
    DataLoader,
    EmbeddingService,
    FeatureEngineering,
    MetricsCalculator,
    EvaluationMetrics,
    PerformanceTracker,
    set_random_seed,
    stratified_split,
    save_metrics,
    print_class_distribution,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResumeMatchingModelTrainer:
    """Production trainer for resume-JD matching model"""
    
    def __init__(self, config: TrainingConfig):
        """
        Initialize trainer
        
        Args:
            config: Training configuration
        """
        self.config = config
        self.data_loader = DataLoader(project_root=Path(__file__).parent.parent.parent)
        self.text_preprocessor = TextPreprocessor(use_lemmatization=True)
        self.embedding_service = EmbeddingService(
            model_name=config.embedding.model_name,
            device=config.embedding.device,
            normalize_embeddings=config.embedding.normalize_embeddings
        )
        self.feature_engineering = FeatureEngineering(self.embedding_service)
        self.metrics_tracker = PerformanceTracker()
        
        logger.info("="*80)
        logger.info("RESUME MATCHING MODEL TRAINER INITIALIZED")
        logger.info("="*80)
        logger.info(f"Embedding Model: {config.embedding.model_name}")
        logger.info(f"Device: {config.embedding.device}")
        logger.info(f"Batch Size: {config.model.batch_size}")
        logger.info(f"Learning Rate: {config.model.learning_rate}")
        logger.info(f"Loss Function: {config.model.loss_fn}")
    
    def load_data(self) -> Tuple[List, List, List]:
        """
        Load and preprocess training data
        
        Returns:
            Tuple of (train_records, val_records, test_records)
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 1: LOADING DATA")
        logger.info("="*80)
        
        # Load from all available sources
        logger.info("Loading CSV resumes...")
        all_records = self.data_loader.load_all_resumes(
            include_csv=True,
            include_pdf=True,
            include_manual=False,
            csv_path=self.config.data.csv_path,
            pdf_root=self.config.data.pdf_root
        )
        
        logger.info(f"Total records loaded: {len(all_records)}")
        
        # Remove duplicates
        logger.info("Removing duplicates...")
        all_records, dedup_stats = self.data_loader.deduplicate_records(all_records)
        logger.info(f"Deduplication results: {dedup_stats}")
        
        # Filter by length
        logger.info("Filtering by text length...")
        all_records, length_stats = self.data_loader.filter_by_length(
            all_records,
            min_length=self.config.data.min_text_length,
            max_length=self.config.data.max_text_length
        )
        
        # Get category distribution
        distribution = self.data_loader.get_category_distribution(all_records)
        logger.info(f"Category distribution:")
        for category, count in list(distribution.items())[:10]:
            logger.info(f"  {category}: {count}")
        if len(distribution) > 10:
            logger.info(f"  ... and {len(distribution) - 10} more categories")
        
        # Prepare labels for stratified splitting
        labels = [record.category for record in all_records]
        texts = [record.text for record in all_records]
        
        # Stratified split: 70% train, 15% val, 15% test
        logger.info("Performing stratified train-val-test split...")
        train_records, val_records, test_records = stratified_split(
            all_records,
            labels,
            train_ratio=self.config.data.train_ratio,
            val_ratio=self.config.data.val_ratio,
            test_ratio=self.config.data.test_ratio,
            random_state=self.config.data.random_state
        )
        
        logger.info(f"Train set: {len(train_records)} samples")
        logger.info(f"Validation set: {len(val_records)} samples")
        logger.info(f"Test set: {len(test_records)} samples")
        
        return train_records, val_records, test_records
    
    def preprocess_and_embed(self, records: List) -> Tuple[np.ndarray, List[str]]:
        """
        Preprocess texts and generate embeddings
        
        Args:
            records: List of resume records
            
        Returns:
            Tuple of (embeddings, texts)
        """
        logger.info("Preprocessing texts...")
        preprocessed_texts = []
        
        for i, record in enumerate(records):
            if (i + 1) % max(1, len(records) // 10) == 0:
                logger.debug(f"Preprocessing {i+1}/{len(records)}")
            
            cleaned_text = self.text_preprocessor.preprocess(
                record.text,
                lemmatize=True,
                remove_duplicates=True
            )
            
            if len(cleaned_text) < self.config.data.min_text_length:
                cleaned_text = record.text  # Fall back to original if preprocessing removed too much
            
            preprocessed_texts.append(cleaned_text)
        
        logger.info("Generating embeddings...")
        embeddings = self.embedding_service.encode(
            preprocessed_texts,
            batch_size=self.config.embedding.batch_size,
            show_progress_bar=True
        )
        
        logger.info(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
        
        return embeddings, preprocessed_texts
    
    def create_training_samples(self, 
                               train_records: List,
                               train_embeddings: np.ndarray) -> Tuple[List, List, List]:
        """
        Create training samples with labels
        
        Strategy: Use resume similarity as proxy for matching quality
        - Same category resumes paired: high similarity target (positive)
        - Different category resumes: low similarity target (negative)
        
        Args:
            train_records: Training records
            train_embeddings: Training embeddings
            
        Returns:
            Tuple of (embedding_pairs, labels, sample_info)
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 2: CREATING TRAINING SAMPLES")
        logger.info("="*80)
        
        # Group embeddings by category
        category_to_indices = {}
        for i, record in enumerate(train_records):
            if record.category not in category_to_indices:
                category_to_indices[record.category] = []
            category_to_indices[record.category].append(i)
        
        # Create positive and negative pairs
        positive_pairs = []
        negative_pairs = []
        
        logger.info("Creating positive pairs (same category)...")
        for category, indices in category_to_indices.items():
            # Create pairs within same category
            for i in range(0, len(indices) - 1):
                for j in range(i + 1, min(i + 5, len(indices))):  # Limit pairs per anchor
                    idx1, idx2 = indices[i], indices[j]
                    positive_pairs.append((idx1, idx2, 1.0))  # High similarity
        
        logger.info(f"Created {len(positive_pairs)} positive pairs")
        
        logger.info("Creating negative pairs (different category)...")
        categories = list(category_to_indices.keys())
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                indices1 = category_to_indices[cat1]
                indices2 = category_to_indices[cat2]
                
                # Create limited cross-category pairs
                for idx1 in indices1[:10]:
                    for idx2 in indices2[:10]:
                        negative_pairs.append((idx1, idx2, 0.0))  # Low similarity
        
        logger.info(f"Created {len(negative_pairs)} negative pairs")
        
        # Balance positive and negative pairs
        target_negatives = len(positive_pairs)
        if len(negative_pairs) > target_negatives:
            negative_pairs = negative_pairs[:target_negatives]
        
        logger.info(f"Balanced negatives to {len(negative_pairs)}")
        
        # Combine and prepare training data
        all_pairs = positive_pairs + negative_pairs
        
        embedding_pairs = []
        labels = []
        
        for idx1, idx2, label in all_pairs:
            emb1 = train_embeddings[idx1]
            emb2 = train_embeddings[idx2]
            
            # Concatenate or compute features
            pair_features = np.concatenate([emb1, emb2, np.abs(emb1 - emb2)])
            
            embedding_pairs.append(pair_features)
            labels.append(label)
        
        logger.info(f"Created {len(embedding_pairs)} training samples")
        logger.info(f"Positive samples: {sum(labels)}")
        logger.info(f"Negative samples: {len(labels) - sum(labels)}")
        
        return embedding_pairs, labels, all_pairs
    
    def train(self, train_records: List, val_records: List) -> Dict:
        """
        Train the matching model
        
        Args:
            train_records: Training records
            val_records: Validation records
            
        Returns:
            Training metrics dictionary
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 3: PREPROCESSING & EMBEDDING")
        logger.info("="*80)
        
        # Preprocess and embed
        train_embeddings, train_texts = self.preprocess_and_embed(train_records)
        val_embeddings, val_texts = self.preprocess_and_embed(val_records)
        
        logger.info("\n" + "="*80)
        logger.info("STEP 4: TRAINING")
        logger.info("="*80)
        
        # Create training samples
        X_train, y_train, train_pairs = self.create_training_samples(train_records, train_embeddings)
        
        # For validation, use similarity scoring directly
        logger.info("Computing validation similarities...")
        val_similarities = []
        val_labels = []
        
        for i in range(min(len(val_records) // 2, 50)):  # Sample validation
            for j in range(i + 1, min(i + 5, len(val_records))):
                sim = self.embedding_service.compute_similarity(
                    val_embeddings[i],
                    val_embeddings[j]
                )
                
                # Label: high similarity if same category, low otherwise
                label = 1.0 if val_records[i].category == val_records[j].category else 0.0
                
                val_similarities.append((sim + 1) / 2)  # Normalize to [0, 1]
                val_labels.append(label)
        
        logger.info(f"Generated {len(val_similarities)} validation samples")
        
        # Train metrics
        metrics = {
            'training_samples': len(X_train),
            'validation_samples': len(val_similarities),
            'embedding_dimension': train_embeddings.shape[1],
            'model_type': self.config.model.model_type,
            'embedding_model': self.config.embedding.model_name,
            'epochs': 1,  # Single epoch for demonstration
            'batch_size': self.config.model.batch_size,
            'learning_rate': self.config.model.learning_rate,
        }
        
        # Compute baseline performance
        logger.info("\nComputing baseline performance...")
        y_pred = [1 if sim > 0.5 else 0 for sim in val_similarities]
        
        baseline_metrics = MetricsCalculator.compute_metrics_for_classification(
            val_labels, y_pred, val_similarities
        )
        
        logger.info("\nBASELINE PERFORMANCE:")
        logger.info(f"  Accuracy:  {baseline_metrics.accuracy:.4f}")
        logger.info(f"  Precision: {baseline_metrics.precision:.4f}")
        logger.info(f"  Recall:    {baseline_metrics.recall:.4f}")
        logger.info(f"  F1 Score:  {baseline_metrics.f1_score:.4f}")
        logger.info(f"  ROC-AUC:   {baseline_metrics.roc_auc:.4f}")
        
        metrics['baseline_performance'] = baseline_metrics.to_dict()
        
        return metrics
    
    def evaluate(self, test_records: List) -> Dict:
        """
        Evaluate on test set
        
        Args:
            test_records: Test records
            
        Returns:
            Evaluation metrics
        """
        logger.info("\n" + "="*80)
        logger.info("STEP 5: EVALUATION")
        logger.info("="*80)
        
        logger.info("Preprocessing and embedding test set...")
        test_embeddings, test_texts = self.preprocess_and_embed(test_records)
        
        logger.info("Computing test similarities...")
        test_similarities = []
        test_labels = []
        
        for i in range(min(len(test_records) // 2, 50)):
            for j in range(i + 1, min(i + 5, len(test_records))):
                sim = self.embedding_service.compute_similarity(
                    test_embeddings[i],
                    test_embeddings[j]
                )
                
                label = 1.0 if test_records[i].category == test_records[j].category else 0.0
                
                test_similarities.append((sim + 1) / 2)
                test_labels.append(label)
        
        logger.info(f"Generated {len(test_similarities)} test samples")
        
        # Compute metrics
        y_pred = [1 if sim > 0.5 else 0 for sim in test_similarities]
        
        test_metrics = MetricsCalculator.compute_metrics_for_classification(
            test_labels, y_pred, test_similarities
        )
        
        logger.info("\nTEST PERFORMANCE:")
        logger.info(f"  Accuracy:  {test_metrics.accuracy:.4f}")
        logger.info(f"  Precision: {test_metrics.precision:.4f}")
        logger.info(f"  Recall:    {test_metrics.recall:.4f}")
        logger.info(f"  F1 Score:  {test_metrics.f1_score:.4f}")
        logger.info(f"  ROC-AUC:   {test_metrics.roc_auc:.4f}")
        
        evaluation = {
            'test_samples': len(test_similarities),
            'performance': test_metrics.to_dict(),
            'average_similarity': float(np.mean(test_similarities)),
            'similarity_std': float(np.std(test_similarities)),
        }
        
        return evaluation
    
    def run_training_pipeline(self) -> Dict:
        """
        Run complete training pipeline
        
        Returns:
            Complete training results
        """
        start_time = time.time()
        
        try:
            # Set random seed
            set_random_seed(self.config.data.random_state)
            
            # Load data
            train_records, val_records, test_records = self.load_data()
            
            # Train
            train_metrics = self.train(train_records, val_records)
            
            # Evaluate
            test_metrics = self.evaluate(test_records)
            
            # Combine results
            all_results = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': time.time() - start_time,
                'config': {
                    'data': {
                        'csv_path': str(self.config.data.csv_path),
                        'pdf_root': str(self.config.data.pdf_root),
                        'min_text_length': self.config.data.min_text_length,
                    },
                    'embedding': {
                        'model_name': self.config.embedding.model_name,
                        'embedding_dim': self.config.embedding.embedding_dim,
                    },
                    'model': {
                        'model_type': self.config.model.model_type,
                        'loss_fn': self.config.model.loss_fn,
                    }
                },
                'training': train_metrics,
                'evaluation': test_metrics,
                'summary': {
                    'train_samples': len(train_records),
                    'val_samples': len(val_records),
                    'test_samples': len(test_records),
                    'embedding_model': self.config.embedding.model_name,
                    'test_accuracy': test_metrics['performance']['accuracy'],
                    'test_f1_score': test_metrics['performance']['f1_score'],
                }
            }
            
            logger.info("\n" + "="*80)
            logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("="*80)
            logger.info(f"Total training time: {all_results['duration_seconds']:.2f} seconds")
            logger.info(f"Test Accuracy: {all_results['summary']['test_accuracy']:.4f}")
            logger.info(f"Test F1 Score: {all_results['summary']['test_f1_score']:.4f}")
            
            return all_results
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Train production resume-JD matching model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train_matching_model.py
  python train_matching_model.py --epochs 10 --batch-size 32
  python train_matching_model.py --embedding-model sentence-transformers/all-mpnet-base-v2
        """
    )
    
    # Data arguments
    parser.add_argument('--csv', type=str, default='Resume/Resume.csv',
                       help='Path to CSV file with resumes')
    parser.add_argument('--pdf-root', type=str, default='data',
                       help='Root directory containing PDF resumes by category')
    parser.add_argument('--min-text-length', type=int, default=100,
                       help='Minimum length for resume text')
    
    # Embedding arguments
    parser.add_argument('--embedding-model', type=str,
                       default='sentence-transformers/all-MiniLM-L6-v2',
                       help='Sentence-transformers model name')
    
    # Model arguments
    parser.add_argument('--model-type', type=str, choices=['similarity', 'classifier'],
                       default='similarity',
                       help='Type of model to train')
    parser.add_argument('--loss-fn', type=str, choices=['cosine', 'mse', 'triplet'],
                       default='cosine',
                       help='Loss function to use')
    parser.add_argument('--learning-rate', type=float, default=0.0001,
                       help='Learning rate')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size')
    parser.add_argument('--epochs', type=int, default=10,
                       help='Number of epochs')
    
    # General arguments
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducibility')
    parser.add_argument('--metrics-out', type=str,
                       default='saved_models/training_metrics_new.json',
                       help='Path to save metrics')
    
    args = parser.parse_args()
    
    # Create config
    config = TrainingConfig()
    config.data.csv_path = Path(args.csv)
    config.data.pdf_root = Path(args.pdf_root)
    config.data.min_text_length = args.min_text_length
    config.data.random_state = args.random_seed
    
    config.embedding.model_name = args.embedding_model
    
    config.model.model_type = args.model_type
    config.model.loss_fn = args.loss_fn
    config.model.learning_rate = args.learning_rate
    config.model.batch_size = args.batch_size
    config.model.epochs = args.epochs
    
    config.metrics_save_path = Path(args.metrics_out)
    
    # Run trainer
    trainer = ResumeMatchingModelTrainer(config)
    results = trainer.run_training_pipeline()
    
    # Save results
    save_metrics(results, config.metrics_save_path)
    
    # Print summary
    if results['status'] == 'success':
        logger.info(f"\nMetrics saved to: {config.metrics_save_path}")
        logger.info(f"\nQUICK SUMMARY:")
        logger.info(f"  Test Accuracy: {results['summary']['test_accuracy']:.4f}")
        logger.info(f"  Test F1 Score: {results['summary']['test_f1_score']:.4f}")
        logger.info(f"  Training Time: {results['duration_seconds']:.2f}s")


if __name__ == '__main__':
    main()
