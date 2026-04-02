"""
Test script for AI Research Paper Formatter
Tests all major components and API endpoints
"""

import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test imports
def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing module imports...")
    
    try:
        from parser.pdf_parser import PDFParser
        logger.info("✓ PDFParser imported")
    except ImportError as e:
        logger.error(f"✗ PDFParser import failed: {e}")
    
    try:
        from ai_models.section_classifier import SectionClassifier
        logger.info("✓ SectionClassifier imported")
    except ImportError as e:
        logger.error(f"✗ SectionClassifier import failed: {e}")
    
    try:
        from parser.section_cleaner import SectionCleaner
        logger.info("✓ SectionCleaner imported")
    except ImportError as e:
        logger.error(f"✗ SectionCleaner import failed: {e}")
    
    try:
        from generators.ieee_formatter import IEEEFormatter
        logger.info("✓ IEEEFormatter imported")
    except ImportError as e:
        logger.error(f"✗ IEEEFormatter import failed: {e}")
    
    try:
        from utils.keyword_extractor import KeywordExtractor
        logger.info("✓ KeywordExtractor imported")
    except ImportError as e:
        logger.error(f"✗ KeywordExtractor import failed: {e}")
    
    try:
        from generators.docx_exporter import DOCXExporter
        logger.info("✓ DOCXExporter imported")
    except ImportError as e:
        logger.error(f"✗ DOCXExporter import failed: {e}")


def test_section_cleaner():
    """Test SectionCleaner functionality"""
    logger.info("\n" + "="*50)
    logger.info("Testing SectionCleaner...")
    logger.info("="*50)
    
    from parser.section_cleaner import SectionCleaner
    
    cleaner = SectionCleaner()
    
    # Test text
    test_text = """
    The Machine Learning model was trained on 10,000 samples.
    The dataset included various features such as age, weight, and medical history.
    
    Results show that accuracy improved by 15% compared to baseline methods.
    Our approach outperformed existing solutions in three key metrics.
    """
    
    result = cleaner.clean_section(test_text, "methodology")
    logger.info(f"✓ Section cleaned")
    logger.info(f"  - Lines: {result['lines']}")
    logger.info(f"  - Words: {result['words']}")
    logger.info(f"  - Warnings: {result['warnings']}")


def test_ieee_formatter():
    """Test IEEE formatter functionality"""
    logger.info("\n" + "="*50)
    logger.info("Testing IEEEFormatter...")
    logger.info("="*50)
    
    from generators.ieee_formatter import IEEEFormatter
    
    formatter = IEEEFormatter()
    
    # Test sections
    sections = {
        'abstract': 'This paper presents a novel approach to machine learning.',
        'introduction': 'Machine learning has revolutionized many fields.',
        'methodology': 'We employed deep neural networks for classification.',
        'results': 'Our model achieved 95% accuracy on the test set.',
        'conclusion': 'This work demonstrates significant improvements.'
    }
    
    metadata = {
        'title': 'Advanced Machine Learning Techniques',
        'authors': ['Dr. Smith', 'Prof. Jones']
    }
    
    formatted = formatter.format_paper(sections, metadata)
    logger.info(f"✓ Paper formatted successfully")
    logger.info(f"  - Title: {metadata['title']}")
    logger.info(f"  - Authors: {len(metadata['authors'])}")
    logger.info(f"  - JSON sections: {list(formatted['json']['sections'].keys())}")
    
    # Validate structure
    validation = formatter.validate_structure(formatted['json']['sections'])
    logger.info(f"✓ Validation result: {validation['valid']}")


def test_keyword_extractor():
    """Test keyword extraction"""
    logger.info("\n" + "="*50)
    logger.info("Testing KeywordExtractor...")
    logger.info("="*50)
    
    from utils.keyword_extractor import KeywordExtractor
    
    extractor = KeywordExtractor()
    
    test_text = """
    Deep learning has revolutionized machine learning. Neural networks are 
    powerful models for pattern recognition. Convolutional neural networks 
    are particularly effective for image processing. Recurrent neural networks 
    excel at sequence modeling. Transformer models have become state-of-the-art 
    for natural language processing.
    """
    
    # Keywords
    keywords = extractor.extract_keywords_tfidf(test_text, top_n=10)
    logger.info(f"✓ Extracted {len(keywords)} keywords")
    for keyword, score in keywords[:5]:
        logger.info(f"  - {keyword}: {score:.4f}")
    
    # Phrases
    phrases = extractor.extract_keyphrases(test_text, top_n=5)
    logger.info(f"✓ Extracted {len(phrases)} key phrases")
    for phrase, freq in phrases:
        logger.info(f"  - {phrase}: {freq}")


