#!/usr/bin/env python3
"""
Isolate the import issue step by step.
"""
import os
import sys

print("Step 1: Basic imports")
try:
    import logging
    logger = logging.getLogger(__name__)
    print("  logging OK")
except Exception as e:
    print(f"  logging FAIL: {e}")

print("\nStep 2: Import settings")
try:
    from src.config import settings
    print("  settings OK")
except Exception as e:
    print(f"  settings FAIL: {e}")
    sys.exit(1)

print("\nStep 3: Import pytesseract")
try:
    import pytesseract
    print("  pytesseract OK")
except Exception as e:
    print(f"  pytesseract FAIL: {e}")

print("\nStep 4: Import pdfplumber")
try:
    import pdfplumber
    print("  pdfplumber OK")
except Exception as e:
    print(f"  pdfplumber FAIL: {e}")

print("\nStep 5: Import PIL")
try:
    from PIL import Image
    print("  PIL OK")
except Exception as e:
    print(f"  PIL FAIL: {e}")

print("\nStep 6: Import magic")
try:
    import magic
    print("  magic OK")
except Exception as e:
    print(f"  magic FAIL: {e}")

print("\nStep 7: Import FastAPI UploadFile")
try:
    from fastapi import UploadFile
    print("  UploadFile OK")
except Exception as e:
    print(f"  UploadFile FAIL: {e}")

print("\nStep 8: Create DocumentProcessor class manually")
try:
    # Define a minimal class without imports
    class MinimalDocumentProcessor:
        def __init__(self):
            self.ocr_enabled = False
            print("    Minimal instance created")

    processor = MinimalDocumentProcessor()
    print("  Minimal class OK")
except Exception as e:
    print(f"  Minimal class FAIL: {e}")

print("\n" + "="*60)
print("All basic imports succeeded.")
print("Now trying to import the actual module...")

# Try importing the module with minimal error handling
import importlib
try:
    spec = importlib.util.spec_from_file_location(
        "document_processor",
        os.path.join(os.path.dirname(__file__), "src", "services", "document_processor.py")
    )
    module = importlib.util.module_from_spec(spec)
    # Don't execute the module yet
    print("Module spec created")
except Exception as e:
    print(f"Module spec FAIL: {e}")

print("\nTrying to import with __import__")
try:
    # This will execute module code
    import src.services.document_processor
    print("Module import succeeded!")
except Exception as e:
    print(f"Module import FAIL: {e}")
    import traceback
    traceback.print_exc()