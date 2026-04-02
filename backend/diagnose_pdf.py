#!/usr/bin/env python3
"""Diagnostic script to analyze what's in the generated PDF"""

import pdfplumber
import os

pdf_path = 'outputs/test_authors_ieee.pdf'

if os.path.exists(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text()
            print('=== EXTRACTED TEXT FROM PDF (First 2000 chars) ===')
            print(text[:2000])
            print('\n=== LINE BY LINE (First 30 lines) ===')
            lines = text.split('\n')
            for i, line in enumerate(lines[:30]):
                print(f'{i}: {line}')
    except Exception as e:
        print(f"Error reading PDF: {e}")
else:
    print(f"PDF file not found: {pdf_path}")
    print("Available files in outputs/:")
    if os.path.exists('outputs'):
        for f in os.listdir('outputs'):
            print(f"  - {f}")
