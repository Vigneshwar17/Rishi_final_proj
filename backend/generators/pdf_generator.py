"""
PDF Generator using ReportLab
Layout:
  Page 1  → Title, Authors, Abstract, Keywords  (single column)
  Page 2+ → Sections, References                (two columns)
"""

import os
import logging
from dataclasses import asdict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Font Name Normaliser
#  ReportLab only accepts its own built-in names.
#  Map common Windows / CSS names → ReportLab equivalents.
# ─────────────────────────────────────────────

_FONT_MAP = {
    # Times family
    "times new roman":  ("Times-Roman", "Times-Bold", "Times-Italic"),
    "times roman":      ("Times-Roman", "Times-Bold", "Times-Italic"),
    "times":            ("Times-Roman", "Times-Bold", "Times-Italic"),
    "georgia":          ("Times-Roman", "Times-Bold", "Times-Italic"),
    # Helvetica / Arial family
    "helvetica":        ("Helvetica",   "Helvetica-Bold", "Helvetica-Oblique"),
    "arial":            ("Helvetica",   "Helvetica-Bold", "Helvetica-Oblique"),
    "calibri":          ("Helvetica",   "Helvetica-Bold", "Helvetica-Oblique"),
    "verdana":          ("Helvetica",   "Helvetica-Bold", "Helvetica-Oblique"),
    "tahoma":           ("Helvetica",   "Helvetica-Bold", "Helvetica-Oblique"),
    "trebuchet ms":     ("Helvetica",   "Helvetica-Bold", "Helvetica-Oblique"),
    # Courier family
    "courier new":      ("Courier",     "Courier-Bold",   "Courier-Oblique"),
    "courier":          ("Courier",     "Courier-Bold",   "Courier-Oblique"),
    "consolas":         ("Courier",     "Courier-Bold",   "Courier-Oblique"),
    "monospace":        ("Courier",     "Courier-Bold",   "Courier-Oblique"),
}

# Already-valid ReportLab font names (pass through unchanged)
_VALID_RL_FONTS = {
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Symbol", "ZapfDingbats",
}


def _normalize_font(name: str) -> tuple:
    """
    Given any font name string, return (regular, bold, italic) ReportLab font names.
    Falls back to Times-Roman family if unknown.
    """
    # Already valid?
    if name in _VALID_RL_FONTS:
        # Derive bold/italic variants from the base name
        base = name.replace("-Bold", "").replace("-Italic", "").replace("-Oblique", "")
        candidates = [f for f in _VALID_RL_FONTS if f.startswith(base)]
        bold = next((f for f in candidates if "Bold" in f and "Italic" not in f and "Oblique" not in f), name)
        italic = next((f for f in candidates if "Italic" in f or "Oblique" in f), name)
        return name, bold, italic

    # Try lookup
    key = name.strip().lower()
    if key in _FONT_MAP:
        return _FONT_MAP[key]

    # Default fallback
    logger.warning(f"Unknown font '{name}', falling back to Times-Roman")
    return "Times-Roman", "Times-Bold", "Times-Italic"


def _safe_text(text: str) -> str:
    """Strip control characters that crash ReportLab's XML parser."""
    import re
    # Remove non-printable control chars except newline/tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Escape bare ampersands that aren't already XML entities
    text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+);)', '&amp;', text)
    return text


def _safe_para(text: str, style) -> "Paragraph":
    """Create a Paragraph, falling back to plain text if XML parse fails."""
    try:
        return Paragraph(_safe_text(text), style)
    except Exception:
        # Strip all tags and retry as plain text
        import re
        plain = re.sub(r'<[^>]+>', '', text)
        return Paragraph(_safe_text(plain), style)


# ─────────────────────────────────────────────
#  Template Configurations
# ─────────────────────────────────────────────

TEMPLATE_CONFIGS = {
    "ieee": {
        "pagesize": letter,
        "title_size": 20,
        "body_size": 10,
        "author_size": 12,
        "heading_size": 11,
        "font_family": "Times-Roman",
        "font_bold": "Times-Bold",
        "font_italic": "Times-Italic",
        "margins": (0.75 * inch, 1 * inch, 0.75 * inch, 1 * inch),  # L R T B
        "col_gap": 0.25 * inch,
    },
    "springer": {
        "pagesize": A4,
        "title_size": 22,
        "body_size": 10,
        "author_size": 12,
        "heading_size": 12,
        "font_family": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "margins": (1 * inch, 1 * inch, 1 * inch, 1 * inch),
        "col_gap": 0.3 * inch,
    },
    "acm": {
        "pagesize": letter,
        "title_size": 18,
        "body_size": 9,
        "author_size": 11,
        "heading_size": 10,
        "font_family": "Helvetica",
        "font_bold": "Helvetica-Bold",
        "font_italic": "Helvetica-Oblique",
        "margins": (0.75 * inch, 0.75 * inch, 1 * inch, 1 * inch),
        "col_gap": 0.2 * inch,
    },
}


