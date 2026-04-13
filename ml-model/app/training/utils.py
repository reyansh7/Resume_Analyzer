"""
Utility functions for training pipeline
"""
import logging
import json
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def set_random_seed(seed: int = 42):
    """
    Set random seed for reproducibility
    
    Args:
        seed: Random seed value
    """
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")


def split_data(data: List, 
              train_ratio: float = 0.7,
              val_ratio: float = 0.15,
              test_ratio: float = 0.15,
              random_state: int = 42) -> Tuple[List, List, List]:
    """
    Split data into train, validation, and test sets
    
    Args:
        data: List of data to split
        train_ratio: Proportion for training (default 0.7)
        val_ratio: Proportion for validation (default 0.15)
        test_ratio: Proportion for testing (default 0.15)
        random_state: Random seed
        
    Returns:
        Tuple of (train_data, val_data, test_data)
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
        raise ValueError(f"Ratios must sum to 1.0, got {train_ratio + val_ratio + test_ratio}")
    
    # Set random seed
    random.seed(random_state)
    np.random.seed(random_state)
    
    # Shuffle data
    shuffled_data = data.copy()
    random.shuffle(shuffled_data)
    
    n = len(shuffled_data)
    train_idx = int(n * train_ratio)
    val_idx = train_idx + int(n * val_ratio)
    
    train_data = shuffled_data[:train_idx]
    val_data = shuffled_data[train_idx:val_idx]
    test_data = shuffled_data[val_idx:]
    
    logger.info(f"Data split: train={len(train_data)}, val={len(val_data)}, test={len(test_data)}")
    
    return train_data, val_data, test_data


def stratified_split(data: List,
                    labels: List,
                    train_ratio: float = 0.7,
                    val_ratio: float = 0.15,
                    test_ratio: float = 0.15,
                    random_state: int = 42) -> Tuple[List, List, List]:
    """
    Split data using stratified sampling (maintaining label distribution)
    
    Args:
        data: List of data samples
        labels: Corresponding labels
        train_ratio: Proportion for training
        val_ratio: Proportion for validation
        test_ratio: Proportion for testing
        random_state: Random seed
        
    Returns:
        Tuple of (train_data, val_data, test_data)
    """
    if len(data) != len(labels):
        raise ValueError("Data and labels must have same length")
    
    # Group by label
    label_to_indices = {}
    for i, label in enumerate(labels):
        if label not in label_to_indices:
            label_to_indices[label] = []
        label_to_indices[label].append(i)
    
    # Split each label stratified
    train_indices = []
    val_indices = []
    test_indices = []
    
    random.seed(random_state)
    
    for label, indices in label_to_indices.items():
        random.shuffle(indices)
        n = len(indices)
        train_idx = int(n * train_ratio)
        val_idx = train_idx + int(n * val_ratio)
        
        train_indices.extend(indices[:train_idx])
        val_indices.extend(indices[train_idx:val_idx])
        test_indices.extend(indices[val_idx:])
    
    train_data = [data[i] for i in train_indices]
    val_data = [data[i] for i in val_indices]
    test_data = [data[i] for i in test_indices]
    
    logger.info(f"Stratified split: train={len(train_data)}, val={len(val_data)}, test={len(test_data)}")
    
    return train_data, val_data, test_data


def save_checkpoint(model_state: Dict, 
                   metrics: Dict,
                   checkpoint_dir: Path,
                   epoch: int) -> Path:
    """
    Save model checkpoint
    
    Args:
        model_state: Model state dictionary
        metrics: Training metrics
        checkpoint_dir: Directory to save checkpoint
        epoch: Epoch number
        
    Returns:
        Path to saved checkpoint
    """
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch}.json"
    
    checkpoint = {
        'epoch': epoch,
        'timestamp': datetime.now().isoformat(),
        'model_state': model_state,
        'metrics': metrics
    }
    
    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint, f, indent=2, default=str)
    
    logger.info(f"Checkpoint saved to {checkpoint_path}")
    return checkpoint_path


def load_checkpoint(checkpoint_path: Path) -> Dict:
    """
    Load model checkpoint
    
    Args:
        checkpoint_path: Path to checkpoint file
        
    Returns:
        Checkpoint dictionary
    """
    with open(checkpoint_path, 'r') as f:
        checkpoint = json.load(f)
    
    logger.info(f"Checkpoint loaded from {checkpoint_path}")
    return checkpoint


def save_metrics(metrics: Dict, metrics_path: Path):
    """
    Save training metrics to JSON
    
    Args:
        metrics: Dictionary of metrics
        metrics_path: Path to save metrics
    """
    metrics_path = Path(metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    metrics['timestamp'] = datetime.now().isoformat()
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logger.info(f"Metrics saved to {metrics_path}")


def get_class_distribution(labels: List) -> Dict[str, int]:
    """
    Get distribution of classes in labels
    
    Args:
        labels: List of labels
        
    Returns:
        Dictionary with class counts
    """
    distribution = {}
    for label in labels:
        distribution[label] = distribution.get(label, 0) + 1
    
    return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))


def print_class_distribution(labels: List, name: str = "Dataset"):
    """
    Print class distribution statistics
    
    Args:
        labels: List of labels
        name: Name of dataset for logging
    """
    distribution = get_class_distribution(labels)
    total = len(labels)
    
    logger.info(f"\n{name} Class Distribution:")
    logger.info(f"Total samples: {total}")
    
    for label, count in distribution.items():
        percentage = (count / total) * 100
        logger.info(f"  {label}: {count} ({percentage:.1f}%)")


def batch_generator(data: List, batch_size: int, shuffle: bool = True):
    """
    Generate batches of data
    
    Args:
        data: List of data
        batch_size: Batch size
        shuffle: Whether to shuffle data
        
    Yields:
        Batches of data
    """
    if shuffle:
        data = data.copy()
        random.shuffle(data)
    
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


def calculate_stats(values: List[float]) -> Dict:
    """
    Calculate statistics for a list of values
    
    Args:
        values: List of numerical values
        
    Returns:
        Dictionary with statistics
    """
    if not values:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0
        }
    
    arr = np.array(values)
    
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'median': float(np.median(arr)),
        'count': len(values)
    }


def format_seconds(seconds: float) -> str:
    """
    Format seconds to readable string
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
