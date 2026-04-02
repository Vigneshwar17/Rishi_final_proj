#!/usr/bin/env python3
"""Check what's in the input PDF"""

import pdfplumber

# Check the one shown in your screenshot
pdf_path = 'outputs/paper_c28a92dc21.pdf'

try:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
        print('=== CONTENT OF paper_c28a92dc21.pdf (8389 bytes) ===')
        print('FULL PAGE TEXT:\n')
        print(text)
        print('\n\n=== LINE-BY-LINE ===')
        lines = text.split('\n')
        for i, line in enumerate(lines[:40]):
            print(f'{i:2d}: {line}')
except Exception as e:
    print(f"Error: {e}")
