"""
Text Preprocessing Pipeline
Handles text cleaning, normalization, and preparation for ML
"""
import re
import unicodedata
import logging
from typing import List, Tuple, Optional

try:
    import spacy
except ImportError:
    spacy = None

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Production-grade text preprocessing pipeline"""
    
    def __init__(self, 
                 use_lemmatization: bool = True,
                 spacy_model: str = "en_core_web_sm"):
        """
        Initialize text preprocessor
        
        Args:
            use_lemmatization: Whether to use spaCy lemmatization
            spacy_model: spaCy model to use
        """
        self.use_lemmatization = use_lemmatization
        self.nlp = None
        
        if use_lemmatization and spacy is not None:
            try:
                self.nlp = spacy.load(spacy_model)
            except OSError:
                logger.warning(f"spaCy model {spacy_model} not found. Run: python -m spacy download {spacy_model}")
                self.use_lemmatization = False
    
    @staticmethod
    def remove_html_tags(text: str) -> str:
        """Remove HTML tags and entities"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = unicodedata.normalize('NFKD', text)
        return text
    
    @staticmethod
    def remove_special_characters(text: str) -> str:
        """
        Remove special characters while preserving alphanumeric and spaces
        Keep some important punctuation (dots, commas, hyphens for compound words)
        """
        # Keep alphanumeric, spaces, dots (for abbreviations), hyphens, @, dots in emails
        text = re.sub(r'[^\w\s@.,-]', ' ', text)
        return text
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace - remove extra spaces, tabs, newlines"""
        # Replace multiple spaces, tabs, newlines with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def normalize_case(text: str) -> str:
        """Convert to lowercase for consistency"""
        return text.lower()
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs"""
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        return text
    
    @staticmethod
    def remove_emails(text: str) -> str:
        """Remove email addresses"""
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        return text
    
    @staticmethod
    def remove_phone_numbers(text: str) -> str:
        """Remove phone numbers"""
        text = re.sub(r'\b[\d\-\+\(\)\s]{10,}\b', '', text)
        return text
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple whitespace tokenization"""
        return text.split()
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        Lemmatize tokens using spaCy
        
        Args:
            tokens: List of word tokens
            
        Returns:
            List of lemmatized tokens
        """
        if not self.use_lemmatization or self.nlp is None:
            return tokens
        
        text = ' '.join(tokens)
        doc = self.nlp(text)
        return [token.lemma_ for token in doc]
    
    def preprocess(self, 
                   text: Optional[str],
                   remove_duplicates: bool = True,
                   lemmatize: bool = True) -> str:
        """
        Full preprocessing pipeline
        
        Args:
            text: Raw input text
            remove_duplicates: Remove consecutive duplicate words
            lemmatize: Apply lemmatization
            
        Returns:
            Cleaned and normalized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Remove HTML tags
        text = self.remove_html_tags(text)
        
        # Step 2: Remove URLs, emails, phone numbers
        text = self.remove_urls(text)
        text = self.remove_emails(text)
        text = self.remove_phone_numbers(text)
        
        # Step 3: Remove special characters (preserve some punctuation)
        text = self.remove_special_characters(text)
        
        # Step 4: Normalize whitespace
        text = self.normalize_whitespace(text)
        
        # Step 5: Normalize case
        text = self.normalize_case(text)
        
        # Step 6: Tokenization
        tokens = self.tokenize(text)
        
        # Step 7: Lemmatization (optional)
        if lemmatize and self.use_lemmatization:
            tokens = self.lemmatize(tokens)
        
        # Step 8: Remove consecutive duplicates (optional)
        if remove_duplicates:
            tokens = [tokens[i] for i in range(len(tokens)) 
                     if i == 0 or tokens[i] != tokens[i-1]]
        
        # Rejoin tokens
        cleaned_text = ' '.join(tokens)
        
        return cleaned_text
    
    @staticmethod
    def truncate(text: str, max_length: int) -> str:
        """Truncate text to maximum length"""
        if len(text) > max_length:
            text = text[:max_length]
        return text
    
    @staticmethod
    def segment_into_sentences(text: str) -> List[str]:
        """
        Simple sentence segmentation based on punctuation
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Split on common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences


def preprocess_text(text: Optional[str],
                   min_length: int = 100,
                   max_length: int = 10000,
                   use_lemmatization: bool = False) -> str:
    """
    Convenience function for single text preprocessing
    
    Args:
        text: Input text to preprocess
        min_length: Minimum text length to keep
        max_length: Maximum text length (truncate if needed)
        use_lemmatization: Whether to use lemmatization
        
    Returns:
        Preprocessed text or empty string if invalid
    """
    if not text or not isinstance(text, str):
        return ""
    
    preprocessor = TextPreprocessor(use_lemmatization=use_lemmatization)
    
    # Apply preprocessing
    cleaned = preprocessor.preprocess(text)
    
    # Truncate if needed
    cleaned = preprocessor.truncate(cleaned, max_length)
    
    # Filter by minimum length
    if len(cleaned) < min_length:
        logger.debug(f"Text too short after preprocessing: {len(cleaned)} < {min_length}")
        return ""
    
    return cleaned
