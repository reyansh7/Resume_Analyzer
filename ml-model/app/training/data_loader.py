"""
Data Loading and Management
Loads resume data from CSV, PDFs, and new sources
"""
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import json

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger(__name__)


@dataclass
class ResumeRecord:
    """Single resume data record"""
    text: str
    category: str
    source: str = "unknown"  # csv, pdf, manual
    confidence: float = 1.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'category': self.category,
            'source': self.source,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


@dataclass
class JobDescriptionRecord:
    """Job description record for resume-JD matching"""
    text: str
    title: str
    category: str
    required_skills: List[str] = None
    min_experience: int = 0
    source: str = "manual"
    
    def __post_init__(self):
        if self.required_skills is None:
            self.required_skills = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'title': self.title,
            'category': self.category,
            'required_skills': self.required_skills,
            'min_experience': self.min_experience,
            'source': self.source
        }


class DataLoader:
    """Production data loader for resumes and job descriptions"""
    
    def __init__(self, project_root: Path = None):
        """
        Initialize data loader
        
        Args:
            project_root: Root directory of ml-model folder
        """
        self.project_root = project_root or Path(__file__).resolve().parents[2]
    
    def load_csv_resumes(self, csv_path: Path = None) -> List[ResumeRecord]:
        """
        Load resumes from CSV file
        
        Args:
            csv_path: Path to CSV file (relative to project root)
            
        Returns:
            List of ResumeRecord objects
        """
        if pd is None:
            logger.warning("pandas not available, skipping CSV loading")
            return []
        
        csv_path = csv_path or self.project_root / "Resume" / "Resume.csv"
        
        if not csv_path.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            return []
        
        try:
            df = pd.read_csv(csv_path)
            records = []
            
            for _, row in df.iterrows():
                # Use Resume_str if available, otherwise Resume_html
                text = row.get('Resume_str') or row.get('Resume_html', '')
                category = row.get('Category', 'UNKNOWN')
                
                if text and len(str(text).strip()) > 0:
                    record = ResumeRecord(
                        text=str(text),
                        category=str(category),
                        source='csv',
                        metadata={'id': row.get('ID', 'unknown')}
                    )
                    records.append(record)
            
            logger.info(f"Loaded {len(records)} resumes from CSV: {csv_path}")
            return records
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return []
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        if PdfReader is None:
            logger.warning("pypdf not available, skipping PDF")
            return ""
        
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.warning(f"Error extracting PDF {pdf_path}: {e}")
            return ""
    
    def load_pdf_resumes(self, pdf_root: Path = None, 
                        max_pdfs_per_category: int = None) -> List[ResumeRecord]:
        """
        Load resumes from PDF files organized by category
        
        Expected structure:
        pdf_root/
        ├── CATEGORY1/
        │   ├── resume1.pdf
        │   └── resume2.pdf
        └── CATEGORY2/
            └── resume3.pdf
        
        Args:
            pdf_root: Root directory containing category folders
            max_pdfs_per_category: Limit PDFs per category (for testing)
            
        Returns:
            List of ResumeRecord objects
        """
        pdf_root = pdf_root or self.project_root / "data"
        
        if not pdf_root.exists():
            logger.warning(f"PDF root directory not found: {pdf_root}")
            return []
        
        records = []
        
        # Iterate through category folders
        for category_dir in pdf_root.iterdir():
            if not category_dir.is_dir():
                continue
            
            category = category_dir.name
            pdf_count = 0
            
            # Load PDFs from category folder
            for pdf_file in category_dir.glob("*.pdf"):
                if max_pdfs_per_category and pdf_count >= max_pdfs_per_category:
                    break
                
                text = self.extract_pdf_text(pdf_file)
                
                if text and len(text.strip()) > 0:
                    record = ResumeRecord(
                        text=text,
                        category=category,
                        source='pdf',
                        metadata={'filename': pdf_file.name}
                    )
                    records.append(record)
                    pdf_count += 1
            
            if pdf_count > 0:
                logger.debug(f"Loaded {pdf_count} PDFs from {category}")
        
        logger.info(f"Loaded {len(records)} resumes from PDFs: {pdf_root}")
        return records
    
    def load_manual_resumes(self, json_file: Path = None) -> List[ResumeRecord]:
        """
        Load manually created/annotated resumes from JSON
        
        JSON format:
        [
            {
                "text": "...",
                "category": "CATEGORY",
                "description": "..."
            }
        ]
        
        Args:
            json_file: Path to JSON file
            
        Returns:
            List of ResumeRecord objects
        """
        if json_file is None or not json_file.exists():
            return []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = []
            for item in data:
                if isinstance(item, dict) and 'text' in item and 'category' in item:
                    record = ResumeRecord(
                        text=item['text'],
                        category=item['category'],
                        source='manual',
                        metadata=item.get('metadata', {})
                    )
                    records.append(record)
            
            logger.info(f"Loaded {len(records)} resumes from JSON: {json_file}")
            return records
            
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return []
    
    def load_all_resumes(self, 
                        include_csv: bool = True,
                        include_pdf: bool = True,
                        include_manual: bool = False,
                        csv_path: Path = None,
                        pdf_root: Path = None,
                        manual_json: Path = None) -> List[ResumeRecord]:
        """
        Load resumes from all available sources
        
        Args:
            include_csv: Load from CSV
            include_pdf: Load from PDFs
            include_manual: Load from manual JSON
            csv_path: Custom CSV path
            pdf_root: Custom PDF root
            manual_json: Custom JSON path
            
        Returns:
            Combined list of ResumeRecord objects
        """
        all_records = []
        
        if include_csv:
            csv_records = self.load_csv_resumes(csv_path)
            all_records.extend(csv_records)
        
        if include_pdf:
            pdf_records = self.load_pdf_resumes(pdf_root)
            all_records.extend(pdf_records)
        
        if include_manual:
            manual_records = self.load_manual_resumes(manual_json)
            all_records.extend(manual_records)
        
        logger.info(f"Total records loaded: {len(all_records)}")
        return all_records
    
    def deduplicate_records(self, records: List[ResumeRecord],
                           similarity_threshold: float = 0.95) -> Tuple[List[ResumeRecord], Dict]:
        """
        Remove duplicate or near-duplicate records
        
        Args:
            records: List of records to deduplicate
            similarity_threshold: Cosine similarity threshold for duplicates
            
        Returns:
            Deduplicated records and statistics
        """
        if len(records) < 2:
            return records, {'duplicates_removed': 0, 'duplicates_found': 0}
        
        # Simple duplicate detection: exact text match
        seen_texts = set()
        unique_records = []
        duplicates_found = 0
        
        for record in records:
            text_hash = hash(record.text.lower()[:500])  # Use first 500 chars as hash
            
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_records.append(record)
            else:
                duplicates_found += 1
        
        stats = {
            'duplicates_found': duplicates_found,
            'duplicates_removed': duplicates_found,
            'unique_count': len(unique_records),
            'original_count': len(records)
        }
        
        logger.info(f"Deduplicated: {duplicates_found} duplicates removed, {len(unique_records)} unique records remain")
        return unique_records, stats
    
    def get_category_distribution(self, records: List[ResumeRecord]) -> Dict[str, int]:
        """
        Get distribution of categories in records
        
        Args:
            records: List of ResumeRecord objects
            
        Returns:
            Dictionary with category counts
        """
        distribution = {}
        for record in records:
            distribution[record.category] = distribution.get(record.category, 0) + 1
        
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    def filter_by_length(self, records: List[ResumeRecord],
                        min_length: int = 100,
                        max_length: int = 10000) -> Tuple[List[ResumeRecord], Dict]:
        """
        Filter records by text length
        
        Args:
            records: List of records
            min_length: Minimum text length
            max_length: Maximum text length
            
        Returns:
            Filtered records and statistics
        """
        filtered_records = []
        removed_too_short = 0
        removed_too_long = 0
        
        for record in records:
            text_len = len(record.text)
            
            if text_len < min_length:
                removed_too_short += 1
            elif text_len > max_length:
                removed_too_long += 1
            else:
                filtered_records.append(record)
        
        stats = {
            'original_count': len(records),
            'filtered_count': len(filtered_records),
            'removed_too_short': removed_too_short,
            'removed_too_long': removed_too_long,
            'min_length': min_length,
            'max_length': max_length
        }
        
        logger.info(f"Length filtering: {len(filtered_records)} records kept "
                   f"({removed_too_short} too short, {removed_too_long} too long)")
        return filtered_records, stats
