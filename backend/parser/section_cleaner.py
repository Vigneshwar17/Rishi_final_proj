"""
Section Cleaner module.
Cleans and structures extracted sections using regex and rule-based processing.
"""

import re
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class SectionCleaner:
    """Clean and structure research paper sections."""

    # Common OCR artifacts and mistakes
    OCR_ARTIFACTS = {
        r'(?i)ﬁ': 'fi',
        r'(?i)ﬂ': 'fl',
        r'(?i)ﬀ': 'ff',
        r'\x00': '',
        r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]': '',
    }

    # Section name cleanup patterns
    SECTION_PATTERNS = {
        r'^(I+\.?\s+)?ABSTRACT': 'ABSTRACT',
        r'^(I+\.?\s+)?INTRODUCTION': 'I.INTRODUCTION',
        r'^(II+\.?\s+)?METHODOLOGY': 'II.METHODOLOGY',
        r'^(II+\.?\s+)?METHODS': 'II.METHODOLOGY',
        r'^(III+\.?\s+)?RESULTS': 'III.RESULTS',
        r'^(III+\.?\s+)?FINDINGS': 'III.RESULTS',
        r'^(IV+\.?\s+)?DISCUSSION': 'IV.DISCUSSION',
        r'^(V+\.?\s+)?CONCLUSION': 'V.CONCLUSION',
        r'^(VI+\.?\s+)?REFERENCES': 'REFERENCES',
    }

    def __init__(self):
        """Initialize section cleaner."""
        self.compiled_ocr = {re.compile(k, re.IGNORECASE): v for k, v in self.OCR_ARTIFACTS.items()}
        self.compiled_sections = {re.compile(k, re.IGNORECASE): v for k, v in self.SECTION_PATTERNS.items()}

    def clean_section(self, section_text: str, section_name: str = None) -> Dict[str, any]:
        """
        Clean a single section.
        
        Args:
            section_text: Raw section text
            section_name: Name of section (optional)
            
        Returns:
            Dict with cleaned text and metadata
        """
        if not section_text or not section_text.strip():
            return {
                'text': '',
                'cleaned': True,
                'lines': 0,
                'words': 0,
                'warnings': ['Empty section']
            }

        cleaned = section_text

        # Remove OCR artifacts
        for pattern, replacement in self.compiled_ocr.items():
            cleaned = pattern.sub(replacement, cleaned)

        # Remove header/footer artifacts (page numbers, running heads)
        cleaned = self._remove_header_footer(cleaned)

        # Normalize whitespace
        cleaned = self._normalize_whitespace(cleaned)

        # Remove citation artifacts
        cleaned = self._clean_citations(cleaned)

        # Split into paragraphs and validate
        paragraphs = [p.strip() for p in cleaned.split('\n\n') if p.strip()]

        # Remove very short lines that are likely artifacts
        paragraphs = [p for p in paragraphs if len(p.split()) > 3]

        cleaned_text = '\n\n'.join(paragraphs)

        return {
            'text': cleaned_text,
            'cleaned': True,
            'lines': len(paragraphs),
            'words': len(cleaned_text.split()),
            'characters': len(cleaned_text),
            'warnings': self._validate_section(cleaned_text, section_name)
        }

    def _remove_header_footer(self, text: str) -> str:
        """Remove page headers and footers."""
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip lines that look like page numbers
            if re.match(r'^\s*(\d+|Page\s+\d+)\s*$', line, re.IGNORECASE):
                continue
            # Skip very short lines that might be headers
            if len(line.strip()) < 5 and line.isupper():
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize spaces and newlines."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n\n+', '\n\n', text)
        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))

        return text.strip()

    def _clean_citations(self, text: str) -> str:
        """Clean up citation formatting."""
        # Fix common citation patterns: [1] [2] etc
        text = re.sub(r'\[\s+(\d+)\s+\]', r'[\1]', text)
        # Fix space before citations: word [1] -> word[1]
        text = re.sub(r'(\w)\s+\[', r'\1[', text)

        return text

    def _validate_section(self, text: str, section_name: str = None) -> List[str]:
        """
        Validate section for common issues.
        
        Args:
            text: Section text to validate
            section_name: Name of section
            
        Returns:
            List of warning messages
        """
        warnings = []

        if not text or len(text.strip()) == 0:
            warnings.append("Empty section after cleaning")

        if len(text.split()) < 50:
            warnings.append("Very short section (less than 50 words)")

        # Check for common OCR issues
        if any(char in text for char in ['|', '1', '0'] * 3):
            if re.search(r'[|10]{3,}', text):
                warnings.append("Possible OCR corruption detected")

        # Abstract should be shorter than methodology
        if section_name and section_name.lower() == 'abstract':
            if len(text.split()) > 500:
                warnings.append("Abstract seems too long")

        return warnings

    def clean_all_sections(self, classified_sections: Dict) -> Dict[str, any]:
        """
        Clean all sections from classification results.
        
        Args:
            classified_sections: Dict of classified sections
            
        Returns:
            Dict with cleaned sections
        """
        cleaned = {}
        stats = defaultdict(lambda: {'count': 0, 'total_words': 0, 'warnings': []})

        for section_name, items in classified_sections.items():
            if not items:
                continue

            # Combine all items in section
            combined_text = '\n\n'.join([item['text'] for item in items])

            # Clean the section
            cleaned_result = self.clean_section(combined_text, section_name)
            cleaned[section_name] = cleaned_result

            # Collect stats
            stats[section_name]['count'] = len(items)
            stats[section_name]['total_words'] = cleaned_result['words']
            stats[section_name]['warnings'] = cleaned_result['warnings']

        return {
            'cleaned_sections': cleaned,
            'statistics': dict(stats),
            'total_sections': len(cleaned),
            'success': True
        }

    def standardize_section_names(self, sections: Dict[str, str]) -> Dict[str, str]:
        """
        Standardize section names to IEEE format.
        
        Args:
            sections: Dict of sections with arbitrary names
            
        Returns:
            Dict with standardized section names
        """
        standardized = {}

        for section_name, content in sections.items():
            # Try to match against patterns
            matched_name = section_name
            for pattern, standard_name in self.compiled_sections.items():
                if pattern.search(section_name):
                    matched_name = standard_name
                    break

            standardized[matched_name] = content

        return standardized

    def extract_keywords_from_section(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Extract important keywords from section text.
        
        Args:
            text: Section text
            top_n: Number of top keywords to extract
            
        Returns:
            List of (keyword, frequency) tuples
        """
        # Remove citations and references
        text = re.sub(r'\[\d+\]', '', text)
        # Remove common words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'be', 'are', 'been',
            'have', 'has', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'can', 'this', 'that', 'these', 'those', 'which', 'who', 'what', 'where',
            'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'also', 'also', 'used', 'using'
        }

        # Tokenize and filter
        words = re.findall(r'\b[a-z]+\b', text.lower())
        words = [w for w in words if w not in common_words and len(w) > 3]

        # Count frequency
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return sorted_words[:top_n]

    def merge_sections(self, sections: Dict[str, str]) -> str:
        """
        Merge cleaned sections into final document.
        
        Args:
            sections: Dict of cleaned sections
            
        Returns:
            Merged document text
        """
        # Define section order
        section_order = [
            'ABSTRACT',
            'I.INTRODUCTION',
            'II.METHODOLOGY',
            'III.RESULTS',
            'IV.DISCUSSION',
            'V.CONCLUSION',
            'REFERENCES'
        ]

        merged = []

        for section_name in section_order:
            if section_name in sections:
                merged.append(f"\n{section_name}\n")
                merged.append(sections[section_name])
                merged.append("\n")

        # Add any remaining sections
        for section_name, content in sections.items():
            if section_name not in section_order:
                merged.append(f"\n{section_name}\n")
                merged.append(content)
                merged.append("\n")

        return "".join(merged).strip()
