"""
Flask Backend - AI Research Paper Formatter
POST /process  → parse + generate document
POST /ai/analyze → AI-based paper analysis using Hugging Face
POST /ai/export → Export formatted paper (DOCX/PDF)
GET  /download/<filename> → serve generated file
GET  /health   → health check
"""

import os
import uuid
import logging
import traceback
import json
from dataclasses import asdict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Internal modules
from utils.file_extractor import extract_from_file, extract_from_text
from parser.nlp_parser import parse_document, Author
from generators.pdf_generator import generate_pdf
from generators.docx_generator import generate_docx

# AI-based modules
from parser.pdf_parser import PDFParser
from ai_models.section_classifier import SectionClassifier
from parser.section_cleaner import SectionCleaner
from generators.ieee_formatter import IEEEFormatter
from generators.docx_exporter import DOCXExporter
from utils.keyword_extractor import KeywordExtractor

# ─────────────────────────────────────────────
#  Setup
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app, origins="*")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def serialize_doc(doc_data) -> dict:
    """Convert DocumentData to a JSON-serialisable dict."""
    def _ser(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _ser(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [_ser(i) for i in obj]
        else:
            return obj

    return _ser(doc_data)


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "AI Research Paper Formatter is running."})


@app.route("/process", methods=["POST"])
def process():
    """
    Expected multipart/form-data fields:
      file       – uploaded file (optional)
      text       – raw text input (optional, used if no file)
      authors    – JSON array of author objects (optional, overrides extraction)
      template   – ieee | springer | acm  (default: ieee)
      format     – pdf | docx             (default: pdf)
      fontFamily – font family name       (optional)
      titleSize  – integer pt             (optional)
      bodySize   – integer pt             (optional)
      lineSpacing – float                 (optional)
    """
    try:
        # ── 1. Gather inputs ────────────────────────────────
        template = request.form.get("template", "ieee").lower()
        output_format = request.form.get("format", "pdf").lower()

        styling = {
            "fontFamily": request.form.get("fontFamily", ""),
            "titleSize": request.form.get("titleSize", ""),
            "bodySize": request.form.get("bodySize", ""),
            "lineSpacing": request.form.get("lineSpacing", ""),
        }
        # Remove empty styling values so generators use defaults
        styling = {k: v for k, v in styling.items() if v}

        # ── 1.5. Parse optional authors from frontend ────────
        manual_authors = []
        try:
            authors_json = request.form.get("authors", "")
            if authors_json:
                manual_authors = json.loads(authors_json)
                logger.info(f"Received {len(manual_authors)} manual authors from frontend")
        except json.JSONDecodeError:
            logger.warning("Failed to parse authors JSON, will use extraction")

        # ── 2. Extract raw text ──────────────────────────────
        raw_text = ""
        extraction_error = None

        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if not allowed_file(file.filename):
                return jsonify({"success": False, "error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
            result = extract_from_file(file)
            raw_text = result["text"]
            extraction_error = result.get("error")
        elif request.form.get("text", "").strip():
            raw_text = request.form.get("text", "").strip()
        else:
            return jsonify({"success": False, "error": "No input provided. Upload a file or paste text."}), 400

        if not raw_text.strip():
            return jsonify({"success": False, "error": "No readable text found in the input."}), 400

        # ── 3. Parse ──────────────────────────────────────────
        logger.info(f"Parsing document | template={template} | format={output_format}")
        doc_data = parse_document(raw_text)

        # ── 3.5. Override authors with manual input ──────────
        if manual_authors:
            doc_data.authors = [
                Author(
                    name=a.get("name", ""),
                    email=a.get("email", ""),
                    role=a.get("role", ""),
                    department=a.get("department", ""),
                    institution=a.get("institution", "")
                )
                for a in manual_authors
            ]
            logger.info(f"Overrode authors with manual input | count={len(doc_data.authors)}")

        # ── 4. Generate output file ──────────────────────────
        uid = uuid.uuid4().hex[:10]
        if output_format == "docx":
            filename = f"paper_{uid}.docx"
            out_path = os.path.join(OUTPUTS_DIR, filename)
            generate_docx(doc_data, out_path, template=template, styling=styling)
        else:
            filename = f"paper_{uid}.pdf"
            out_path = os.path.join(OUTPUTS_DIR, filename)
            generate_pdf(doc_data, out_path, template=template, styling=styling)

        # ── 5. Build response ────────────────────────────────
        response = {
            "success": True,
            "detected_sections": doc_data.detected_sections,
            "missing_sections": doc_data.missing_sections,
            "warnings": doc_data.warnings,
            "document": {
                "title": doc_data.title,
                "authors": [
                    {
                        "name": a.name,
                        "email": a.email,
                        "institution": a.institution,
                        "department": a.department,
                        "role": a.role,
                    }
                    for a in doc_data.authors
                ],
                "abstract": doc_data.abstract[:400] + ("..." if len(doc_data.abstract) > 400 else ""),
                "keywords": doc_data.keywords,
                "section_count": len(doc_data.sections),
                "reference_count": len(doc_data.references),
                "sections": [
                    {"heading": s.heading, "paragraph_count": len(s.paragraphs)}
                    for s in doc_data.sections
                ],
            },
            "download_url": f"/download/{filename}",
            "filename": filename,
            "extraction_error": extraction_error,
        }

        logger.info(f"Document generated: {filename}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Processing error: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/ai/analyze", methods=["POST"])
def ai_analyze():
    """
    AI-based paper analysis using Hugging Face.
    Extracts sections, cleans text, and formats using IEEE style.
    
    Request:
        - file: PDF file upload (required)
        - extract_keywords: boolean (optional, default: true)
    
    Response:
        - formatted_text: IEEE formatted paper
        - json: Structured JSON version
        - sections: Dict of extracted sections
        - keywords: Extracted keywords per section
        - statistics: Analysis statistics
    """
    try:
        if "file" not in request.files or not request.files["file"].filename:
            return jsonify({"success": False, "error": "No PDF file provided"}), 400

        file = request.files["file"]
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Only PDF files supported for AI analysis"}), 400

        # ── 1. Save uploaded file ────────────────────────────
        temp_path = os.path.join(OUTPUTS_DIR, f"temp_{uuid.uuid4().hex}.pdf")
        file.save(temp_path)

        try:
            # ── 2. Extract text from PDF ─────────────────────
            logger.info(f"Extracting text from PDF: {file.filename}")
            pdf_parser = PDFParser(max_pages=None)
            extraction_result = pdf_parser.extract_text(temp_path)
            full_text = extraction_result['full_text']

            # ── 3. Classify sections using HF API ────────────
            logger.info("Classifying sections with Hugging Face...")
            classifier = SectionClassifier()
            classified = classifier.classify_segments(full_text)
            
            # Extract title and authors
            title_authors = classifier.extract_title_and_authors(full_text)

            # ── 4. Clean sections ────────────────────────────
            logger.info("Cleaning and normalizing sections...")
            cleaner = SectionCleaner()
            cleaned_result = cleaner.clean_all_sections(classified['classified_sections'])
            cleaned_sections = {
                section: item['text'] 
                for section, item in cleaned_result['cleaned_sections'].items()
            }

            # ── 5. Format as IEEE standard ───────────────────
            logger.info("Formatting as IEEE standard...")
            formatter = IEEEFormatter()
            metadata = {
                'title': title_authors.get('title', 'Untitled Paper'),
                'authors': title_authors.get('authors', [])
            }
            formatted = formatter.format_paper(cleaned_sections, metadata)

            # ── 6. Extract keywords (bonus) ──────────────────
            extract_keywords = request.form.get('extract_keywords', 'true').lower() == 'true'
            keywords = {}
            if extract_keywords:
                logger.info("Extracting keywords...")
                keyword_extractor = KeywordExtractor()
                keywords = keyword_extractor.extract_by_section(cleaned_sections, top_n_per_section=10)

            # ── 7. Build response ────────────────────────────
            response = {
                'success': True,
                'metadata': {
                    'title': metadata['title'],
                    'authors': metadata['authors'],
                    'total_pages': extraction_result['metadata']['total_pages'],
                    'file_name': secure_filename(file.filename)
                },
                'sections_found': list(cleaned_sections.keys()),
                'formatted_text': formatted['formatted_text'],
                'json': formatted['json'],
                'keywords': keywords,
                'statistics': {
                    'total_words': formatted['json']['statistics']['total_words'],
                    'sections_count': formatted['json']['statistics']['sections_count'],
                    'has_references': formatted['json']['statistics']['has_references'],
                    'has_appendix': formatted['json']['statistics']['has_appendix']
                },
                'validation': formatter.validate_structure(formatted['json']['sections'])
            }

            logger.info(f"AI analysis completed successfully")
            return jsonify(response), 200

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"success": False, "error": f"Invalid input: {str(e)}"}), 400
    except RuntimeError as e:
        logger.error(f"Runtime error: {str(e)}")
        if "HF_TOKEN" in str(e):
            return jsonify({"success": False, "error": "Hugging Face API token not configured"}), 500
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"AI analysis error: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/ai/export", methods=["POST"])
def ai_export():
    """
    Export structured paper to DOCX or PDF.
    
    Request:
        - json_data: Structured JSON from /ai/analyze (required)
        - format: 'docx' or 'pdf' (default: 'docx')
    
    Response:
        - download_url: URL to download file
        - filename: Generated filename
    """
    try:
        json_str = request.form.get('json_data', '{}')
        export_format = request.form.get('format', 'docx').lower()

        if export_format not in ['docx', 'pdf']:
            return jsonify({"success": False, "error": "Format must be 'docx' or 'pdf'"}), 400

        # Parse structured data
        structured = json.loads(json_str)

        # Reconstruct structured dict for formatter
        structured_paper = {
            'title': structured.get('metadata', {}).get('title', 'Untitled'),
            'authors': structured.get('metadata', {}).get('authors', []),
            'abstract': structured.get('sections', {}).get('abstract', {}).get('content', ''),
            'introduction': structured.get('sections', {}).get('introduction', {}).get('content', ''),
            'methodology': structured.get('sections', {}).get('methodology', {}).get('content', ''),
            'results': structured.get('sections', {}).get('results', {}).get('content', ''),
            'discussion': structured.get('sections', {}).get('discussion', {}).get('content', '') or '',
            'conclusion': structured.get('sections', {}).get('conclusion', {}).get('content', ''),
            'references': structured.get('sections', {}).get('references', {}).get('content', ''),
            'appendix': ''
        }

        uid = uuid.uuid4().hex[:10]

        if export_format == 'docx':
            filename = f"paper_{uid}.docx"
            output_path = os.path.join(OUTPUTS_DIR, filename)
            exporter = DOCXExporter()
            result = exporter.export_paper(structured_paper, output_path)
            
            if not result.get('success'):
                return jsonify({"success": False, "error": result.get('error', 'Export failed')}), 500
        else:
            filename = f"paper_{uid}.pdf"
            output_path = os.path.join(OUTPUTS_DIR, filename)
            # Use existing PDF generator
            from generators.pdf_generator import PDFGenerator
            pgen = PDFGenerator()
            try:
                pgen.generate(structured_paper, output_path, template='ieee')
                result = {'success': True, 'path': output_path}
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        return jsonify({
            'success': True,
            'format': export_format,
            'filename': filename,
            'download_url': f"/download/{filename}",
            'file_size': result.get('file_size', 'Unknown')
        }), 200

    except json.JSONDecodeError:
        return jsonify({"success": False, "error": "Invalid JSON data"}), 400
    except Exception as e:
        logger.error(f"Export error: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    """Serve a generated file for download."""
    safe_name = secure_filename(filename)
    return send_from_directory(OUTPUTS_DIR, safe_name, as_attachment=True)


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
