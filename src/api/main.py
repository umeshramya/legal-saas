"""
Main FastAPI application for Legal Analysis SAAS.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from typing import List, Optional

from src.config.settings import settings
from src.database.database import init_db, close_db, get_db
from src.database.models import User, Case, Document, Analysis
from src.api.models import (
    UserCreate, UserResponse, Token, CaseCreate, CaseResponse,
    DocumentResponse, AnalysisCreate, AnalysisResponse, SearchQuery,
    SearchResponse, FileUploadResponse, HealthResponse, PaginationParams,
    CNRSearchRequest, CNRSearchResponse
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Legal Analysis SAAS")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing without database")

    yield

    # Shutdown
    logger.info("Shutting down Legal Analysis SAAS")
    await close_db()
    logger.info("Database connections closed")

# Create FastAPI app
app = FastAPI(
    title="Legal Analysis SAAS",
    description="AI-powered legal document analysis platform with Indian Kanoon integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from src.database.database import health_check as db_health_check
    from src.services.deepseek_service import get_deepseek_service
    from src.services.kanoon_service import get_kanoon_client

    health = {
        "status": "healthy",
        "database": await db_health_check(),
        "timestamp": datetime.now()
    }

    # Check DeepSeek API if configured
    if settings.deepseek_api_key:
        try:
            deepseek_service = await get_deepseek_service()
            health["deepseek_api"] = await deepseek_service.test_connection()
        except Exception as e:
            logger.error(f"DeepSeek API health check failed: {e}")
            health["deepseek_api"] = False

    # Check Kanoon API if configured
    if settings.indian_kanoon_api_key:
        try:
            kanoon_client = await get_kanoon_client()
            # Simple test query
            await kanoon_client.search_documents(query="test", maxpages=1)
            health["kanoon_api"] = True
        except Exception as e:
            logger.error(f"Kanoon API health check failed: {e}")
            health["kanoon_api"] = False

    return health


# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db=Depends(get_db)):
    """Register a new user."""
    # TODO: Implement user registration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration not implemented yet"
    )


@app.post("/auth/login", response_model=Token)
async def login(username: str, password: str):
    """Login and get access token."""
    # TODO: Implement login
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login not implemented yet"
    )


# Case management endpoints
@app.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(case_data: CaseCreate, db=Depends(get_db)):
    """Create a new case."""
    # TODO: Implement case creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Case creation not implemented yet"
    )


@app.get("/cases", response_model=List[CaseResponse])
async def list_cases(
    pagination: PaginationParams = Depends(),
    db=Depends(get_db)
):
    """List cases with pagination."""
    # TODO: Implement case listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Case listing not implemented yet"
    )


@app.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: int, db=Depends(get_db)):
    """Get case by ID."""
    # TODO: Implement case retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Case retrieval not implemented yet"
    )


@app.put("/cases/{case_id}", response_model=CaseResponse)
async def update_case(case_id: int, case_data: dict, db=Depends(get_db)):
    """Update a case."""
    # TODO: Implement case update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Case update not implemented yet"
    )


# Document endpoints
@app.post("/cases/{case_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: int,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    """Upload and process a document."""
    # TODO: Implement document upload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document upload not implemented yet"
    )


@app.get("/cases/{case_id}/documents", response_model=List[DocumentResponse])
async def list_documents(case_id: int, db=Depends(get_db)):
    """List documents for a case."""
    # TODO: Implement document listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document listing not implemented yet"
    )


# Analysis endpoints
@app.post("/cases/{case_id}/analyses", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    case_id: int,
    analysis_data: AnalysisCreate,
    db=Depends(get_db)
):
    """Create an analysis for a case or document."""
    # TODO: Implement analysis creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analysis creation not implemented yet"
    )


@app.get("/cases/{case_id}/analyses", response_model=List[AnalysisResponse])
async def list_analyses(case_id: int, db=Depends(get_db)):
    """List analyses for a case."""
    # TODO: Implement analysis listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analysis listing not implemented yet"
    )


@app.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int, db=Depends(get_db)):
    """Get analysis by ID."""
    # TODO: Implement analysis retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analysis retrieval not implemented yet"
    )


# Kanoon search endpoints
@app.post("/search/kanoon", response_model=SearchResponse)
async def search_kanoon(search_query: SearchQuery):
    """Search Indian Kanoon for legal documents."""
    from src.services.kanoon_service import get_kanoon_client

    try:
        kanoon_client = await get_kanoon_client()
        results = await kanoon_client.search_documents(
            query=search_query.query,
            doctypes=search_query.doctypes,
            fromdate=search_query.fromdate,
            todate=search_query.todate,
            title=search_query.title,
            cite=search_query.cite,
            author=search_query.author,
            bench=search_query.bench,
            pagenum=search_query.pagenum,
            maxpages=search_query.maxpages
        )

        parsed_results = kanoon_client.parse_search_result(results)

        return SearchResponse(
            query=search_query.query,
            total_results=results.get("total", 0),
            page=search_query.pagenum,
            results=parsed_results,
            filters={
                "doctypes": search_query.doctypes,
                "fromdate": search_query.fromdate,
                "todate": search_query.todate
            }
        )

    except Exception as e:
        logger.error(f"Kanoon search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/kanoon/documents/{doc_id}")
async def get_kanoon_document(doc_id: str, maxcites: int = 10, maxcitedby: int = 10):
    """Get a document from Indian Kanoon."""
    from src.services.kanoon_service import get_kanoon_client

    try:
        kanoon_client = await get_kanoon_client()
        document = await kanoon_client.get_document(
            doc_id=doc_id,
            maxcites=maxcites,
            maxcitedby=maxcitedby
        )
        return document
    except Exception as e:
        logger.error(f"Error getting Kanoon document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@app.post("/analyze/cnr", response_model=CNRSearchResponse)
async def analyze_by_cnr(cnr_request: CNRSearchRequest):
    """
    Analyze a legal case by CNR (Case Number Record) number.

    Searches Indian Kanoon for documents with the given CNR,
    retrieves the document, and performs AI analysis.
    """
    from src.services.kanoon_service import get_kanoon_client
    from src.services.deepseek_service import get_deepseek_service

    try:
        # Step 1: Search for documents by CNR
        kanoon_client = await get_kanoon_client()
        cnr_result = await kanoon_client.analyze_case_by_cnr(cnr_request.cnr_number)

        if not cnr_result.get('found'):
            return CNRSearchResponse(
                cnr_number=cnr_request.cnr_number,
                found=False,
                error="No documents found for the given CNR number",
                search_results_count=0
            )

        # Prepare base response
        response_data = {
            'cnr_number': cnr_request.cnr_number,
            'found': True,
            'document_id': cnr_result.get('document_id'),
            'document_title': cnr_result.get('document_title'),
            'court': cnr_result.get('court'),
            'date': cnr_result.get('date'),
            'citation': cnr_result.get('citation'),
            'search_results_count': cnr_result.get('metadata', {}).get('search_results', 0),
            'document_text_preview': cnr_result.get('document_text', '')[:500] if cnr_result.get('document_text') else None,
            'metadata': cnr_result.get('metadata', {})
        }

        # Step 2: Perform AI analysis if requested and document text is available
        if cnr_request.include_analysis and cnr_result.get('analysis_ready') and cnr_result.get('document_text'):
            try:
                deepseek_service = await get_deepseek_service()

                # Prepare context for analysis
                context = {
                    'case_context': f"Case with CNR: {cnr_request.cnr_number}",
                    'court': cnr_result.get('court'),
                    'citation': cnr_result.get('citation'),
                    'date': cnr_result.get('date'),
                    'search_results': cnr_result.get('metadata', {}).get('search_results', 0)
                }

                analysis_result = await deepseek_service.analyze_document(
                    document_text=cnr_result['document_text'],
                    analysis_type=cnr_request.analysis_type,
                    context=context
                )

                response_data['analysis_result'] = analysis_result
                response_data['analysis_type'] = cnr_request.analysis_type

            except Exception as analysis_error:
                logger.error(f"AI analysis failed for CNR {cnr_request.cnr_number}: {analysis_error}")
                response_data['error'] = f"Document found but analysis failed: {str(analysis_error)}"
        elif cnr_request.include_analysis and not cnr_result.get('analysis_ready'):
            response_data['error'] = "Document found but text extraction failed for analysis"

        return CNRSearchResponse(**response_data)

    except Exception as e:
        logger.error(f"CNR analysis error for {cnr_request.cnr_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CNR analysis failed: {str(e)}"
        )


@app.post("/search/cnr", response_model=CNRSearchResponse)
async def search_by_cnr(cnr_request: CNRSearchRequest):
    """
    Search for documents by CNR number without AI analysis.
    """
    from src.services.kanoon_service import get_kanoon_client

    try:
        kanoon_client = await get_kanoon_client()
        cnr_result = await kanoon_client.analyze_case_by_cnr(cnr_request.cnr_number)

        if not cnr_result.get('found'):
            return CNRSearchResponse(
                cnr_number=cnr_request.cnr_number,
                found=False,
                error="No documents found for the given CNR number",
                search_results_count=0
            )

        return CNRSearchResponse(
            cnr_number=cnr_request.cnr_number,
            found=True,
            document_id=cnr_result.get('document_id'),
            document_title=cnr_result.get('document_title'),
            court=cnr_result.get('court'),
            date=cnr_result.get('date'),
            citation=cnr_result.get('citation'),
            search_results_count=cnr_result.get('metadata', {}).get('search_results', 0),
            document_text_preview=cnr_result.get('document_text', '')[:500] if cnr_result.get('document_text') else None,
            metadata=cnr_result.get('metadata', {}),
            analysis_type=None if not cnr_request.include_analysis else cnr_request.analysis_type
        )

    except Exception as e:
        logger.error(f"CNR search error for {cnr_request.cnr_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CNR search failed: {str(e)}"
        )


# File processing endpoint
@app.post("/process/file", response_model=FileUploadResponse)
async def process_file(
    file: UploadFile = File(...),
    use_ocr: bool = True,
    page_limit: int = 50
):
    """Process a file (OCR, text extraction)."""
    from src.services.document_processor import get_document_processor

    try:
        processor = await get_document_processor()
        result = await processor.process_uploaded_file(
            file=file,
            use_ocr=use_ocr,
            page_limit=page_limit
        )

        return FileUploadResponse(
            filename=file.filename,
            file_size=result.get("file_size", 0),
            mime_type=result.get("mime_type", "unknown"),
            processing_result=result,
            success=result.get("error") is None,
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"File processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


# AI analysis endpoint
@app.post("/analyze/document")
async def analyze_document(
    document_text: str,
    analysis_type: str = "document_summary",
    context: Optional[dict] = None
):
    """Analyze a document using DeepSeek AI."""
    from src.services.deepseek_service import get_deepseek_service

    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DeepSeek API key not configured"
        )

    try:
        deepseek_service = await get_deepseek_service()
        result = await deepseek_service.analyze_document(
            document_text=document_text,
            analysis_type=analysis_type,
            context=context
        )
        return result
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Legal Analysis SAAS",
        "version": "1.0.0",
        "description": "AI-powered legal document analysis platform",
        "endpoints": {
            "health": "/health",
            "documentation": "/docs",
            "cases": "/cases",
            "search": "/search/kanoon",
            "analysis": "/analyze/document"
        }
    }


# Import datetime for health check
from datetime import datetime