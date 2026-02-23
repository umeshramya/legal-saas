#!/usr/bin/env python3
"""
Minimal test to isolate DocumentProcessor import issue.
"""
import os
import sys
import logging

# Disable logging
logging.disable(logging.CRITICAL)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Test 1: Import settings")
try:
    from src.config import settings
    print("  OK: settings imported")
except Exception as e:
    print(f"  FAIL settings import failed: {e}")
    sys.exit(1)

print("\nTest 2: Import pytesseract")
try:
    import pytesseract
    print(f"  OK pytesseract imported, tesseract_cmd: {getattr(pytesseract.pytesseract, 'tesseract_cmd', 'NOT SET')}")
except Exception as e:
    print(f"  FAIL pytesseract import failed: {e}")

print("\nTest 3: Import DocumentProcessor class")
try:
    from src.services.document_processor import DocumentProcessor
    print("  OK DocumentProcessor class imported")
except Exception as e:
    print(f"  FAIL DocumentProcessor import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTest 4: Create DocumentProcessor instance")
try:
    # Temporarily disable OCR to avoid tesseract issues
    os.environ['OCR_ENABLED'] = 'false'

    processor = DocumentProcessor()
    print(f"  OK DocumentProcessor created, ocr_enabled={processor.ocr_enabled}")

    # Test a method
    text = "Test legal document text"
    keywords = processor.extract_keywords(text)
    print(f"  OK Keyword extraction works: {keywords}")

except Exception as e:
    print(f"  FAIL DocumentProcessor creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("All tests passed!")
print("DocumentProcessor works correctly (OCR disabled).")