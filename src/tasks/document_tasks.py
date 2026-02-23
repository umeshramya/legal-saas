"""
Document processing background tasks.
Placeholder - actual implementations will be added later.
"""
from src.tasks.celery_app import celery_app

@celery_app.task
def process_document_ocr(document_id: int):
    """Process document OCR in background."""
    # TODO: Implement OCR processing
    raise NotImplementedError("OCR processing not implemented yet")

@celery_app.task
def extract_document_text(document_id: int):
    """Extract text from document in background."""
    # TODO: Implement text extraction
    raise NotImplementedError("Text extraction not implemented yet")