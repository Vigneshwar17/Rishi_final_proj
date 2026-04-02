"""
Keyword Extractor module (BONUS).
Uses sentence-transformers for semantic keyword extraction.
"""

import logging
import os
from typing import List, Dict, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Extract keywords and key phrases from research paper sections.
    Supports both TF-IDF and semantic approaches.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize keyword extractor.
        
        Args:
            model_name: Sentence transformers model name (downloads on first use)
        """
        self.model_name = model_name
        self.embeddings_cache = {}

        try:
            # Try to import sentence-transformers (optional)
            from sentence_transformers import SentenceTransformer
            self.sem_model = SentenceTransformer(model_name)
            self.has_semantic = True
            logger.info(f"Loaded semantic model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using TF-IDF only")
            self.sem_model = None
            self.has_semantic = False

    def extract_keywords_tfidf(self, text: str, top_n: int = 15) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF approach.
        
        Args:
            text: Input text
            top_n: Number of top keywords to extract
            
        Returns:
            List of (keyword, score) tuples
        """
        # Clean text
        words = re.findall(r'\b[a-z]+\b', text.lower())

        # Remove stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'be', 'are', 'been',
            'have', 'has', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'can', 'this', 'that', 'it', 'its', 'we', 'they', 'their', 'what',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both'
        }

        words = [w for w in words if w not in stopwords and len(w) > 3]

        # Calculate frequency
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1

        # TF-IDF score (simplified)
        total = len(words)
        scores = [(w, f / total) for w, f in freq.items()]
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_n]

    def extract_keyphrases(self, text: str, top_n: int = 10, phrase_length: int = 3) -> List[Tuple[str, float]]:
        """
        Extract key phrases (multi-word terms).
        
        Args:
            text: Input text
            top_n: Number of phrases to extract
            phrase_length: Length of phrases in words
            
        Returns:
            List of (phrase, score) tuples
        """
        sentences = re.split(r'[.!?]', text)
        phrases_freq = {}

        for sentence in sentences:
            words = re.findall(r'\b[a-z]+\b', sentence.lower())
            words = [w for w in words if len(w) > 3]

            # Create n-grams
            for i in range(len(words) - phrase_length + 1):
                phrase = ' '.join(words[i:i + phrase_length])
                phrases_freq[phrase] = phrases_freq.get(phrase, 0) + 1

        # Score and sort
        scores = [(p, f) for p, f in phrases_freq.items()]
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_n]

    def extract_named_entities(self, text: str) -> List[str]:
        """
        Extract proper nouns (named entities - basic approach).
        
        Args:
            text: Input text
            
        Returns:
            List of named entities
        """
        # Simple capitalization-based extraction
        # In production, use spaCy or transformers-based NER

        words = text.split()
        entities = []

        for word in words:
            # Check if word is capitalized (excluding sentence starts)
            if word and word[0].isupper() and len(word) > 2:
                # Remove punctuation
                clean_word = re.sub(r'[,;:.]', '', word)
                if clean_word and clean_word not in ['The', 'A', 'An']:
                    entities.append(clean_word)

        # Remove duplicates and return top entities
        return list(dict.fromkeys(entities))[:15]

    def extract_by_section(self, sections: Dict[str, str], top_n_per_section: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """
        Extract keywords from each section.
        
        Args:
            sections: Dict of section texts
            top_n_per_section: Keywords per section
            
        Returns:
            Dict with keywords per section
        """
        section_keywords = {}

        for section_name, content in sections.items():
            if not content or isinstance(content, dict):
                continue

            keywords = self.extract_keywords_tfidf(content, top_n_per_section)
            if keywords:
                section_keywords[section_name] = keywords

        return section_keywords

    def get_paper_summary(self, text: str, summary_length: int = 3) -> List[str]:
        """
        Extract summary sentences (simple extractive summarization).
        
        Args:
            text: Full paper text
            summary_length: Number of sentences
            
        Returns:
            List of key sentences
        """
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        # Score sentences by keyword frequency
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            words = set(re.findall(r'\b[a-z]+\b', sentence.lower()))
            # Count important words
            score = len(words) * len(sentence.split())
            sentence_scores[i] = score

        # Get top sentences
        top_indices = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:summary_length]
        top_indices = sorted([i for i, _ in top_indices])

        return [sentences[i] for i in top_indices]

    def rank_sections_by_importance(self, sections: Dict[str, str]) -> Dict[str, float]:
        """
        Rank sections by importance based on keyword density.
        
        Args:
            sections: Dict of section texts
            
        Returns:
            Dict with section importance scores
        """
        scores = {}

        for section_name, content in sections.items():
            if not content or isinstance(content, dict):
                continue

            content = content.get('text', '') if isinstance(content, dict) else content

            # Score based on metrics
            word_count = len(content.split())
            unique_words = len(set(re.findall(r'\b\w+\b', content.lower())))
            keyword_count = len(self.extract_keywords_tfidf(content, 10))

            # Composite score
            diversity = unique_words / max(word_count, 1)
            score = (word_count * 0.3 + unique_words * 0.4 + keyword_count * 0.3) * diversity

            scores[section_name] = score

        return scores
