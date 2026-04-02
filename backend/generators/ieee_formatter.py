"""
IEEE Formatter module.
Formats extracted and cleaned sections into IEEE-style structure.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IEEEFormatter:
    """Format research paper into IEEE standard style."""

    IEEE_TEMPLATE = """
{title}

{authors}

{abstract}

I. INTRODUCTION
{introduction}

II. METHODOLOGY
{methodology}

III. RESULTS
{results}

IV. CONCLUSION
{conclusion}

REFERENCES
{references}
"""

    def __init__(self):
        """Initialize IEEE formatter."""
        self.formatted_at = None

    def format_paper(self, cleaned_sections: Dict[str, str], metadata: Dict = None) -> Dict[str, any]:
        """
        Format all sections into IEEE-style paper.
        
        Args:
            cleaned_sections: Dict of cleaned section texts
            metadata: Optional metadata (title, authors, etc.)
            
        Returns:
            Dict with formatted paper, JSON, and metadata
        """
        try:
            self.formatted_at = datetime.now().isoformat()

            # Extract or create metadata
            if not metadata:
                metadata = {'title': 'Untitled Paper', 'authors': []}

            # Build structure
            structured = self._structure_sections(cleaned_sections, metadata)

            # Generate formatted text
            formatted_text = self._generate_ieee_text(structured)

            # Generate JSON version
            json_version = self._generate_json_structure(structured)

            return {
                'formatted_text': formatted_text,
                'json': json_version,
                'metadata': metadata,
                'sections_found': list(cleaned_sections.keys()),
                'formatted_at': self.formatted_at,
                'success': True
            }

        except Exception as e:
            logger.error(f"Error formatting paper: {str(e)}")
            raise RuntimeError(f"Paper formatting failed: {str(e)}")

    def _structure_sections(self, cleaned_sections: Dict[str, str], metadata: Dict) -> Dict[str, any]:
        """
        Structure sections into IEEE format.
        
        Args:
            cleaned_sections: Cleaned section texts
            metadata: Paper metadata
            
        Returns:
            Structured paper dict
        """
        structured = {
            'title': metadata.get('title', 'Untitled Paper'),
            'authors': metadata.get('authors', []),
            'abstract': self._get_section(cleaned_sections, 'abstract', 'No abstract provided'),
            'introduction': self._get_section(cleaned_sections, 'introduction', 'No introduction provided'),
            'methodology': self._get_section(cleaned_sections, 'methodology', 
                                            self._get_section(cleaned_sections, 'methods', 'No methodology provided')),
            'results': self._get_section(cleaned_sections, 'results',
                                        self._get_section(cleaned_sections, 'findings', 'No results provided')),
            'discussion': self._get_section(cleaned_sections, 'discussion', ''),
            'conclusion': self._get_section(cleaned_sections, 'conclusion', 'No conclusion provided'),
            'references': self._get_section(cleaned_sections, 'references', 'No references provided'),
            'appendix': self._get_section(cleaned_sections, 'appendix', ''),
        }

        return structured

    def _get_section(self, sections: Dict, key: str, default: str = '') -> str:
        """
        Get section by key, case-insensitive.
        
        Args:
            sections: Sections dict
            key: Section key to find
            default: Default text if not found
            
        Returns:
            Section text or default
        """
        key_lower = key.lower()

        for section_key, content in sections.items():
            if isinstance(content, dict):
                # From cleaned sections with metadata
                content = content.get('text', '')

            if section_key.lower() == key_lower:
                return content

        return default

    def _generate_ieee_text(self, structured: Dict[str, any]) -> str:
        """
        Generate formatted IEEE-style text.
        
        Args:
            structured: Structured paper dict
            
        Returns:
            Formatted text
        """
        lines = []

        # Title
        lines.append(f"{'=' * 80}")
        lines.append(structured['title'].upper())
        lines.append(f"{'=' * 80}")
        lines.append("")

        # Authors
        if structured['authors']:
            lines.append("Authors: " + ", ".join(structured['authors']))
            lines.append("")

        # Abstract
        lines.append("ABSTRACT")
        lines.append("-" * 40)
        lines.append(structured['abstract'])
        lines.append("")

        # Introduction
        lines.append("I. INTRODUCTION")
        lines.append("-" * 40)
        lines.append(structured['introduction'])
        lines.append("")

        # Methodology
        lines.append("II. METHODOLOGY")
        lines.append("-" * 40)
        lines.append(structured['methodology'])
        lines.append("")

        # Results
        lines.append("III. RESULTS")
        lines.append("-" * 40)
        lines.append(structured['results'])
        lines.append("")

        # Discussion
        if structured['discussion']:
            lines.append("IV. DISCUSSION")
            lines.append("-" * 40)
            lines.append(structured['discussion'])
            lines.append("")

        # Conclusion
        lines.append("V. CONCLUSION")
        lines.append("-" * 40)
        lines.append(structured['conclusion'])
        lines.append("")

        # References
        lines.append("REFERENCES")
        lines.append("-" * 40)
        lines.append(structured['references'])
        lines.append("")

        # Appendix
        if structured['appendix']:
            lines.append("APPENDIX")
            lines.append("-" * 40)
            lines.append(structured['appendix'])
            lines.append("")

        return "\n".join(lines)

    def _generate_json_structure(self, structured: Dict[str, any]) -> Dict[str, any]:
        """
        Generate structured JSON version.
        
        Args:
            structured: Structured paper dict
            
        Returns:
            JSON-compatible dict
        """
        return {
            'metadata': {
                'title': structured['title'],
                'authors': structured['authors'],
                'formatted_at': self.formatted_at,
                'format': 'IEEE'
            },
            'sections': {
                'abstract': {
                    'level': 0,
                    'number': None,
                    'content': structured['abstract']
                },
                'introduction': {
                    'level': 1,
                    'number': 'I',
                    'content': structured['introduction']
                },
                'methodology': {
                    'level': 1,
                    'number': 'II',
                    'content': structured['methodology']
                },
                'results': {
                    'level': 1,
                    'number': 'III',
                    'content': structured['results']
                },
                'discussion': {
                    'level': 1,
                    'number': 'IV',
                    'content': structured['discussion'] if structured['discussion'] else None
                },
                'conclusion': {
                    'level': 1,
                    'number': 'V',
                    'content': structured['conclusion']
                },
                'references': {
                    'level': 0,
                    'number': None,
                    'content': structured['references']
                }
            },
            'statistics': {
                'total_words': sum(len(s.split()) for s in [
                    structured['abstract'],
                    structured['introduction'],
                    structured['methodology'],
                    structured['results'],
                    structured['conclusion']
                ]),
                'sections_count': 6,
                'has_references': bool(structured['references']),
                'has_appendix': bool(structured['appendix'])
            }
        }

    def format_to_markdown(self, structured: Dict[str, any]) -> str:
        """
        Format paper as Markdown.
        
        Args:
            structured: Structured paper dict
            
        Returns:
            Markdown formatted text
        """
        lines = []

        # Title
        lines.append(f"# {structured['title']}\n")

        # Authors
        if structured['authors']:
            lines.append(f"**Authors:** {', '.join(structured['authors'])}\n")

        # Abstract
        lines.append("## ABSTRACT\n")
        lines.append(f"{structured['abstract']}\n")

        # Introduction
        lines.append("## I. INTRODUCTION\n")
        lines.append(f"{structured['introduction']}\n")

        # Methodology
        lines.append("## II. METHODOLOGY\n")
        lines.append(f"{structured['methodology']}\n")

        # Results
        lines.append("## III. RESULTS\n")
        lines.append(f"{structured['results']}\n")

        # Discussion
        if structured['discussion']:
            lines.append("## IV. DISCUSSION\n")
            lines.append(f"{structured['discussion']}\n")

        # Conclusion
        lines.append("## V. CONCLUSION\n")
        lines.append(f"{structured['conclusion']}\n")

        # References
        lines.append("## REFERENCES\n")
        lines.append(f"{structured['references']}\n")

        return "".join(lines)

    def validate_structure(self, structured: Dict[str, any]) -> Dict[str, any]:
        """
        Validate the structured paper.
        
        Args:
            structured: Structured paper dict
            
        Returns:
            Validation results
        """
        issues = []
        warnings = []

        # Check required sections
        required = ['abstract', 'introduction', 'methodology', 'results', 'conclusion']
        for section in required:
            content = structured.get(section, '')
            if not content or len(content.strip()) < 50:
                issues.append(f"Missing or incomplete {section} section")

        # Check content length
        intro_len = len(structured.get('introduction', '').split())
        if intro_len < 100:
            warnings.append(f"Introduction is short ({intro_len} words)")

        # Check references
        if not structured.get('references') or 'No references' in structured.get('references', ''):
            warnings.append("No references found")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'structure_complete': len([s for s in required if structured.get(s)]) == len(required)
        }
