# Legal Analysis SAAS

An AI-powered legal document analysis platform with Indian Kanoon integration, built with FastAPI, DeepSeek AI, and PostgreSQL.

## Features

- **Document Processing**: OCR and text extraction from PDFs, Word documents, images
- **AI Analysis**: DeepSeek AI integration for legal document summarization, risk assessment, case analysis
- **Indian Kanoon Integration**: Search and retrieve legal documents from Indian Kanoon API
- **Case Management**: Organize legal cases with documents, analyses, and team collaboration
- **Database Storage**: PostgreSQL for structured data storage with SQLAlchemy ORM
- **RESTful API**: FastAPI with OpenAPI documentation
- **Authentication**: JWT-based authentication and authorization

## Architecture

```
legal-saas/
├── src/
│   ├── api/                 # FastAPI application and endpoints
│   ├── database/            # SQLAlchemy models and database connection
│   ├── services/            # Business logic services
│   │   ├── deepseek_service.py      # DeepSeek AI integration
│   │   ├── kanoon_service.py      # Indian Kanoon API integration
│   │   └── document_processor.py  # Document processing (OCR, text extraction)
│   ├── config/              # Configuration and settings
│   └── utils/               # Utility functions
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Tesseract OCR (for document processing)
- Indian Kanoon API key (optional)
- DeepSeek API key

### 2. Installation

```bash
# Clone and navigate to project
cd legal-saas

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Ubuntu: sudo apt install tesseract-ocr

# Copy environment file
cp .env.example .env
```

### 3. Configure Environment Variables

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/legal_analysis

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Indian Kanoon API
INDIAN_KANOON_API_KEY=your_indian_kanoon_api_key_here

# JWT
JWT_SECRET_KEY=your_jwt_secret_key_change_in_production
```

### 4. Database Setup

```bash
# Create database (PostgreSQL)
createdb legal_analysis

# The application will create tables automatically on startup
```

### 5. Run the Application

```bash
uvicorn src.api.main:app --reload
```

Open http://localhost:8000/docs for API documentation.

## API Endpoints

### Health Check
- `GET /health` - System health status

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token

### Case Management
- `POST /cases` - Create new case
- `GET /cases` - List cases
- `GET /cases/{id}` - Get case details
- `PUT /cases/{id}` - Update case

### Document Management
- `POST /cases/{id}/documents` - Upload document
- `GET /cases/{id}/documents` - List case documents

### Analysis
- `POST /cases/{id}/analyses` - Create AI analysis
- `GET /cases/{id}/analyses` - List analyses
- `GET /analyses/{id}` - Get analysis results

### Indian Kanoon Integration
- `POST /search/kanoon` - Search legal documents
- `GET /kanoon/documents/{id}` - Get Kanoon document

### File Processing
- `POST /process/file` - Process file (OCR, text extraction)

### AI Analysis
- `POST /analyze/document` - Analyze document with DeepSeek AI

### CNR-Based Case Analysis
- `POST /analyze/cnr` - Search and analyze case by CNR (Case Number Record) number
- `POST /search/cnr` - Search for documents by CNR number

## Indian Kanoon API Integration

The system integrates with Indian Kanoon API for legal document search and retrieval:

### Features
- **Document Search**: Search by keywords, parties, citations
- **Document Retrieval**: Get full document text and metadata
- **Citation Analysis**: Get citing and cited documents
- **Batch Search**: Multiple queries concurrently
- **CNR Search**: Search by Case Number Record (CNR) number

### API Documentation
- Official documentation: https://api.indiankanoon.org/documentation/
- Authentication: API token or public-private key
- Response formats: JSON or XML

## DeepSeek AI Integration

Uses DeepSeek AI (OpenAI-compatible API) for legal document analysis:

### Analysis Types
- **Document Summary**: Comprehensive document analysis
- **Risk Assessment**: Legal risk analysis with scores
- **Case Analysis**: Complete case strategy analysis
- **Legal Arguments**: Generate legal arguments and counterarguments
- **Outcome Prediction**: Predict case outcomes with confidence scores

## CNR-Based Analysis

The system supports searching and analyzing legal cases by CNR (Case Number Record) number, a unique identifier used in Indian courts.

### How it Works
1. **CNR Search**: The system searches Indian Kanoon for documents containing the CNR number
2. **Document Retrieval**: Retrieves the most relevant document
3. **Text Extraction**: Extracts text from the document
4. **AI Analysis**: Performs DeepSeek AI analysis on the extracted text
5. **Comprehensive Report**: Provides legal analysis, risk assessment, and strategic recommendations

