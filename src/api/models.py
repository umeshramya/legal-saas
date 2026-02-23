"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    LAWYER = "lawyer"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    RESEARCHER = "researcher"


class CaseStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    PLEADING = "pleading"
    AFFIDAVIT = "affidavit"
    ORDER = "order"
    JUDGMENT = "judgment"
    EVIDENCE = "evidence"
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class AnalysisType(str, Enum):
    DOCUMENT_SUMMARY = "document_summary"
    RISK_ASSESSMENT = "risk_assessment"
    CASE_ANALYSIS = "case_analysis"
    DOCUMENT_REVIEW = "document_review"
    LEGAL_ARGUMENTS = "legal_arguments"
    OUTCOME_PREDICTION = "outcome_prediction"


# User models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.CLIENT


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Authentication models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


# Team models
class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TeamMemberCreate(BaseModel):
    user_id: int
    role: str = Field(default="member", pattern="^(owner|admin|member)$")


# Case models
class CaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    case_number: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=255)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    plaintiff: Optional[str] = Field(None, max_length=255)
    defendant: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    filing_date: Optional[datetime] = None
    hearing_date: Optional[datetime] = None


class CaseCreate(CaseBase):
    team_id: Optional[int] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    case_number: Optional[str] = Field(None, max_length=100)
    court_name: Optional[str] = Field(None, max_length=255)
    status: Optional[CaseStatus] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    hearing_date: Optional[datetime] = None


class CaseResponse(CaseBase):
    id: int
    user_id: int
    team_id: Optional[int]
    status: CaseStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Document models
class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    file_type: DocumentType = DocumentType.OTHER
    document_date: Optional[datetime] = None
    author: Optional[str] = Field(None, max_length=255)


class DocumentCreate(DocumentBase):
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1, max_length=100)


class DocumentResponse(DocumentBase):
    id: int
    case_id: int
    filename: str
    file_size: int
    mime_type: str
    storage_path: str
    storage_provider: str
    page_count: Optional[int]
    extracted_text: Optional[str]
    ocr_used: bool
    is_processed: bool
    kanoon_doc_id: Optional[str]
    kanoon_citation: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Analysis models
class AnalysisBase(BaseModel):
    analysis_type: AnalysisType
    document_id: Optional[int] = None


class AnalysisCreate(AnalysisBase):
    prompt_customization: Optional[Dict[str, Any]] = None


class AnalysisResponse(AnalysisBase):
    id: int
    case_id: int
    user_id: int
    status: str
    model_used: Optional[str]
    model_version: Optional[str]
    analysis_result: Optional[Dict[str, Any]]
    processing_time_ms: Optional[int]
    token_count: Optional[int]
    cost_estimate: Optional[float]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Search models
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    doctypes: Optional[List[str]] = None
    fromdate: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    todate: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    title: Optional[str] = None
    cite: Optional[str] = None
    author: Optional[str] = None
    bench: Optional[str] = None
    pagenum: int = Field(default=0, ge=0)
    maxpages: int = Field(default=10, ge=1, le=1000)


class SearchResponse(BaseModel):
    query: str
    total_results: int
    page: int
    results: List[Dict[str, Any]]
    filters: Optional[Dict[str, Any]] = None


# Kanoon models
class KanoonDocumentRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    maxcites: int = Field(default=10, ge=1, le=50)
    maxcitedby: int = Field(default=10, ge=1, le=50)


class CNRSearchRequest(BaseModel):
    """Request model for CNR (Case Number Record) search."""
    cnr_number: str = Field(..., min_length=5, max_length=50, description="CNR number to search for")
    include_analysis: bool = Field(default=True, description="Whether to perform AI analysis")
    analysis_type: str = Field(default="case_analysis", description="Type of analysis to perform")


class CNRSearchResponse(BaseModel):
    """Response model for CNR search and analysis."""
    cnr_number: str
    found: bool
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    citation: Optional[str] = None
    search_results_count: int = 0
    document_text_preview: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    analysis_type: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class KanoonBatchSearchRequest(BaseModel):
    queries: List[str] = Field(..., min_items=1, max_items=10)
    filters: Optional[Dict[str, Any]] = None
    limit_per_query: int = Field(default=10, ge=1, le=50)


# File upload models
class FileUploadResponse(BaseModel):
    filename: str
    file_size: int
    mime_type: str
    processing_result: Dict[str, Any]
    success: bool
    error: Optional[str] = None


# Health check
class HealthResponse(BaseModel):
    status: str
    database: bool
    redis: Optional[bool] = None
    deepseek_api: Optional[bool] = None
    kanoon_api: Optional[bool] = None
    timestamp: datetime


# Pagination models
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int