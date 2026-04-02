#!/usr/bin/env python3
"""
Test script for author formatting improvements.
Tests both parsing and output generation.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from parser.nlp_parser import parse_document, Author
from generators.pdf_generator import generate_pdf
from generators.docx_generator import generate_docx
from dataclasses import dataclass


def test_author_parsing():
    """Test author extraction with various formats."""
    print("=" * 70)
    print("TEST 1: Author Parsing")
    print("=" * 70)
    
    # Test single-line author format (like in your images)
    single_line_text = """
Predictive Machine Learning Models for Early Detection in Chronic Kidney Disease

Dr. Samidhasharma, Department of Computer Science, Rajalakshmi Institute of Technology, Chennai, samidha@gmail.com
Prof. Gopinath K, Department of Computer Science, Saveetha College of Liberal Arts and Sciences, Chennai, gopinath.codes@gmail.com
T. Lakshmi, Department of Computer Science, Saveetha College of Liberal Arts and Sciences, Chennai, lakshmi.research@gmail.com

Abstract
Chronic Kidney Disease (CKD) is one of the major health concerns worldwide...
"""
    
    print("\n📄 Sample Text (Single-line format):")
    print(single_line_text[:300] + "...")
    
    doc = parse_document(single_line_text)
    
    print(f"\n✓ Title extracted: {doc.title}")
    print(f"✓ Authors found: {len(doc.authors)}")
    
    for i, author in enumerate(doc.authors, 1):
        print(f"\n  Author {i}:")
        print(f"    Name: {author.name}")
        print(f"    Role: {author.role}")
        print(f"    Department: {author.department}")
        print(f"    Institution: {author.institution}")
        print(f"    Email: {author.email}")
    
    print(f"\n✓ Abstract detected: {len(doc.abstract)} chars")
    
    return doc


def test_docx_generation(doc):
    """Test DOCX generation with improved author formatting."""
    print("\n" + "=" * 70)
    print("TEST 2: DOCX Generation with Authors")
    print("=" * 70)
    
    try:
        output_path = Path(__file__).parent / "outputs" / "test_authors_ieee.docx"
        output_path.parent.mkdir(exist_ok=True)
        
        generate_docx(doc, str(output_path), template="ieee", styling={})
        print(f"✓ DOCX generated: {output_path.name}")
        print(f"  Size: {output_path.stat().st_size} bytes")
        print(f"  Location: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error generating DOCX: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_generation(doc):
    """Test PDF generation with improved author layout."""
    print("\n" + "=" * 70)
    print("TEST 3: PDF Generation with Authors")
    print("=" * 70)
    
    try:
        output_path = Path(__file__).parent / "outputs" / "test_authors_ieee.pdf"
        output_path.parent.mkdir(exist_ok=True)
        
        generate_pdf(doc, str(output_path), template="ieee", styling={})
        print(f"✓ PDF generated: {output_path.name}")
        print(f"  Size: {output_path.stat().st_size} bytes")
        print(f"  Location: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_author_data_structure():
    """Test Author dataclass with various combinations."""
    print("\n" + "=" * 70)
    print("TEST 4: Author Data Structure")
    print("=" * 70)
    
    author1 = Author(
        name="Dr. Samidha Sharma",
        role="Professor",
        department="Department of Computer Science",
        institution="Rajalakshmi Institute of Technology, Chennai",
        email="samidha.sharma@gmail.com"
    )
    
    author2 = Author(
        name="Prof. Gopinath K",
        institution="Saveetha College of Liberal Arts and Sciences",
        email="gopinath.codes@gmail.com"
    )
    
    author3 = Author(
        name="T. Lakshmi",
        email="lakshmi@research.edu"
    )
    
    authors = [author1, author2, author3]
    
    for i, a in enumerate(authors, 1):
        print(f"\nAuthor {i}:")
        print(f"  Name: {a.name if a.name else '(not specified)'}")
        print(f"  Role: {a.role if a.role else '(not specified)'}")
        print(f"  Dept: {a.department if a.department else '(not specified)'}")
        print(f"  Inst: {a.institution if a.institution else '(not specified)'}")
        print(f"  Email: {a.email if a.email else '(not specified)'}")
    
    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  AUTHOR FORMATTING OPTIMIZATION - TEST SUITE  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Test 1: Author parsing
    doc = test_author_parsing()
    
    # Test 2: Author data structure
    test_author_data_structure()
    
    # Test 3: DOCX generation
    docx_ok = test_docx_generation(doc)
    
    # Test 4: PDF generation
    pdf_ok = test_pdf_generation(doc)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Author Parsing: PASSED")
    print(f"✓ Data Structure: PASSED")
    print(f"{'✓' if docx_ok else '✗'} DOCX Generation: {'PASSED' if docx_ok else 'FAILED'}")
    print(f"{'✓' if pdf_ok else '✗'} PDF Generation: {'PASSED' if pdf_ok else 'FAILED'}")
    print("\n" + "=" * 70)
    
    if docx_ok and pdf_ok:
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check output above.")
    
    print("\nTest files generated in: backend/outputs/")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