### Supported CNR Formats
- Standard CNR format: `DLCT010001232023` (16 digits)
- CNR with prefixes: `CNR NO: DLCT010001232023`
- Case number variations

### API Endpoints
- `POST /analyze/cnr` - Full analysis pipeline
- `POST /search/cnr` - Search only (no AI analysis)

### Example Request
```json
{
  "cnr_number": "DLCT010001232023",
  "include_analysis": true,
  "analysis_type": "case_analysis"
}
```

## Database Schema

### Core Tables
- **users**: User accounts and authentication
- **cases**: Legal cases with metadata
- **documents**: Legal documents with extracted text
- **analyses**: AI analysis results
- **teams**: Team collaboration
- **search_queries**: Kanoon search history
- **audit_logs**: Security audit trail

## Development

### Code Structure
- **FastAPI Application**: `src/api/main.py`
- **Database Models**: `src/database/models.py`
- **Services**: `src/services/`
- **Configuration**: `src/config/settings.py`

### Adding New Features
1. Add database models in `src/database/models.py`
2. Create service logic in `src/services/`
3. Add API endpoints in `src/api/main.py`
4. Update Pydantic models in `src/api/models.py`

### Testing
```bash
# Run tests (to be implemented)
pytest tests/
```

## Deployment

### Quick Start
- **Docker**: `docker-compose up -d` (See [QUICK_DEPLOYMENT.md](QUICK_DEPLOYMENT.md))
- **VPS/Cloud**: Comprehensive guide in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Tesseract OCR**: Cloud deployment instructions in [CLOUD_DEPLOYMENT_TESSERACT.md](CLOUD_DEPLOYMENT_TESSERACT.md)

### Architecture
The application uses a multi-service architecture:
- **FastAPI Application**: Main API server (Port 8000)
- **PostgreSQL**: Primary database (Port 5432) - Fully implemented
- **Redis**: Cache and task queue (Port 6379) - Configured, needs implementation
- **Celery**: Background task processing - Referenced, needs implementation

### Deployment Options
- **🐳 Docker**: Local development and production with `docker-compose`
- **☁️ Cloud Platforms**: AWS, Google Cloud, Azure, Render, Railway, Heroku
- **🖥️ VPS**: Hostinger, DigitalOcean, Linode with Nginx + systemd
- **🚀 Managed Services**: Platform-as-a-Service options

### Database Requirements
- **PostgreSQL 12+** with asyncpg driver
- **Redis 7+** for caching and task queues
- Connection pooling recommended for production

For complete deployment instructions across all platforms, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:password@localhost:5432/legal_analysis` | Yes |
| `REDIS_URL` | Redis connection URL for caching and task queues | `redis://localhost:6379/0` | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek API key for AI analysis | (None) | Yes |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL | `https://api.deepseek.com` | No |
| `INDIAN_KANOON_API_KEY` | Indian Kanoon API key for legal document search | (None) | No |
| `INDIAN_KANOON_BASE_URL` | Indian Kanoon API base URL | `https://api.indiankanoon.org` | No |
| `JWT_SECRET_KEY` | JWT signing key for authentication | (None) | Yes |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `30` | No |
| `DEBUG` | Debug mode (disables in production) | `True` | No |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size in MB | `50` | No |
| `ALLOWED_HOSTS` | Allowed hostnames for the application | `localhost,127.0.0.1` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` | No |
| `TESSERACT_PATH` | Path to Tesseract OCR executable (auto-detected) | (None) | No |
| `OCR_ENABLED` | Enable/disable OCR functionality | `true` | No |
| `S3_BUCKET_NAME` | AWS S3 bucket for document storage (optional) | (None) | No |
| `S3_ACCESS_KEY` | AWS S3 access key (optional) | (None) | No |
| `S3_SECRET_KEY` | AWS S3 secret key (optional) | (None) | No |
| `S3_REGION` | AWS S3 region | `ap-south-1` | No |

For complete environment configuration, copy `.env.example` to `.env` and update the values.

## Implementation Status

For a detailed breakdown of what's implemented and what's planned, see [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

**Key Notes:**
- ✅ **PostgreSQL**: Fully implemented with async SQLAlchemy models
- ⚠️ **Redis**: Configured but not implemented (caching, sessions missing)
- ⚠️ **Celery**: Referenced in docker-compose but not implemented
- ✅ **OCR/Tesseract**: Fully implemented with cloud deployment support
- ✅ **AI Integration**: DeepSeek API integration complete
- ✅ **Indian Kanoon**: API client implementation complete

## License

MIT

## Support

For issues and feature requests, please create an issue in the repository.