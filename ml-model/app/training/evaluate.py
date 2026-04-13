"""
Evaluation Metrics
Comprehensive metrics for model evaluation and performance tracking
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    roc_auc: float = 0.0
    mean_reciprocal_rank: float = 0.0
    average_similarity: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'accuracy': round(self.accuracy, 4),
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'roc_auc': round(self.roc_auc, 4),
            'mean_reciprocal_rank': round(self.mean_reciprocal_rank, 4),
            'average_similarity': round(self.average_similarity, 4),
        }


class MetricsCalculator:
    """Calculate various evaluation metrics"""
    
    @staticmethod
    def compute_confusion_matrix(y_true: List[int], 
                                y_pred: List[int]) -> Tuple[int, int, int, int]:
        """
        Compute confusion matrix elements
        
        Args:
            y_true: True labels (0 or 1)
            y_pred: Predicted labels (0 or 1)
            
        Returns:
            Tuple of (TP, FP, FN, TN)
        """
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
        
        return tp, fp, fn, tn
    
    @staticmethod
    def compute_accuracy(y_true: List, y_pred: List) -> float:
        """
        Compute accuracy
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Accuracy score
        """
        if len(y_true) == 0:
            return 0.0
        
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        return correct / len(y_true)
    
    @staticmethod
    def compute_precision(tp: int, fp: int) -> float:
        """
        Compute precision = TP / (TP + FP)
        
        Args:
            tp: True positives
            fp: False positives
            
        Returns:
            Precision score
        """
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)
    
    @staticmethod
    def compute_recall(tp: int, fn: int) -> float:
        """
        Compute recall = TP / (TP + FN)
        
        Args:
            tp: True positives
            fn: False negatives
            
        Returns:
            Recall score
        """
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)
    
    @staticmethod
    def compute_f1_score(precision: float, recall: float) -> float:
        """
        Compute F1 score = 2 * (precision * recall) / (precision + recall)
        
        Args:
            precision: Precision score
            recall: Recall score
            
        Returns:
            F1 score
        """
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def compute_roc_auc(y_true: List[int], y_scores: List[float]) -> float:
        """
        Compute ROC-AUC score
        
        Args:
            y_true: True binary labels
            y_scores: Predicted scores/probabilities
            
        Returns:
            ROC-AUC score
        """
        if len(y_true) < 2:
            return 0.0
        
        # Sort by scores
        sorted_indices = np.argsort(y_scores)[::-1]
        y_true_sorted = [y_true[i] for i in sorted_indices]
        
        tp = 0
        fp = 0
        auc = 0.0
        prev_fp = 0
        
        n_pos = sum(y_true)
        n_neg = len(y_true) - n_pos
        
        if n_pos == 0 or n_neg == 0:
            return 0.5  # Random classifier
        
        for label in y_true_sorted:
            if label == 1:
                tp += 1
            else:
                fp += 1
            
            auc += (fp - prev_fp) * tp
            prev_fp = fp
        
        auc /= (n_pos * n_neg)
        return auc
    
    @staticmethod
    def compute_mean_reciprocal_rank(ranked_results: List[int], 
                                     relevant_threshold: int = 1) -> float:
        """
        Compute Mean Reciprocal Rank
        
        Measures how high the first relevant result appears in ranking
        
        Args:
            ranked_results: List of relevance scores (1 = relevant, 0 = not relevant)
            relevant_threshold: Score threshold for relevance
            
        Returns:
            MRR score
        """
        for i, score in enumerate(ranked_results, 1):
            if score >= relevant_threshold:
                return 1.0 / i
        
        return 0.0
    
    @staticmethod
    def compute_metrics_for_classification(y_true: List[int], 
                                          y_pred: List[int],
                                          y_scores: Optional[List[float]] = None) -> EvaluationMetrics:
        """
        Compute all classification metrics
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_scores: Predicted scores (for ROC-AUC)
            
        Returns:
            EvaluationMetrics object
        """
        # Compute confusion matrix
        tp, fp, fn, tn = MetricsCalculator.compute_confusion_matrix(y_true, y_pred)
        
        # Compute metrics
        accuracy = MetricsCalculator.compute_accuracy(y_true, y_pred)
        precision = MetricsCalculator.compute_precision(tp, fp)
        recall = MetricsCalculator.compute_recall(tp, fn)
        f1 = MetricsCalculator.compute_f1_score(precision, recall)
        
        roc_auc = 0.0
        if y_scores is not None:
            y_scores_binary = [1 if s > 0.5 else 0 for s in y_scores]
            roc_auc = MetricsCalculator.compute_roc_auc(y_true, y_scores)
        
        return EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc
        )
    
    @staticmethod
    def compute_metrics_for_ranking(similarities: List[float],
                                   labels: List[int]) -> EvaluationMetrics:
        """
        Compute metrics for ranking/similarity tasks
        
        Args:
            similarities: Computed similarity scores
            labels: Ground truth labels (1 = match, 0 = no match)
            
        Returns:
            EvaluationMetrics object
        """
        # Convert similarities to predictions (threshold at 0.5)
        y_pred = [1 if s > 0.5 else 0 for s in similarities]
        
        # Compute classification metrics
        metrics = MetricsCalculator.compute_metrics_for_classification(
            labels, y_pred, similarities
        )
        
        # Compute average similarity
        avg_similarity = np.mean(similarities) if similarities else 0.0
        metrics.average_similarity = avg_similarity
        
        # Compute MRR on ranked results
        sorted_indices = np.argsort(similarities)[::-1]
        ranked_labels = [labels[i] for i in sorted_indices]
        mrr = MetricsCalculator.compute_mean_reciprocal_rank(ranked_labels)
        metrics.mean_reciprocal_rank = mrr
        
        return metrics


class PerformanceTracker:
    """Track performance over training iterations"""
    
    def __init__(self):
        """Initialize performance tracker"""
        self.losses = []
        self.accuracies = []
        self.f1_scores = []
        self.val_losses = []
        self.val_accuracies = []
        self.val_f1_scores = []
    
    def add_train_batch(self, loss: float, accuracy: float = None, f1: float = None):
        """Add training batch metrics"""
        self.losses.append(loss)
        if accuracy is not None:
            self.accuracies.append(accuracy)
        if f1 is not None:
            self.f1_scores.append(f1)
    
    def add_val_batch(self, loss: float, accuracy: float = None, f1: float = None):
        """Add validation batch metrics"""
        self.val_losses.append(loss)
        if accuracy is not None:
            self.val_accuracies.append(accuracy)
        if f1 is not None:
            self.val_f1_scores.append(f1)
    
    def get_train_summary(self) -> Dict:
        """Get training summary statistics"""
        return {
            'avg_loss': np.mean(self.losses) if self.losses else 0.0,
            'min_loss': np.min(self.losses) if self.losses else 0.0,
            'max_loss': np.max(self.losses) if self.losses else 0.0,
            'avg_accuracy': np.mean(self.accuracies) if self.accuracies else 0.0,
            'avg_f1': np.mean(self.f1_scores) if self.f1_scores else 0.0,
        }
    
    def get_val_summary(self) -> Dict:
        """Get validation summary statistics"""
        return {
            'avg_loss': np.mean(self.val_losses) if self.val_losses else 0.0,
            'min_loss': np.min(self.val_losses) if self.val_losses else 0.0,
            'max_loss': np.max(self.val_losses) if self.val_losses else 0.0,
            'avg_accuracy': np.mean(self.val_accuracies) if self.val_accuracies else 0.0,
            'avg_f1': np.mean(self.val_f1_scores) if self.val_f1_scores else 0.0,
        }
    
    def should_stop_early(self, patience: int = 3, min_delta: float = 0.001) -> bool:
        """
        Check if should stop early based on validation loss
        
        Args:
            patience: Number of iterations without improvement
            min_delta: Minimum improvement threshold
            
        Returns:
            True if should stop early
        """
        if len(self.val_losses) < patience:
            return False
        
        # Check if validation loss improved in last `patience` iterations
        best_loss = min(self.val_losses[:-patience])
        recent_loss = self.val_losses[-1]
        
        if best_loss - recent_loss < min_delta:
            return False  # Recent loss is better
        
        return True
