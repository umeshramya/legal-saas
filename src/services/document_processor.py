"""
Document processing service for OCR and text extraction.
"""

import os
import io
import tempfile
import logging
from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime
import asyncio

import pdfplumber
import pytesseract
from PIL import Image
# Try to import magic (python-magic or python-magic-bin)
# python-magic-bin is recommended for Windows, python-magic for Linux/Mac
try:
    import magic
except ImportError:
    try:
        import magic as magic
    except ImportError:
        magic = None
        import warnings
        warnings.warn(
            "python-magic not installed. File type validation will be limited. "
            "Install python-magic (Linux/Mac) or python-magic-bin (Windows)."
        )
from fastapi import UploadFile

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing legal documents (OCR, text extraction, etc.)."""

    def __init__(self):
        # Configure Tesseract OCR path
        # Priority: 1. settings.tesseract_path, 2. Default Windows path, 3. System PATH
        tesseract_path = None

        # Check settings.tesseract_path first
        if settings.tesseract_path and os.path.exists(settings.tesseract_path):
            tesseract_path = settings.tesseract_path
            logger.info(f"Tesseract configured from settings: {tesseract_path}")
        elif os.name == 'nt':  # Windows
            # Try default Windows installation path
            default_windows_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(default_windows_path):
                tesseract_path = default_windows_path
                logger.info(f"Tesseract configured at default Windows path: {tesseract_path}")
            else:
                # Try alternative Windows paths
                alternative_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    r'C:\Tesseract-OCR\tesseract.exe'
                ]
                for path in alternative_paths:
                    if os.path.exists(path):
                        tesseract_path = path
                        logger.info(f"Tesseract found at alternative path: {tesseract_path}")
                        break
        else:  # Linux/Mac
            # Check if tesseract is in PATH
            import shutil
            path_check = shutil.which('tesseract')
            if path_check:
                tesseract_path = path_check
                logger.info(f"Tesseract found in system PATH: {tesseract_path}")
            else:
                # Try common Linux/Mac locations
                common_paths = [
                    '/usr/bin/tesseract',
                    '/usr/local/bin/tesseract',
                    '/opt/homebrew/bin/tesseract',  # macOS Homebrew
                    '/usr/bin/tesseract-ocr',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        tesseract_path = path
                        logger.info(f"Tesseract found at common location: {tesseract_path}")
                        break

        # Set tesseract command if found
        self.ocr_enabled = settings.ocr_enabled
        try:
            if tesseract_path and settings.ocr_enabled:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                self.ocr_enabled = True
                logger.info(f"Tesseract OCR configured successfully: {tesseract_path}")
            elif settings.ocr_enabled:
                self.ocr_enabled = False
                logger.warning(
                    "Tesseract OCR not found. OCR functionality will not work. "
                    "Please install Tesseract OCR: "
                    "Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki "
                    "Linux: sudo apt-get install tesseract-ocr "
                    "macOS: brew install tesseract"
                )
            else:
                self.ocr_enabled = False
                logger.info("OCR functionality disabled via settings (OCR_ENABLED=false)")
        except Exception as e:
            self.ocr_enabled = False
            logger.error(f"Error configuring Tesseract OCR: {e}")
            logger.warning("OCR functionality disabled due to configuration error")

        # File type validation
        self.allowed_mime_types = {
            'application/pdf': ['pdf'],
            'application/msword': ['doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
            'text/plain': ['txt'],
            'application/rtf': ['rtf'],
            'image/jpeg': ['jpg', 'jpeg'],
            'image/png': ['png'],
            'image/tiff': ['tif', 'tiff'],
        }

        self.max_file_size = settings.max_upload_size_mb * 1024 * 1024  # Convert MB to bytes

        logger.info("Document processor initialized")

    async def process_uploaded_file(
        self,
        file: UploadFile,
        use_ocr: bool = True,
        page_limit: int = 50
    ) -> Dict[str, Any]:
        """
        Process an uploaded file.

        Args:
            file: UploadFile from FastAPI
            use_ocr: Whether to use OCR for images/scanned PDFs
            page_limit: Maximum pages to process

        Returns:
            Dict with processing results
        """
        # Validate file
        validation_result = await self.validate_file(file)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid file: {validation_result['error']}")

        # Read file content
        content = await file.read()
        filename = file.filename
        mime_type = validation_result["mime_type"]

        # Process based on file type
        if mime_type == "application/pdf":
            return await self.process_pdf(content, filename, use_ocr, page_limit)
        elif mime_type in ["image/jpeg", "image/png", "image/tiff"]:
            return await self.process_image(content, filename, use_ocr)
        elif mime_type in ["text/plain", "application/rtf"]:
            return await self.process_text_file(content, filename)
        elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return await self.process_word_document(content, filename)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

    def _guess_mime_type_from_extension(self, filename: str) -> str:
        """
        Guess MIME type from file extension when magic is not available.
        """
        if not filename:
            return "application/octet-stream"

        ext = filename.split('.')[-1].lower() if '.' in filename else ''

        # Common legal document extensions
        extension_map = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'rtf': 'application/rtf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tif': 'image/tiff',
            'tiff': 'image/tiff',
        }

        return extension_map.get(ext, 'application/octet-stream')

    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded file.

        Args:
            file: UploadFile to validate

        Returns:
            Dict with validation results
        """
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to start

        if file_size > self.max_file_size:
            return {
                "valid": False,
                "error": f"File too large. Maximum size is {settings.max_upload_size_mb}MB"
            }

        # Check file type
        content = await file.read(2048)  # Read first 2KB for magic detection
        file.file.seek(0)

        mime_type = None
        if magic:
            try:
                mime_type = magic.from_buffer(content, mime=True)
            except Exception as e:
                logger.warning(f"Magic file type detection failed: {e}")
                # Fall back to file extension
                mime_type = self._guess_mime_type_from_extension(filename)
        else:
            # No magic library, use file extension
            mime_type = self._guess_mime_type_from_extension(filename)

        if mime_type not in self.allowed_mime_types:
            return {
                "valid": False,
                "error": f"Unsupported file type: {mime_type}"
            }

        # Check file extension
        filename = file.filename
        if filename:
            ext = filename.split('.')[-1].lower()
            allowed_exts = self.allowed_mime_types.get(mime_type, [])
            if ext not in allowed_exts:
                return {
                    "valid": False,
                    "error": f"File extension .{ext} doesn't match MIME type {mime_type}"
                }

        return {
            "valid": True,
            "mime_type": mime_type,
            "file_size": file_size,
            "filename": filename
        }

    async def process_pdf(
        self,
        pdf_content: bytes,
        filename: str,
        use_ocr: bool = True,
        page_limit: int = 50
    ) -> Dict[str, Any]:
        """
        Process PDF file.

        Args:
            pdf_content: PDF file bytes
            filename: Original filename
            use_ocr: Whether to use OCR
            page_limit: Maximum pages to process

        Returns:
            Dict with processing results
        """
        result = {
            "filename": filename,
            "file_type": "pdf",
            "total_pages": 0,
            "pages_processed": 0,
            "extracted_text": "",
            "ocr_used": False,
            "error": None,
            "metadata": {},
        }

        try:
            # Use temp file for PDF processing
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(pdf_content)
                tmp_path = tmp_file.name

            try:
                with pdfplumber.open(tmp_path) as pdf:
                    result["total_pages"] = len(pdf.pages)
                    result["metadata"] = pdf.metadata

                    # Process pages
                    limit = min(page_limit, result["total_pages"])
                    extracted_text = []
                    ocr_used = False

                    for i in range(limit):
                        page = pdf.pages[i]
                        logger.debug(f"Processing PDF page {i+1}/{limit}")

                        # Try direct text extraction first
                        text = page.extract_text()

                        if text and text.strip():
                            extracted_text.append(f"=== Page {i+1} ===\n{text}\n")
                        elif use_ocr and self.ocr_enabled:
                            # Use OCR for scanned pages
                            images = page.images
                            if images:
                                for img_idx, img in enumerate(images):
                                    try:
                                        img_bytes = img["stream"].get_data()
                                        image = Image.open(io.BytesIO(img_bytes))
                                        ocr_text = pytesseract.image_to_string(image, lang='eng')
                                        extracted_text.append(f"=== Page {i+1} (OCR Image {img_idx+1}) ===\n{ocr_text}\n")
                                        ocr_used = True
                                    except Exception as e:
                                        extracted_text.append(f"=== Page {i+1} ===\n[OCR Error: {e}]\n")
                            else:
                                extracted_text.append(f"=== Page {i+1} ===\n[No text or images found]\n")
                        elif use_ocr and not self.ocr_enabled:
                            extracted_text.append(f"=== Page {i+1} ===\n[OCR disabled - Tesseract not installed]\n")
                        else:
                            extracted_text.append(f"=== Page {i+1} ===\n[No text extracted]\n")

                        result["pages_processed"] = i + 1

                    result["extracted_text"] = "\n".join(extracted_text)
                    result["ocr_used"] = ocr_used

            finally:
                # Clean up temp file
                os.unlink(tmp_path)

            logger.info(f"PDF processing completed: {filename}, pages: {result['pages_processed']}")

        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            result["error"] = str(e)

        return result

    async def process_image(
        self,
        image_content: bytes,
        filename: str,
        use_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Process image file.

        Args:
            image_content: Image file bytes
            filename: Original filename
            use_ocr: Whether to use OCR

        Returns:
            Dict with processing results
        """
        result = {
            "filename": filename,
            "file_type": "image",
            "extracted_text": "",
            "ocr_used": False,
            "error": None,
        }

        try:
            if use_ocr and self.ocr_enabled:
                image = Image.open(io.BytesIO(image_content))
                text = pytesseract.image_to_string(image, lang='eng')
                result["extracted_text"] = text
                result["ocr_used"] = True
                logger.info(f"Image OCR completed: {filename}")
            elif use_ocr and not self.ocr_enabled:
                result["extracted_text"] = "[OCR disabled - Tesseract not installed]"
                result["ocr_used"] = False
                logger.warning(f"OCR requested but Tesseract not installed for {filename}")
            else:
                result["extracted_text"] = "[OCR not enabled for images]"

        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            result["error"] = str(e)

        return result

    async def process_text_file(
        self,
        text_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Process text file.

        Args:
            text_content: Text file bytes
            filename: Original filename

        Returns:
            Dict with processing results
        """
        result = {
            "filename": filename,
            "file_type": "text",
            "extracted_text": "",
            "error": None,
        }

        try:
            # Try UTF-8 first, then fallback
            try:
                text = text_content.decode('utf-8')
            except UnicodeDecodeError:
                text = text_content.decode('latin-1')

            result["extracted_text"] = text
            logger.info(f"Text file processed: {filename}")

        except Exception as e:
            logger.error(f"Error processing text file {filename}: {e}")
            result["error"] = str(e)

        return result

    async def process_word_document(
        self,
        doc_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Process Word document.

        Args:
            doc_content: Word document bytes
            filename: Original filename

        Returns:
            Dict with processing results
        """
        result = {
            "filename": filename,
            "file_type": "word",
            "extracted_text": "",
            "error": None,
        }

        try:
            # For now, use a simple approach
            # In production, use python-docx or similar library
            result["extracted_text"] = "[Word document processing not fully implemented]"
            logger.warning(f"Word document processing limited for {filename}")

        except Exception as e:
            logger.error(f"Error processing Word document {filename}: {e}")
            result["error"] = str(e)

        return result

    def extract_keywords(
        self,
        text: str,
        keyword_categories: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, List[str]]:
        """
        Extract keywords from text.

        Args:
            text: Text to analyze
            keyword_categories: Custom keyword categories

        Returns:
            Dict with found keywords by category
        """
        if keyword_categories is None:
            # Default legal keywords
            keyword_categories = {
                'hearing': ['hearing', 'proceeding', 'meeting', 'tribunal', 'arbitrator'],
                'filing': ['filed', 'submitted', 'application', 'statement', 'defense', 'claim'],
                'dates': ['2025', '2026', 'january', 'february', 'march', 'april', 'may', 'june'],
                'financial': ['payment', 'amount', 'crore', 'lakh', 'rupees', '₹'],
                'legal': ['objection', 'affidavit', 'section', 'order', 'rule', 'cpc']
            }

        text_lower = text.lower()
        found_keywords = {}

        for category, keywords in keyword_categories.items():
            found = [word for word in keywords if word in text_lower]
            if found:
                found_keywords[category] = found

        return found_keywords

    def estimate_reading_time(self, text: str, words_per_minute: int = 200) -> int:
        """
        Estimate reading time for text.

        Args:
            text: Text to estimate
            words_per_minute: Average reading speed

        Returns:
            Estimated reading time in minutes
        """
        words = len(text.split())
        return max(1, words // words_per_minute)

    async def batch_process_files(
        self,
        files: List[UploadFile],
        use_ocr: bool = True,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Process multiple files concurrently.

        Args:
            files: List of UploadFile objects
            use_ocr: Whether to use OCR
            max_concurrent: Maximum concurrent processing

        Returns:
            List of processing results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(file: UploadFile) -> Dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.process_uploaded_file(file, use_ocr)
                    return {
                        "filename": file.filename,
                        "success": True,
                        "result": result
                    }
                except Exception as e:
                    return {
                        "filename": file.filename,
                        "success": False,
                        "error": str(e)
                    }

        tasks = [process_with_semaphore(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                final_results.append(result)

        return final_results


# Global processor instance
_document_processor = None


async def get_document_processor() -> DocumentProcessor:
    """
    Get or create document processor.

    Returns:
        DocumentProcessor instance
    """
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor