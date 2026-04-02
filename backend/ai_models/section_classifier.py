"""
Hugging Face Section Classifier module.
Uses Qwen2.5-72B-Instruct for intelligent section identification.
Identifies and segments sections in research papers using advanced LLM capabilities.
"""

import logging
import os
import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import requests
import time

logger = logging.getLogger(__name__)


class SectionClassifier:
    """
    Classify and identify sections in research papers.
    Uses Hugging Face Inference API with Qwen2.5-72B-Instruct for intelligent classification.
    """

    # Define expected sections in research papers
    PAPER_SECTIONS = [
        "abstract",
        "introduction",
        "methodology",
        "methods",
        "background",
        "literature review",
        "results",
        "findings",
        "discussion",
        "conclusion",
        "conclusions",
        "references",
        "appendix",
        "author information",
        "acknowledgments"
    ]

    # Keywords for section detection (fallback method)
    SECTION_KEYWORDS = {
        'abstract': ['abstract', 'summary'],
        'introduction': ['introduction', 'intro'],
        'methodology': ['methodology', 'methods', 'approach'],
        'background': ['background', 'related work'],
        'literature': ['literature review', 'literature'],
        'results': ['results', 'findings', 'experiments'],
        'discussion': ['discussion', 'analysis'],
        'conclusion': ['conclusion', 'conclusions', 'future work'],
        'references': ['references', 'bibliography', 'works cited'],
        'appendix': ['appendix', 'appendices'],
    }

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize section classifier with Qwen2.5-72B-Instruct.
        
        Args:
            hf_token: Hugging Face API token (uses HF_TOKEN env var if not provided)
            
        Raises:
            ValueError: If no token available
        """
        self.hf_token = hf_token or os.getenv('HF_TOKEN')
        if not self.hf_token:
            raise ValueError("HF_TOKEN not provided and not found in environment")

        self.model_id = "Qwen/Qwen2.5-72B-Instruct"
        # Using Hugging Face Inference API
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}
        self.max_retries = 3
        self.retry_delay = 2

    def _query_hf_api(self, text: str) -> str:
        """
        Query Hugging Face Inference API with Qwen2.5-72B-Instruct.
        
        Args:
            text: Text to classify
            
        Returns:
            Classification result from Qwen
            
        Raises:
            RuntimeError: If API call fails after retries
        """
        # Create prompt for Qwen to classify section
        prompt = f"""Analyze the following text and identify which research paper section it belongs to.
            
Text: "{text[:500]}"

Available sections: {', '.join(self.PAPER_SECTIONS)}

Respond with ONLY the section name that best matches, nothing else."""

        # Format for text generation API
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 20,
                "temperature": 0.3,
                "top_p": 0.9
            }
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    # Extract text from response - handle different response formats
                    if isinstance(result, dict):
                        # Check for generated_text field
                        if 'generated_text' in result:
                            return result['generated_text'].strip().lower()
                        # Check for choices field (OpenAI-like format)
                        elif 'choices' in result and len(result['choices']) > 0:
                            choice = result['choices'][0]
                            if isinstance(choice, dict):
                                if 'generated_text' in choice:
                                    return choice['generated_text'].strip().lower()
                                elif 'message' in choice:
                                    return choice['message'].get('content', '').strip().lower()
                    elif isinstance(result, list) and len(result) > 0:
                        if 'generated_text' in result[0]:
                            return result[0]['generated_text'].strip().lower()
                    return ""
                    
                elif response.status_code == 503:
                    # Model loading
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Model loading, retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise RuntimeError("Model still loading after retries")
                else:
                    raise RuntimeError(f"API error {response.status_code}: {response.text}")

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"API request failed, retrying... ({e})")
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"API connection failed: {str(e)}")

        raise RuntimeError("Failed to connect to Hugging Face API after retries")

    def classify_segments(self, text: str, chunk_size: int = 512) -> Dict[str, any]:
        """
        Classify text segments into paper sections using Qwen2.5-72B-Instruct.
        
        Args:
            text: Full paper text
            chunk_size: Size of segments to classify
            
        Returns:
            Dict with classified sections and confidence scores
        """
        try:
            # Split into paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

            if not paragraphs:
                raise ValueError("No paragraphs found in text")

            classified_sections = {section: [] for section in self.PAPER_SECTIONS}
            unclassified = []

            # Classify each paragraph (limit to first 100 for cost/time efficiency)
            for idx, para in enumerate(paragraphs[:100]):
                # Check for section headers first (fast path)
                section_guess = self._detect_section_header(para)

                if section_guess:
                    classified_sections[section_guess].append({
                        'text': para,
                        'confidence': 0.98,
                        'method': 'header_detection',
                        'para_index': idx
                    })
                else:
                    # Use Qwen for intelligent classification
                    try:
                        result = self._query_hf_api(para)
                        
                        # Find best matching section
                        best_section = None
                        best_score = 0.0
                        
                        result_lower = result.lower().strip()
                        
                        # Exact match check
                        for section in self.PAPER_SECTIONS:
                            if section.lower() in result_lower or result_lower == section.lower():
                                best_section = section
                                best_score = 0.95
                                break
                        
                        # Partial match check if no exact match
                        if not best_section:
                            for section in self.PAPER_SECTIONS:
                                if section.lower() in result_lower:
                                    best_section = section
                                    best_score = 0.85
                                    break
                        
                        # Fallback to keyword detection if Qwen didn't identify
                        if not best_section:
                            best_section = self._detect_section_by_keywords(para)
                            best_score = 0.70 if best_section else 0.0
                        
                        if best_section:
                            classified_sections[best_section].append({
                                'text': para,
                                'confidence': best_score,
                                'method': 'qwen_classification',
                                'para_index': idx,
                                'qwen_output': result
                            })
                        else:
                            unclassified.append({
                                'text': para,
                                'para_index': idx,
                                'qwen_output': result,
                                'method': 'qwen_unclassified'
                            })

                    except Exception as e:
                        logger.warning(f"Qwen classification failed for paragraph {idx}, using fallback: {e}")
                        fb_section = self._detect_section_by_keywords(para)
                        if fb_section:
                            classified_sections[fb_section].append({
                                'text': para,
                                'confidence': 0.60,
                                'method': 'keyword_fallback',
                                'para_index': idx,
                                'error': str(e)
                            })
                        else:
                            unclassified.append({
                                'text': para,
                                'para_index': idx,
                                'error': str(e),
                                'method': 'fallback_failed'
                            })

            # Merge results
            results = {
                'classified_sections': {k: v for k, v in classified_sections.items() if v},
                'unclassified': unclassified,
                'total_paragraphs': len(paragraphs),
                'processed_paragraphs': min(100, len(paragraphs)),
                'model_used': 'Qwen2.5-72B-Instruct',
                'success': True
            }

            logger.info(f"Classified {min(100, len(paragraphs))} paragraphs using Qwen2.5-72B-Instruct")
            return results

        except Exception as e:
            logger.error(f"Error in classify_segments: {str(e)}")
            raise RuntimeError(f"Section classification failed: {str(e)}")

    def _detect_section_header(self, text: str) -> Optional[str]:
        """
        Detect if text is a section header using keyword matching.
        
        Args:
            text: Text to check
            
        Returns:
            Section name if header detected, None otherwise
        """
        text_lower = text.lower().strip()

        # Check if line is short (likely a header)
        if len(text_lower.split()) > 15:
            return None

        # Match against keywords
        for section, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if re.match(rf"^({keyword}|{keyword.upper()})", text_lower, re.IGNORECASE):
                    return section

        return None

    def _detect_section_by_keywords(self, text: str) -> Optional[str]:
        """
        Detect section by keyword matching in text content.
        Used as fallback when Qwen classification fails.
        
        Args:
            text: Text to analyze
            
        Returns:
            Section name if detected, None otherwise
        """
        text_lower = text.lower()
        
        # Score each section based on keyword matches
        section_scores = {}
        for section, keywords in self.SECTION_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                score += text_lower.count(keyword)
            if score > 0:
                section_scores[section] = score
        
        # Return highest scoring section
        if section_scores:
            return max(section_scores, key=section_scores.get)
        
        return None

    def extract_title_and_authors(self, text: str) -> Dict[str, any]:
        """
        Extract title and authors from beginning of paper using Qwen.
        
        Args:
            text: Full paper text
            
        Returns:
            Dict with title and authors
        """
        lines = text.split('\n')
        
        # Get first 50 lines as they usually contain metadata
        metadata_section = "\n".join(lines[:50])
        
        # Extract title (usually first non-empty line or using keyword detection)
        title = None
        title_candidates = [l.strip() for l in lines[:15] if l.strip() and len(l.strip()) > 10]
        
        if title_candidates:
            # Use first substantial line as title
            for candidate in title_candidates:
                if len(candidate) > 20 and len(candidate) < 200:
                    title = candidate
                    break
            
            if not title:
                title = title_candidates[0]

        # Extract emails (more reliable than trying to extract names)
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, metadata_section)
        emails = list(set(emails))  # Remove duplicates

        # Try to extract author names using more sophisticated pattern
        # Looking for patterns like "FirstName LastName" followed by institution or email
        author_names = self._extract_author_names(metadata_section)

        return {
            'title': title,
            'authors': author_names,
            'emails': emails,
            'method': 'combined_extraction',
            'extracted_metadata_chars': len(metadata_section)
        }

    def _extract_author_names(self, text: str) -> List[str]:
        """
        Extract author names from metadata section.
        
        Args:
            text: Metadata section text
            
        Returns:
            List of author names
        """
        authors = []
        
        # Pattern: Name (usually capitalized words before email/institution)
        # This is a fallback - most papers have emails which are more reliable
        name_pattern = r'(?:^|\n)([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:,|\n|@)'
        matches = re.findall(name_pattern, text)
        
        if matches:
            authors = list(set(matches))[:10]  # Limit to 10 unique names
        
        return authors

    def get_section_summary(self, classified: Dict) -> Dict[str, str]:
        """
        Create a summary of classified sections.
        
        Args:
            classified: Classification results
            
        Returns:
            Dict with summary of each section
        """
        summary = {}

        if 'classified_sections' in classified:
            for section, items in classified['classified_sections'].items():
                if items:
                    # Get first paragraph of section as summary
                    first_item = items[0]
                    text_preview = first_item['text'][:150] + "..."
                    summary[section] = text_preview

        return summary
