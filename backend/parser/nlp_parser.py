"""
Multi-layer NLP Parsing Engine
Converts raw academic text → structured DocumentData

Layer 1: Pattern Detection  (regex + keyword scanning)
Layer 2: Heuristic Rules    (positional, linguistic cues)
Layer 3: Graceful Fallback  (placeholder + warning flags)
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Data Models
# ─────────────────────────────────────────────

@dataclass
class Author:
    name: str = ""
    role: str = ""
    department: str = ""
    institution: str = ""
    email: str = ""


@dataclass
class Figure:
    caption: str = ""
    path: str = ""


@dataclass
class Table:
    caption: str = ""
    rows: list = field(default_factory=list)


@dataclass
class Section:
    heading: str = ""
    paragraphs: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    equations: list = field(default_factory=list)


@dataclass
class DocumentData:
    title: str = ""
    authors: list = field(default_factory=list)
    abstract: str = ""
    keywords: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    references: list = field(default_factory=list)
    missing_sections: list = field(default_factory=list)
    detected_sections: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


# ─────────────────────────────────────────────
#  Regex Patterns
# ─────────────────────────────────────────────

RE_EMAIL = re.compile(r"[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}")
RE_ROMAN_HEADING = re.compile(
    r"^\s*((?:I{1,3}|IV|V?I{0,3}|IX|X{0,3}(?:IX|IV|V?I{0,3}))\.)\s+(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
RE_NUMERIC_HEADING = re.compile(
    r"^\s*(\d+(?:\.\d+)*)\.\s+(.+)$", re.MULTILINE
)
RE_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
RE_ALLCAPS_HEADING = re.compile(r"^([A-Z][A-Z\s\-]{4,})$", re.MULTILINE)
# Abstract: stop at Keywords, Index Terms, first numbered section, or markdown heading
RE_ABSTRACT = re.compile(
    r"(?i)\bAbstract\b[\s\-:—]*\n?(.*?)(?=\n\s*\n\s*(?:Index\s+Terms|Keywords?)|\bKeywords?\b|\bIndex\s+Terms\b|(?:^|\n)\s*\d+\.\s+\S|\bI\.|##|\Z)",
    re.DOTALL,
)
# Keywords: also recognise "Index Terms" (IEEE style) and "Index words"
RE_KEYWORDS = re.compile(
    r"(?i)(?:\bKeywords?\b|\bIndex\s+Terms\b|\bIndex\s+Words\b)[\s:—\-]*(.*?)(?=\n\s*\n|\n\s*\d+\.|\bI\.|\Z)", re.DOTALL
)
RE_REFERENCES_BLOCK = re.compile(
    r"(?i)\b(?:References?|Bibliography)\b[\s:—\-]*\n(.*)", re.DOTALL
)
RE_YEAR_IN_REF = re.compile(r"\b(19|20)\d{2}\b")
RE_AFFILIATION_KEYWORDS = re.compile(
    r"(?i)\b(university|institute|college|department|lab|laboratory|school|faculty|"
    r"center|centre|corp|inc|ltd|technologies|research)\b"
)
# Location/city lines — used to exclude false-positive author names
RE_LOCATION = re.compile(
    r"(?i)\b(india|usa|uk|china|germany|france|canada|australia|japan|korea|"
    r"tamil\s+nadu|karnataka|maharashtra|delhi|mumbai|bangalore|chennai|kolkata|"
    r"hyderabad|pune|new\s+york|california|london|paris|berlin|tokyo)\b"
)
RE_EQUATION = re.compile(
    r"(\$\$.+?\$\$|\$[^$]+?\$|\\begin\{equation\}.*?\\end\{equation\})",
    re.DOTALL,
)


# ─────────────────────────────────────────────
#  Main Parser
# ─────────────────────────────────────────────

class NLPParser:
    """
    Parses raw academic text into a DocumentData structure.
    Uses pattern matching + positional heuristics.
    Does NOT rely on any hardcoded author/title values.
    """

    def parse(self, raw_text: str) -> DocumentData:
        doc = DocumentData()

        if not raw_text or not raw_text.strip():
            doc.warnings.append("Empty input text received.")
            doc.missing_sections = ["title", "abstract", "sections", "references"]
            return doc

        lines = raw_text.splitlines()
        non_empty_lines = [l for l in lines if l.strip()]

        # ── Layer 1+2: Extract each component ──
        doc.abstract, abstract_span = self._extract_abstract(raw_text)
        doc.keywords = self._extract_keywords(raw_text)
        doc.title = self._extract_title(non_empty_lines, raw_text)
        doc.authors = self._extract_authors(raw_text, lines, doc.title)
        doc.sections = self._extract_sections(raw_text)
        doc.references = self._extract_references(raw_text)

        # ── Track detected / missing ──
        doc.detected_sections = self._list_detected(doc)
        doc.missing_sections = self._list_missing(doc)

        # ── Warnings ──
        for m in doc.missing_sections:
            doc.warnings.append(f"Could not detect '{m}' — please review.")

        return doc

    # ─────────────────────────────
    #  Title Extraction
    # ─────────────────────────────
    def _extract_title(self, non_empty_lines: list, raw_text: str) -> str:
        """
        Title = the FIRST short, meaningful line that:
        - Is not an email / URL
        - Is not a section heading (Roman/numeric)
        - Is not a label word (Abstract, Keywords…)
        - Is not a long comma-separated author-style line
        Using the first valid candidate avoids grabbing long author lines.
        """
        for line in non_empty_lines[:12]:
            stripped = line.strip()
            # Strip markdown links before length check
            stripped_plain = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', stripped)
            if len(stripped_plain) < 5:
                continue
            if len(stripped_plain) > 250:      # definitely not a title
                continue
            if RE_EMAIL.search(stripped_plain):
                continue
            if re.match(r'https?://', stripped_plain):
                continue
            if RE_ROMAN_HEADING.match(stripped_plain):
                continue
            if re.match(r'^\d+\.', stripped_plain):
                continue
            if re.match(r'(?i)^(abstract|keywords?|index\s+terms?|introduction|authors?)$', stripped_plain):
                continue
            # Skip single-line author entries (3+ commas with an email somewhere nearby)
            if stripped_plain.count(',') >= 3:
                continue
            # Good title candidate — return immediately (first wins)
            return stripped_plain
        return ""

    # ─────────────────────────────
    #  Author Extraction
    # ─────────────────────────────
    def _extract_authors(self, raw_text: str, lines: list, title: str) -> list:
        """
        Authors typically appear between the title and the abstract.
        Strategy:
          1. Find title line index
          2. Find abstract line index
          3. Parse lines in between for names, emails, affiliations
        """
        title_idx = -1
        abstract_idx = len(lines)

        for i, line in enumerate(lines):
            if title and title[:30].lower() in line.lower():
                title_idx = i
                break

        for i, line in enumerate(lines):
            if re.search(r"(?i)\bAbstract\b", line):
                abstract_idx = i
                break

        author_block = lines[title_idx + 1: abstract_idx]
        return self._parse_author_block(author_block)

    def _parse_author_block(self, lines: list) -> list:
        """
        Supports two author formats:
        FORMAT A (single-line): 'Name, Dept, Institution, City, email'
        FORMAT B (multi-line):  name / dept / institution on separate lines
        """
        # ── Normalise: strip markdown links [text](url) -> text
        clean_lines = []
        for line in lines:
            clean = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', line.strip())
            clean_lines.append(clean)

        # ── Detect single-line format ──────────────────────────────────────
        # A line qualifies if it has >=2 commas AND contains an email
        single_line_entries = [
            l for l in clean_lines
            if l.count(',') >= 2 and RE_EMAIL.search(l)
        ]

        if single_line_entries:
            return self._parse_single_line_authors(single_line_entries)

        # ── Multi-line format (original logic) ────────────────────────────
        return self._parse_multiline_authors(clean_lines)

    def _parse_single_line_authors(self, lines: list) -> list:
        """
        Parse entries like:
          'Monikapreethi S K, Dept CCE, Rajalakshmi Institute, Chennai, India, email@x.com'
        Strategy: split on comma, extract email first, then intelligently classify remaining parts.
        """
        authors = []
        for line in lines:
            if not line.strip():
                continue
            
            parts = [p.strip() for p in line.split(',')]
            author = Author()
            
            # Step 1: Extract email
            email_match = RE_EMAIL.search(line)
            if email_match:
                author.email = email_match.group(0)
            
            # Step 2: Classify each part
            name_candidates = []
            dept_candidates = []
            inst_candidates = []
            role_candidates = []
            
            for part in parts:
                if not part:
                    continue
                if RE_EMAIL.search(part) or author.email and author.email in part:
                    continue  # Skip email part
                
                lower_part = part.lower()
                
                # Skip labels and metadata
                if re.match(r'(?i)^(author|title|abstract|keywords?|index\s+terms?|introduction|mail|email|phone)$', lower_part):
                    continue
                
                # Check what this part is
                if RE_LOCATION.search(part):
                    continue  # Skip locations/cities
                
                if any(kw in lower_part for kw in ['department', 'dept', 'school', 'faculty', 'division']):
                    dept_candidates.append(part)
                elif RE_AFFILIATION_KEYWORDS.search(part):
                    inst_candidates.append(part)
                elif self._looks_like_name(part):
                    # Extract name, separating any role prefix
                    cleaned_name, extracted_role = self._extract_role_from_name(part)
                    if cleaned_name:
                        name_candidates.append(cleaned_name)
                    if extracted_role and not any(kw in lower_part.lower() for kw in ['department', 'dept']):
                        role_candidates.append(extracted_role)
            
            # Step 3: Assign to author fields (prefer first occurrence)
            if name_candidates:
                author.name = self._fix_name_spacing(name_candidates[0])
            if role_candidates:
                author.role = role_candidates[0]
            if dept_candidates:
                author.department = dept_candidates[0]
            if inst_candidates:
                author.institution = inst_candidates[0]

            if author.name or author.email:
                authors.append(author)
        
        return authors
    
    def _extract_role_from_name(self, text: str) -> tuple:
        """
        Extract role prefix from name.
        E.g., "Dr. Samidha Sharma" -> ("Samidha Sharma", "Dr.")
        E.g., "Prof. John Doe" -> ("John Doe", "Prof.")
        """
        role_prefixes = [
            r'^\s*(Dr\.?|Prof\.?|Professor|Dr\.-Ing\.?|Dipl\.?-Ing\.?)\s+',
            r'^\s*(Associate\s+Professor|Assistant\s+Professor|Asst\.?\s+Prof\.?)\s+',
        ]
        
        for pattern in role_prefixes:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                name = text[match.end():].strip()
                return name, role
        
        return text, ""
    
    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a person name."""
        if not text:
            return False
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        if re.search(r'\d', text):
            return False
        if not text[0].isupper():
            return False
        if RE_EMAIL.search(text):
            return False
        if RE_AFFILIATION_KEYWORDS.search(text):
            return False
        return True
    
    def _fix_name_spacing(self, name: str) -> str:
        """
        Fix names with missing spaces.
        E.g., "SamidhaShrama" -> "Samidha Shrama"
        E.g., "Samidhasharma" -> "Samidha Sharma"
        Uses multiple strategies for detecting word boundaries in names.
        """
        if not name or len(name) < 3:
            return name
        
        # Already has spaces?
        if ' ' in name:
            return name
        
        # Strategy 1: CamelCase pattern (lowercase followed by uppercase)
        # E.g., "JohnSmith" -> "John Smith"
        if re.search(r'[a-z][A-Z]', name):
            fixed = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
            return fixed
        
        # Strategy 2: All one case but looks like compound name
        # For names like "Samidhasharma", try common split points
        if name[0].isupper() and len(name) > 5:
            # Common Indian name pattern: first name 5-6 chars, surname 4-6 chars
            # Try splitting at 5 characters first
            candidates = []
            
            # Try typical split points for compound names
            for split_pos in [4, 5, 6, 7]:
                if 2 <= split_pos < len(name) - 1:
                    left = name[:split_pos]
                    right = name[split_pos:]
                    # Both parts should look like valid name segments
                    if left and right and len(left) >= 2 and len(right) >= 2:
                        # Prefer splits that end with typical vowels (a, i)
                        if left.lower().endswith(('a', 'i', 'e')):
                            # Capitalize the second part
                            right_capitalized = right[0].upper() + right[1:] if len(right) > 0 else right
                            candidates.append((split_pos, f"{left} {right_capitalized}"))
            
            # Return the best candidate (prefer longer first name for Indian names)
            if candidates:
                candidates.sort(key=lambda x: -x[0])  # Prefer later splits
                return candidates[0][1]
        
        # Fallback: return as-is
        return name

    def _parse_multiline_authors(self, lines: list) -> list:
        """
        Smart multi-line author block parser with grouping.
        Groups author information based on proximity and email anchors.
        """
        # ── Group lines into author blocks by blank lines ──
        blocks = []
        current_block = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(stripped)
        
        if current_block:
            blocks.append(current_block)
        
        # ── Parse each block into an Author object ──
        authors = []
        
        for block in blocks:
            if not block:
                continue
            
            author = Author()
            
            # Step 1: Extract email (anchor point)
            for line in block:
                email_match = RE_EMAIL.search(line)
                if email_match:
                    author.email = email_match.group(0)
                    break
            
            # Step 2: Extract name, role, department, institution from remaining lines
            for line in block:
                if RE_EMAIL.search(line):
                    continue
                
                lower_line = line.lower()
                
                # Skip labels and metadata
                if re.match(r'(?i)^(author|title|abstract|keywords?|index\s+terms?|introduction|mail|email|phone)$', lower_line):
                    continue
                if RE_LOCATION.search(line):
                    continue
                
                # --- Detect line type ---
                is_role_line = any(kw in lower_line for kw in [
                    'professor', 'dr.', 'dr ', 'dr,',
                    'associate', 'assistant', 'principal', 'investigator', 'researcher',
                    'postdoc', 'phd', 'lecturer', 'faculty', 'scholar'
                ])
                
                is_dept_line = any(kw in lower_line for kw in [
                    'department', 'dept', 'school', 'faculty', 'division', 'lab', 'laboratory'
                ])
                
                is_inst_line = RE_AFFILIATION_KEYWORDS.search(line)
                
                # --- Assign to appropriate field ---
                if is_role_line and not author.role:
                    author.role = line
                elif is_dept_line and not author.department:
                    author.department = line
                elif is_inst_line and not author.institution:
                    author.institution = line
                elif not author.name:
                    # Try to parse as name (proper capitalization, 2-4 words)
                    words = line.split()
                    if (
                        2 <= len(words) <= 4
                        and not RE_EMAIL.search(line)
                        and not re.search(r'\d', line)
                        and line[0].isupper()
                        and not is_role_line
                        and not is_dept_line
                        and not is_inst_line
                    ):
                        author.name = self._fix_name_spacing(line)
            
            # Only add if we have at least a name or email
            if author.name or author.email:
                authors.append(author)
        
        # Fallback: if we got nothing, collect all emails as authors
        if not authors:
            collected_emails = []
            for line in lines:
                emails = RE_EMAIL.findall(line)
                collected_emails.extend(emails)
            
            for email in collected_emails:
                authors.append(Author(email=email))
        
        return authors

    # ─────────────────────────────
    #  Abstract Extraction
    # ─────────────────────────────
    def _extract_abstract(self, text: str) -> tuple:
        match = RE_ABSTRACT.search(text)
        if match:
            abstract_text = match.group(1).strip()
            abstract_text = re.sub(r"\s+", " ", abstract_text)
            return abstract_text, match.span()
        # Fallback: use first long paragraph if no abstract label
        paragraphs = re.split(r"\n\s*\n", text.strip())
        for para in paragraphs[1:4]:
            para = para.strip()
            if len(para) > 150:
                return re.sub(r"\s+", " ", para), (0, 0)
        return "", (0, 0)

    # ─────────────────────────────
    #  Keywords Extraction
    # ─────────────────────────────
    def _extract_keywords(self, text: str) -> list:
        match = RE_KEYWORDS.search(text)
        if match:
            kw_text = match.group(1).strip()
            # Split by common delimiters
            keywords = re.split(r"[;,·—\n]+", kw_text)
            return [k.strip() for k in keywords if k.strip()]
        return []

    # ─────────────────────────────
    #  Section Extraction
    # ─────────────────────────────
    def _extract_sections(self, text: str) -> list:
        """
        Detect section headings via:
          - Roman numerals: I. Introduction
          - Numeric: 1. Introduction / 1.1 Sub-section
          - Markdown: ## Heading
          - ALL CAPS lines
        """
        sections = []
        splits = self._split_by_headings(text)
        for heading, body in splits:
            # Skip sections handled separately: abstract, keywords, references
            # Use substring search so 'IX. REFERENCES' is caught as well as bare 'References'
            if re.search(r'(?i)\b(abstract|keywords?|index\s+terms?|references?|bibliography)\b', heading.strip()):
                continue
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
            equations = RE_EQUATION.findall(body)
            sec = Section(
                heading=heading.strip(),
                paragraphs=paragraphs,
                equations=equations,
            )
            sections.append(sec)
        return sections

    def _split_by_headings(self, text: str) -> list:
        """Returns list of (heading, body) tuples."""
        # Build a unified heading pattern.
        # Subsections like '3.1 Title' (no trailing dot) are also matched.
        heading_pattern = re.compile(
            r"^(?:"
            r"(?:(?:I{1,3}|IV|V?I{0,3}|IX|X{0,3}(?:IX|IV|V?I{0,3}))\.)\s+\S.*"  # Roman: I. II.
            r"|(?:\d+(?:\.\d+)*)\.?\s+[A-Z]\S.*"  # Numeric: 1. Intro OR 3.1 SubSection
            r"|#{1,6}\s+\S.*"                      # Markdown: ## Heading
            r"|[A-Z][A-Z\s\-]{4,}"                 # ALL CAPS
            r")$",
            re.MULTILINE,
        )

        positions = []
        for m in heading_pattern.finditer(text):
            heading_text = m.group().strip()
            # Skip lines that are too long to be headings
            if len(heading_text) > 80:
                continue
            # Skip lines that look like list items inside body (bullet points starting mid-sentence)
            if re.match(r"^\d+\.\s+[a-z]", heading_text):  # '1. lowercase' = list item
                continue
            positions.append((m.start(), m.end(), heading_text))

        if not positions:
            return []

        results = []
        for i, (start, end, heading) in enumerate(positions):
            next_start = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            body = text[end:next_start]
            results.append((heading, body))

        return results

    # ─────────────────────────────
    #  References Extraction
    # ─────────────────────────────
    def _extract_references(self, text: str) -> list:
        match = RE_REFERENCES_BLOCK.search(text)
        if not match:
            return []

        ref_text = match.group(1)
        # Split by numbered references [1], [2] or 1. 2.
        refs = re.split(r"\n\s*(?:\[\d+\]|\d+\.)\s*", ref_text)
        cleaned = []
        for ref in refs:
            ref = re.sub(r"\s+", " ", ref).strip()
            if ref and len(ref) > 10:
                cleaned.append(ref)
        return cleaned

    # ─────────────────────────────
    #  Detected / Missing Tracking
    # ─────────────────────────────
    def _list_detected(self, doc: DocumentData) -> list:
        detected = []
        if doc.title:
            detected.append("title")
        if doc.authors:
            detected.append("authors")
        if doc.abstract:
            detected.append("abstract")
        if doc.keywords:
            detected.append("keywords")
        if doc.sections:
            detected.append(f"sections ({len(doc.sections)})")
        if doc.references:
            detected.append(f"references ({len(doc.references)})")
        return detected

    def _list_missing(self, doc: DocumentData) -> list:
        missing = []
        if not doc.title:
            missing.append("title")
        if not doc.authors:
            missing.append("authors")
        if not doc.abstract:
            missing.append("abstract")
        if not doc.sections:
            missing.append("sections")
        return missing


def parse_document(raw_text: str) -> DocumentData:
    """Public entry point."""
    parser = NLPParser()
    return parser.parse(raw_text)
