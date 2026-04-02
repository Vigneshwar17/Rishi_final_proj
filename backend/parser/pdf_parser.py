"""
PDF Parser module using pdfplumber for text extraction.
Handles both standard and complex PDF layouts.
"""

import pdfplumber
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class PDFParser:
    """Extract and structure text from PDF research papers."""

    def __init__(self, max_pages: Optional[int] = None):
        """
        Initialize PDF parser.
        
        Args:
            max_pages: Maximum pages to process (None = all pages)
        """
        self.max_pages = max_pages

    def extract_text(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract raw text from PDF with metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with 'full_text', 'pages', 'metadata'
            
        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF is empty or corrupted
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    raise ValueError("PDF has no pages")

                # Get metadata
                metadata = {
                    'total_pages': len(pdf.pages),
                    'author': pdf.metadata.get('Author', 'Unknown'),
                    'title': pdf.metadata.get('Title', 'Unknown'),
                    'creation_date': str(pdf.metadata.get('CreationDate', 'Unknown')),
                }

                # Extract text from pages
                pages_text = []
                full_text = []
                pages_to_process = self.max_pages or len(pdf.pages)

                for i, page in enumerate(pdf.pages[:pages_to_process]):
                    text = page.extract_text()
                    if text:
                        pages_text.append({
                            'page_num': i + 1,
                            'text': text,
                            'length': len(text)
                        })
                        full_text.append(text)

                if not full_text:
                    raise ValueError("No text could be extracted from PDF")

                combined_text = "\n\n".join(full_text)

                logger.info(f"Extracted {len(full_text)} pages from PDF")

                return {
                    'full_text': combined_text,
                    'pages': pages_text,
                    'metadata': metadata,
                    'success': True
                }

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    def extract_text_with_layout(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text preserving layout (tables, structure).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with preserved layout information
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_with_layout = []

                for i, page in enumerate(pdf.pages[:self.max_pages or len(pdf.pages)]):
                    # Extract text with layout
                    text = page.extract_text()

                    # Try to extract tables
                    tables = page.extract_tables()

                    # Extract text with formatting
                    layout_text = page.extract_text_simple()

                    pages_with_layout.append({
                        'page_num': i + 1,
                        'text': text,
                        'has_tables': len(tables) > 0 if tables else False,
                        'table_count': len(tables) if tables else 0,
                        'layout_preserved': layout_text
                    })

                full_text = "\n\n".join([p['text'] for p in pages_with_layout if p['text']])

                return {
                    'full_text': full_text,
                    'pages_with_layout': pages_with_layout,
                    'success': True
                }

        except Exception as e:
            logger.error(f"Error extracting layout from PDF: {str(e)}")
            raise ValueError(f"Failed to extract layout: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = 1024, overlap: int = 100) -> List[str]:
        """
        Split large text into chunks for processing.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks to preserve context
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks

    def clean_extracted_text(self, text: str) -> str:
        """
        Clean up extracted text (remove extra whitespace, special chars).
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        # Remove multiple newlines
        text = re.sub(r'\n\n+', '\n\n', text)
        # Remove trailing spaces
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        # Remove special characters that break parsing
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        return text.strip()