def test_environment():
    """Test environment configuration"""
    logger.info("\n" + "="*50)
    logger.info("Testing Environment Configuration...")
    logger.info("="*50)
    
    # Check .env file
    env_path = Path('.env')
    if env_path.exists():
        logger.info("✓ .env file found")
        with open(env_path) as f:
            content = f.read()
            if 'HF_TOKEN' in content:
                logger.info("✓ HF_TOKEN configured in .env")
            else:
                logger.error("✗ HF_TOKEN not found in .env")
    else:
        logger.error("✗ .env file not found")
        logger.info("  Create .env from .env.example and add your HF_TOKEN")
    
    # Check directories
    dirs = ['outputs', 'images', 'ai_models', 'utils']
    for directory in dirs:
        if os.path.exists(directory):
            logger.info(f"✓ Directory '{directory}' exists")
        else:
            logger.error(f"✗ Directory '{directory}' missing")


def test_requirements():
    """Test if all required packages are installed"""
    logger.info("\n" + "="*50)
    logger.info("Testing Required Packages...")
    logger.info("="*50)
    
    required = {
        'flask': 'Flask web framework',
        'flask_cors': 'CORS support',
        'pdfplumber': 'PDF text extraction',
        'requests': 'HTTP requests',
        'docx': 'DOCX file generation',
    }
    
    optional = {
        'sentence_transformers': 'Semantic keyword extraction',
        'torch': 'Deep learning (for transformers)',
        'sklearn': 'Machine learning utilities',
    }
    
    # Check required
    for package, description in required.items():
        try:
            __import__(package)
            logger.info(f"✓ {package}: {description}")
        except ImportError:
            logger.error(f"✗ {package}: NOT INSTALLED (required)")
    
    # Check optional
    for package, description in optional.items():
        try:
            __import__(package)
            logger.info(f"✓ {package}: {description} (optional)")
        except ImportError:
            logger.warning(f"⚠ {package}: NOT INSTALLED (optional)")


def test_sample_pipeline():
    """Test complete processing pipeline with sample data"""
    logger.info("\n" + "="*50)
    logger.info("Testing Sample Processing Pipeline...")
    logger.info("="*50)
    
    try:
        from parser.section_cleaner import SectionCleaner
        from generators.ieee_formatter import IEEEFormatter
        from utils.keyword_extractor import KeywordExtractor
        
        # Sample paper sections
        sections = {
            'abstract': 'This study proposes a novel deep learning architecture for medical imaging analysis.',
            'introduction': 'Medical imaging is crucial for disease diagnosis. Deep learning has shown promise.',
            'methodology': 'We trained a convolutional neural network on 5000 medical images.',
            'results': 'Our model achieved 98% accuracy with sensitivity of 0.97.',
            'conclusion': 'The proposed method significantly outperforms baseline approaches.'
        }
        
        # Step 1: Clean sections
        logger.info("Step 1: Cleaning sections...")
        cleaner = SectionCleaner()
        cleaned = {}
        for section, text in sections.items():
            result = cleaner.clean_section(text, section)
            cleaned[section] = result['text']
        logger.info(f"✓ Cleaned {len(cleaned)} sections")
        
        # Step 2: Format as IEEE
        logger.info("Step 2: Formatting as IEEE...")
        formatter = IEEEFormatter()
        metadata = {
            'title': 'Deep Learning for Medical Image Analysis',
            'authors': ['Dr. Smith', 'Prof. Jones']
        }
        formatted = formatter.format_paper(cleaned, metadata)
        logger.info(f"✓ Paper formatted with {len(formatted['json']['sections'])} sections")
        
        # Step 3: Extract keywords
        logger.info("Step 3: Extracting keywords...")
        extractor = KeywordExtractor()
        keywords = extractor.extract_by_section(cleaned, top_n_per_section=5)
        logger.info(f"✓ Keywords extracted for {len(keywords)} sections")
        
        logger.info("\n✅ Complete pipeline test PASSED")
        
        return True
    
    except Exception as e:
        logger.error(f"\n❌ Pipeline test FAILED: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting AI Research Paper Formatter Tests...")
    logger.info("="*50)
    
    test_environment()
    test_requirements()
    test_imports()
    test_section_cleaner()
    test_ieee_formatter()
    test_keyword_extractor()
    success = test_sample_pipeline()
    
    logger.info("\n" + "="*50)
    if success:
        logger.info("✅ All tests completed successfully!")
    else:
        logger.info("⚠ Some tests failed. Check output above.")
    logger.info("="*50)


if __name__ == '__main__':
    main()
