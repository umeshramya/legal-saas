"""
SQLAlchemy models for the legal analysis SAAS.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Float, JSON, Enum, LargeBinary
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    LAWYER = "lawyer"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    RESEARCHER = "researcher"


class CaseStatus(str, enum.Enum):
    """Case status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class DocumentType(str, enum.Enum):
    """Document type enumeration."""
    PLEADING = "pleading"
    AFFIDAVIT = "affidavit"
    ORDER = "order"
    JUDGMENT = "judgment"
    EVIDENCE = "evidence"
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class AnalysisStatus(str, enum.Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cases = relationship("Case", back_populates="user")
    teams = relationship("TeamMember", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    analyses = relationship("Analysis", back_populates="user")


class Team(Base):
    """Team model for collaboration."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    members = relationship("TeamMember", back_populates="team")
    cases = relationship("Case", back_populates="team")


class TeamMember(Base):
    """Team membership model."""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member")  # owner, admin, member
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="teams")


class Case(Base):
    """Legal case model."""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)

    # Case metadata
    title = Column(String(500), nullable=False)
    case_number = Column(String(100), nullable=True)
    court_name = Column(String(255), nullable=True)
    jurisdiction = Column(String(100), nullable=True)

    # Parties
    plaintiff = Column(String(255), nullable=True)
    defendant = Column(String(255), nullable=True)

    # Status and dates
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT)
    filing_date = Column(DateTime(timezone=True), nullable=True)
    hearing_date = Column(DateTime(timezone=True), nullable=True)

    # Description and tags
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=[])  # List of tag strings

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cases")
    team = relationship("Team", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    """Legal document model."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)

    # Document metadata
    title = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    mime_type = Column(String(100), nullable=False)

    # Storage information
    storage_path = Column(String(500), nullable=False)  # S3 path or local path
    storage_provider = Column(String(50), default="s3")  # s3, local, kanoon

    # Content information
    page_count = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    ocr_used = Column(Boolean, default=False)

    # Source information (if from Kanoon API)
    kanoon_doc_id = Column(String(100), nullable=True, index=True)
    kanoon_citation = Column(String(255), nullable=True)

    # Metadata
    upload_date = Column(DateTime(timezone=True), nullable=True)
    document_date = Column(DateTime(timezone=True), nullable=True)
    author = Column(String(255), nullable=True)

    # Processing information
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    case = relationship("Case", back_populates="documents")
    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")


class Analysis(Base):
    """AI analysis of a document or case."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Analysis metadata
    analysis_type = Column(String(100), nullable=False)  # summary, risk, strategy, etc.
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)

    # AI model information
    model_used = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)

    # Analysis content
    prompt_used = Column(Text, nullable=True)
    analysis_result = Column(JSON, nullable=True)  # Structured JSON result
    raw_response = Column(Text, nullable=True)  # Raw AI response

    # Metrics
    processing_time_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    cost_estimate = Column(Float, nullable=True)

    # Error information
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    case = relationship("Case", back_populates="analyses")
    document = relationship("Document", back_populates="analyses")
    user = relationship("User", back_populates="analyses")


class SearchQuery(Base):
    """Search query history for Kanoon API."""
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Query information
    query_text = Column(Text, nullable=False)
    filters = Column(JSON, nullable=True)  # JSON object with filters

    # Results
    result_count = Column(Integer, nullable=True)
    results = Column(JSON, nullable=True)  # First page results

    # Kanoon API information
    kanoon_request_id = Column(String(100), nullable=True)
    kanoon_response_time_ms = Column(Integer, nullable=True)

    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")


class APIKey(Base):
    """API keys for external integrations."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Key information
    name = Column(String(100), nullable=False)
    key = Column(String(255), unique=True, index=True, nullable=False)
    secret = Column(String(255), nullable=False)  # Hashed secret

    # Permissions
    scopes = Column(JSON, default=[])  # List of allowed scopes

    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Expiry
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="api_keys")


class AuditLog(Base):
    """Audit log for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Action information
    action = Column(String(100), nullable=False)  # login, create, update, delete, etc.
    resource_type = Column(String(100), nullable=False)  # user, case, document, etc.
    resource_id = Column(String(100), nullable=True)

    # Details
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())