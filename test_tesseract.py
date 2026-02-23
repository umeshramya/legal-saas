#!/usr/bin/env python3
"""
Test script to verify Tesseract OCR installation and configuration.
Run this script to check if Tesseract is properly configured for the application.
"""

import os
import sys
import logging
from PIL import Image, ImageDraw
import io

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tesseract_installation():
    """Test if Tesseract is installed and accessible."""
    try:
        import pytesseract

        # Check tesseract command
        tesseract_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
        if not tesseract_cmd:
            logger.warning("Tesseract command not configured in pytesseract")

            # Try to find tesseract
            import shutil
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                logger.info(f"Tesseract found in PATH: {tesseract_path}")
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                tesseract_cmd = tesseract_path
            else:
                logger.error("Tesseract not found in PATH")
                return False

        logger.info(f"Tesseract command: {tesseract_cmd}")

        # Test tesseract version
        try:
            import subprocess
            result = subprocess.run([tesseract_cmd, '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                logger.info(f"Tesseract version: {version_line}")
            else:
                logger.warning(f"Could not get tesseract version: {result.stderr}")
        except Exception as e:
            logger.warning(f"Could not check tesseract version: {e}")

        return True

    except ImportError:
        logger.error("pytesseract module not installed. Install with: pip install pytesseract")
        return False
    except Exception as e:
        logger.error(f"Error testing tesseract installation: {e}")
        return False


def test_ocr_functionality():
    """Test OCR functionality with a simple generated image."""
    try:
        import pytesseract
        from PIL import Image, ImageDraw

        # Create a simple test image with text
        img = Image.new('RGB', (200, 100), color='white')
        d = ImageDraw.Draw(img)
        d.text((20, 40), 'OCR Test 123', fill='black')

        # Perform OCR
        text = pytesseract.image_to_string(img, lang='eng')
        text = text.strip()

        logger.info(f"OCR Test - Extracted text: '{text}'")

        # Check if we got something reasonable
        if 'OCR' in text or 'Test' in text or '123' in text:
            logger.info("✓ OCR functionality working correctly")
            return True
        else:
            logger.warning(f"OCR test extracted unexpected text: '{text}'")
            return False

    except Exception as e:
        logger.error(f"Error testing OCR functionality: {e}")
        return False


def test_document_processor():
    """Test the DocumentProcessor class initialization."""
    try:
        from src.services.document_processor import DocumentProcessor

        logger.info("Testing DocumentProcessor initialization...")
        processor = DocumentProcessor()
        logger.info("✓ DocumentProcessor initialized successfully")

        # Check if tesseract is configured
        import pytesseract
        tesseract_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
        if tesseract_cmd:
            logger.info(f"DocumentProcessor configured tesseract at: {tesseract_cmd}")
        else:
            logger.warning("DocumentProcessor did not configure tesseract command")

        return True

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing DocumentProcessor: {e}")
        return False


def check_environment():
    """Check environment variables."""
    logger.info("Checking environment variables...")

    tesseract_path = os.getenv('TESSERACT_PATH')
    if tesseract_path:
        logger.info(f"TESSERACT_PATH environment variable: {tesseract_path}")
        if os.path.exists(tesseract_path):
            logger.info("✓ TESSERACT_PATH points to valid file")
        else:
            logger.warning("✗ TESSERACT_PATH does not exist: {tesseract_path}")
    else:
        logger.info("TESSERACT_PATH environment variable not set (using automatic detection)")

    return True


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Tesseract OCR Configuration Test")
    logger.info("=" * 60)

    results = []

    logger.info("\n1. Checking environment...")
    results.append(("Environment", check_environment()))

    logger.info("\n2. Testing Tesseract installation...")
    results.append(("Tesseract Installation", test_tesseract_installation()))

    logger.info("\n3. Testing OCR functionality...")
    if results[-1][1]:  # Only test OCR if installation succeeded
        results.append(("OCR Functionality", test_ocr_functionality()))
    else:
        logger.warning("Skipping OCR functionality test (installation failed)")
        results.append(("OCR Functionality", False))

    logger.info("\n4. Testing DocumentProcessor...")
    results.append(("DocumentProcessor", test_document_processor()))

    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name:30} {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("All tests passed! Tesseract OCR is properly configured.")
        return 0
    else:
        logger.error("Some tests failed. Check the logs above for issues.")
        logger.info("\nTroubleshooting tips:")
        logger.info("1. Install Tesseract OCR:")
        logger.info("   - Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        logger.info("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        logger.info("   - macOS: brew install tesseract")
        logger.info("2. Set TESSERACT_PATH environment variable if tesseract is in non-standard location")
        logger.info("3. Install pytesseract: pip install pytesseract")
        return 1


if __name__ == "__main__":
    sys.exit(main())