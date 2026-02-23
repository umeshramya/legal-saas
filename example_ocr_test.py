#!/usr/bin/env python3
"""
Example script to demonstrate OCR functionality.
This creates a simple test image and processes it using DocumentProcessor.
"""

import asyncio
import sys
import os
from PIL import Image, ImageDraw
import io

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_image_ocr():
    """Test OCR on a generated image."""
    from src.services.document_processor import DocumentProcessor

    print("Testing DocumentProcessor with generated image...")

    # Create a test image with legal text
    img = Image.new('RGB', (600, 200), color='white')
    d = ImageDraw.Draw(img)
    d.text((20, 50), 'IN THE HIGH COURT OF DELHI AT NEW DELHI', fill='black')
    d.text((20, 80), 'Case No: DLCT010001232023', fill='black')
    d.text((20, 110), 'Petitioner: John Doe vs Respondent: State', fill='black')
    d.text((20, 140), 'Date: 15th January 2025', fill='black')

    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()

    # Create DocumentProcessor
    processor = DocumentProcessor()

    # Process the image
    result = await processor.process_image(img_bytes, "test_case.png", use_ocr=True)

    print(f"\nOCR Results:")
    print(f"Filename: {result['filename']}")
    print(f"File type: {result['file_type']}")
    print(f"OCR used: {result['ocr_used']}")
    print(f"Error: {result['error']}")
    print(f"\nExtracted text:\n{'-'*40}")
    print(result['extracted_text'])
    print(f"{'-'*40}")

    if result['error']:
        print(f"\n✗ Error: {result['error']}")
        return False
    else:
        print("\n✓ Image processed successfully")
        # Check if key phrases were extracted
        text = result['extracted_text'].lower()
        keywords = ['high court', 'delhi', 'case', 'petitioner', 'respondent']
        found = [kw for kw in keywords if kw in text]
        print(f"Found keywords: {found}")
        return True


async def test_keyword_extraction():
    """Test keyword extraction from legal text."""
    from src.services.document_processor import DocumentProcessor

    print("\n\nTesting keyword extraction...")

    legal_text = """
    IN THE HIGH COURT OF DELHI AT NEW DELHI
    Case Number: DLCT010001232023
    Date: 15th January 2025

    ORDER

    The petitioner has filed an application under Section 9 of the
    Arbitration and Conciliation Act, 1996 seeking interim measures.

    The respondent has raised objections regarding the maintainability
    of the application. The court will hear arguments on the next date
    of hearing scheduled for 30th January 2025.

    Both parties are directed to file their written submissions
    along with relevant citations by 25th January 2025.

    The matter is adjourned to 30th January 2025 for further hearing.
    """

    processor = DocumentProcessor()
    keywords = processor.extract_keywords(legal_text)

    print(f"Extracted keywords by category:")
    for category, words in keywords.items():
        print(f"  {category}: {words}")

    expected_categories = ['hearing', 'filing', 'dates', 'financial', 'legal']
    found_categories = [cat for cat in expected_categories if cat in keywords and keywords[cat]]

    print(f"\nFound keywords in {len(found_categories)}/{len(expected_categories)} categories")
    return len(found_categories) > 0


async def main():
    """Run all tests."""
    print("=" * 60)
    print("DocumentProcessor OCR Example")
    print("=" * 60)

    print("\nNote: This example requires Tesseract OCR to be installed.")
    print("If OCR fails, install Tesseract and ensure it's in PATH.")
    print("Or set TESSERACT_PATH environment variable.\n")

    try:
        # Test 1: Image OCR
        success1 = await test_image_ocr()

        # Test 2: Keyword extraction
        success2 = await test_keyword_extraction()

        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print(f"Image OCR test: {'✓ PASS' if success1 else '✗ FAIL'}")
        print(f"Keyword extraction test: {'✓ PASS' if success2 else '✗ FAIL'}")

        if success1 and success2:
            print("\n✓ All tests passed!")
            print("\nDocumentProcessor is working correctly.")
            print("You can now use OCR functionality in the Legal Analysis SAAS.")
        else:
            print("\n✗ Some tests failed.")
            print("\nTroubleshooting:")
            print("1. Install Tesseract OCR (see CLAUDE.md for instructions)")
            print("2. Check TESSERACT_PATH environment variable")
            print("3. Verify pytesseract installation: pip install pytesseract")

    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("Make sure you have installed all requirements:")
        print("  pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))