def generate_pdf(doc_data, output_path: str, template: str = "ieee", styling: dict = None) -> str:
    """
    Generate a formatted academic PDF.
    Returns the output path.
    """
    styling = styling or {}
    cfg = TEMPLATE_CONFIGS.get(template.lower(), TEMPLATE_CONFIGS["ieee"])

    # Resolve font — normalise user-supplied name to ReportLab built-ins
    raw_font = styling.get("fontFamily", "") or cfg["font_family"]
    font_family, font_bold, font_italic = _normalize_font(raw_font)
    # Patch cfg so decorators / styles use the resolved names
    cfg = dict(cfg)  # don't mutate the module-level dict
    cfg["font_family"] = font_family
    cfg["font_bold"]   = font_bold
    cfg["font_italic"] = font_italic

    title_size  = int(styling.get("titleSize",   cfg["title_size"]))
    body_size   = int(styling.get("bodySize",    cfg["body_size"]))
    line_spacing = float(styling.get("lineSpacing", 1.15))

    page_w, page_h = cfg["pagesize"]
    L, R, T, B = cfg["margins"]
    col_gap = cfg["col_gap"]

    usable_w = page_w - L - R
    col_w = (usable_w - col_gap) / 2

    # ── Page Templates ──────────────────────────────
    # Front page: single wide frame
    front_frame = Frame(
        L, B, usable_w, page_h - T - B,
        id="front", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
    )

    # Body pages: two-column
    left_frame = Frame(
        L, B, col_w, page_h - T - B,
        id="left", leftPadding=0, rightPadding=col_gap / 2, topPadding=0, bottomPadding=0
    )
    right_frame = Frame(
        L + col_w + col_gap, B, col_w, page_h - T - B,
        id="right", leftPadding=col_gap / 2, rightPadding=0, topPadding=0, bottomPadding=0
    )

    front_template = PageTemplate(id="FrontPage", frames=[front_frame], onPage=_make_page_decorator(template, cfg, font_family))
    body_template = PageTemplate(id="BodyPage", frames=[left_frame, right_frame], onPage=_make_page_decorator(template, cfg, font_family))

    doc = BaseDocTemplate(
        output_path,
        pagesize=cfg["pagesize"],
        leftMargin=L, rightMargin=R, topMargin=T, bottomMargin=B,
        pageTemplates=[front_template, body_template],
    )

    # ── Styles ──────────────────────────────────────
    styles = _build_styles(cfg, font_family, title_size, body_size, line_spacing)

    # ── Build Story ──────────────────────────────────
    story = []
    story.append(NextPageTemplate("FrontPage"))

    # Title
    title_text = doc_data.title or "Untitled Document"
    story.append(Spacer(1, 0.2 * inch))
    story.append(_safe_para(title_text, styles["title"]))

    # Authors — multi-column grid (one column per author)
    if doc_data.authors:
        story.append(Spacer(1, 6))
        story.append(_build_author_table(doc_data.authors, styles, usable_w))

    # Abstract
    if doc_data.abstract:
        story.append(Spacer(1, 6))
        story.append(_safe_para("Abstract", styles["section_heading"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray))
        story.append(Spacer(1, 2))
        story.append(_safe_para(doc_data.abstract, styles["body"]))

    # Keywords
    if doc_data.keywords:
        story.append(Spacer(1, 4))
        kw_text = "<b>Keywords:</b> " + _safe_text(", ".join(doc_data.keywords))
        story.append(_safe_para(kw_text, styles["body"]))

    # Warnings for missing sections
    if doc_data.missing_sections:
        story.append(Spacer(1, 4))
        warn_text = "<b>Missing Sections:</b> " + ", ".join(doc_data.missing_sections)
        story.append(_safe_para(warn_text, styles["warning"]))

    # Switch to two-column layout
    story.append(NextPageTemplate("BodyPage"))
    story.append(PageBreak())

    # Sections
    for section in doc_data.sections:
        story.append(_safe_para(section.heading, styles["section_heading"]))
        story.append(Spacer(1, 2))
        for para in section.paragraphs:
            if para.strip():
                story.append(_safe_para(para, styles["body"]))
        for eq in section.equations:
            story.append(_safe_para(eq, styles["equation"]))
        story.append(Spacer(1, 4))

    # References
    if doc_data.references:
        story.append(_safe_para("References", styles["section_heading"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray))
        story.append(Spacer(1, 2))
        for i, ref in enumerate(doc_data.references, 1):
            story.append(_safe_para(f"[{i}] {_safe_text(ref)}", styles["reference"]))

    doc.build(story)
    logger.info(f"PDF generated: {output_path}")
    return output_path


def _make_page_decorator(template_name, cfg, font_family):
    """Returns a page decorator that draws only the page-number footer."""
    def on_page(canvas, doc):
        canvas.saveState()
        page_w, page_h = cfg["pagesize"]
        # Footer: centred page number only — no template label
        canvas.setFont(font_family, 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawCentredString(page_w / 2, 0.4 * inch, str(doc.page))
        canvas.restoreState()
    return on_page


def _build_author_table(authors, styles, usable_w):
    """
    Build a ReportLab Table where each author occupies one column.
    Each cell stacks: Name (bold) / Role / Department / Institution / Email (italic)
    Mirrors the classic academic paper multi-column author block.
    """
    n = len(authors)
    # Cap at 3 columns per row; wrap to multiple rows if needed
    cols_per_row = min(n, 3)
    col_w = usable_w / cols_per_row

    def author_cell(author):
        """Return a list of Paragraph flowables for one author cell."""
        cell = []
        if author.name:
            cell.append(_safe_para(f"<b>{_safe_text(author.name)}</b>", styles["author_cell_name"]))
        if author.role:
            cell.append(_safe_para(_safe_text(author.role), styles["author_cell_body"]))
        if author.department:
            cell.append(_safe_para(_safe_text(author.department), styles["author_cell_body"]))
        if author.institution:
            cell.append(_safe_para(_safe_text(author.institution), styles["author_cell_body"]))
        if author.email:
            cell.append(_safe_para(f"<i>{_safe_text(author.email)}</i>", styles["author_cell_body"]))
        return cell if cell else [Spacer(1, 1)]

    # Split authors into groups of cols_per_row
    rows = []
    for i in range(0, n, cols_per_row):
        group = authors[i : i + cols_per_row]
        # Pad short rows so the table columns stay consistent
        while len(group) < cols_per_row:
            from types import SimpleNamespace
            group.append(SimpleNamespace(name='', role='', department='', institution='', email=''))
        rows.append([author_cell(a) for a in group])

    col_widths = [col_w] * cols_per_row
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        # Thin vertical dividers between authors
        ("LINEBEFORE",    (1, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ]))
    return tbl


def _build_styles(cfg, font_family, title_size, body_size, line_spacing):
    """Build a comprehensive style dictionary."""
    from reportlab.lib.styles import ParagraphStyle

    leading = body_size * line_spacing * 1.2

    styles = {
        "title": ParagraphStyle(
            "title",
            fontName=cfg["font_bold"],
            fontSize=title_size,
            leading=title_size * 1.3,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "authors": ParagraphStyle(
            "authors",
            fontName=cfg["font_italic"],
            fontSize=cfg["author_size"],
            leading=cfg["author_size"] * 1.3,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontName=cfg["font_bold"],
            fontSize=cfg["heading_size"],
            leading=cfg["heading_size"] * 1.4,
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=font_family,
            fontSize=body_size,
            leading=leading,
            alignment=TA_JUSTIFY,
            spaceAfter=2,
        ),
        "reference": ParagraphStyle(
            "reference",
            fontName=font_family,
            fontSize=max(body_size - 1, 7),
            leading=max(body_size - 1, 7) * 1.3,
            alignment=TA_JUSTIFY,
            leftIndent=12,
            firstLineIndent=-12,
            spaceAfter=1,
        ),
        "equation": ParagraphStyle(
            "equation",
            fontName=cfg["font_italic"],
            fontSize=body_size,
            leading=leading,
            alignment=TA_CENTER,
        ),
        "warning": ParagraphStyle(
            "warning",
            fontName=cfg["font_bold"],
            fontSize=body_size,
            leading=leading,
            textColor=colors.HexColor("#c0392b"),
            alignment=TA_LEFT,
        ),
        # ── Author column cell styles ──────────────────────────────
        "author_cell_name": ParagraphStyle(
            "author_cell_name",
            fontName=cfg["font_bold"],
            fontSize=body_size + 1,
            leading=(body_size + 1) * 1.3,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "author_cell_body": ParagraphStyle(
            "author_cell_body",
            fontName=font_family,
            fontSize=body_size - 0.5,
            leading=(body_size - 0.5) * 1.35,
            alignment=TA_CENTER,
            spaceAfter=1,
        ),
    }
    return styles
