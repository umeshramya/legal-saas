# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Legal Analysis SAAS is an AI-powered legal document analysis platform with Indian Kanoon integration, built with FastAPI, DeepSeek AI, and PostgreSQL. The system processes legal documents, performs AI analysis, and integrates with Indian Kanoon for legal document search.

## Architecture

The application follows a layered architecture:

1. **API Layer** (`src/api/`): FastAPI application with RESTful endpoints
2. **Service Layer** (`src/services/`): Business logic for AI analysis, document processing, and external API integration
3. **Database Layer** (`src/database/`): SQLAlchemy ORM models and async database operations
4. **Configuration Layer** (`src/config/`): Pydantic-based settings management

Key services:
- `deepseek_service.py`: DeepSeek AI integration for legal document analysis
- `kanoon_service.py`: Indian Kanoon API client for legal document search
- `document_processor.py`: OCR and text extraction from documents

## Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Tesseract OCR (for document processing)
- Indian Kanoon API key (optional)
- DeepSeek API key

**Windows Development Note:**
- Install Tesseract OCR for Windows from https://github.com/UB-Mannheim/tesseract/wiki
- For file type detection, install `python-magic-bin` instead of `python-magic`:
  ```bash
  pip uninstall python-magic
  pip install python-magic-bin
  ```

### Initial Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows Git Bash)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Database Setup
```bash
# Create PostgreSQL database
createdb legal_analysis

# Or use Docker Compose
docker-compose up -d postgres redis
```

## Running the Application

### Development Mode
```bash
# Using venv Python directly
"venv/Scripts/python" -m uvicorn src.api.main:app --reload

# Or activate venv first
source venv/Scripts/activate
uvicorn src.api.main:app --reload
```

### Production Mode with Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Integration Tests
```bash
# Run all integration tests
python test_integration.py

# Test specific components
python -c "import asyncio; from test_integration import test_kanoon_integration; asyncio.run(test_kanoon_integration())"
```

### Example Script
```bash
# Run CNR analysis example
python example_cnr_analysis.py

# With specific CNR number
python example_cnr_analysis.py "DLCT010001232023"
```

## Key API Endpoints

### Core Functionality
- `POST /analyze/cnr` - Full CNR-based case analysis with AI
- `POST /search/cnr` - Search for documents by CNR number
- `POST /search/kanoon` - Search Indian Kanoon for legal documents
- `POST /analyze/document` - Analyze document text with DeepSeek AI
- `POST /process/file` - Process uploaded files (OCR, text extraction)

### Health and Status
- `GET /health` - System health check with service status
- `GET /` - API information and available endpoints

## Database Operations

The application uses SQLAlchemy with asyncpg. Database tables are created automatically on startup. Key models include:
- `User`, `Team` - User management and collaboration
- `Case`, `Document` - Legal case and document management
- `Analysis` - AI analysis results storage
- `SearchQuery`, `AuditLog` - Search history and security logging

## Service Integration Notes

### Indian Kanoon API
- All endpoints require POST requests with form data
- API key authentication via `Authorization: Token {api_key}` header
- Search endpoint: `/search/` with `formInput` parameter
- Document retrieval: `/doc/{doc_id}/` with optional `maxcites` and `maxcitedby` parameters

### DeepSeek AI
- Uses OpenAI-compatible API (base URL: `https://api.deepseek.com`)
- Supports multiple analysis types: `document_summary`, `risk_assessment`, `case_analysis`, etc.
- Response includes token usage and cost estimation

## Development Workflow

### Adding New Features
1. Add database models in `src/database/models.py`
2. Create service logic in `src/services/`
3. Add Pydantic models in `src/api/models.py`
4. Implement API endpoints in `src/api/main.py`

### Code Style
- Use async/await pattern for all I/O operations
- Follow FastAPI dependency injection pattern
- Use Pydantic models for request/response validation
- Log errors with appropriate context using the configured logger

### Environment Configuration
Settings are managed through `src/config/settings.py` using Pydantic Settings. Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `DEEPSEEK_API_KEY`: DeepSeek AI API key
- `INDIAN_KANOON_API_KEY`: Indian Kanoon API key (optional)
- `JWT_SECRET_KEY`: JWT signing key for authentication

Optional environment variables:
- `TESSERACT_PATH`: Path to Tesseract OCR executable (for non-standard installations)
- `OCR_ENABLED`: Set to `false` to disable OCR functionality entirely (default: `true`)

## Troubleshooting

### Common Issues
1. **Database connection fails**: Ensure PostgreSQL is running and credentials in `.env` are correct
2. **Indian Koon API 405 errors**: All Kanoon endpoints require POST requests (not GET)
3. **DeepSeek API 401 errors**: Verify API key is valid and properly set in `.env`
4. **OCR failures**:
   - Install Tesseract OCR system package: `apt-get install tesseract-ocr` (Linux) or download installer (Windows)
   - Check Tesseract path: Set `TESSERACT_PATH` environment variable if tesseract is installed in non-standard location
   - Verify installation: Run `tesseract --version` in terminal
5. **Tesseract not found in cloud deployment**:
   - Use Docker deployment (includes Tesseract in Dockerfile)
   - Add Tesseract to build configuration for your cloud platform
   - Set `TESSERACT_PATH` environment variable to the correct path

### Debug Mode
Set `DEBUG=True` in `.env` for detailed logging and error messages.

## Tesseract OCR Deployment

### Docker/Container Deployment
The Dockerfile already includes Tesseract installation:
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libmagic1
```
- **Docker**: Works automatically, tesseract is in PATH
- **Docker Compose**: Uses the same Dockerfile, no additional setup needed

### Cloud Platform Deployment

#### AWS (Elastic Beanstalk/ECS/EKS)
1. **Using Docker**: Use the provided Dockerfile - Tesseract is automatically installed
2. **Using Platform-as-a-Service**: Add Tesseract to your build configuration:
   ```yaml
   # .ebextensions/tesseract.config (Elastic Beanstalk)
   packages:
     yum:
       tesseract: []
       tesseract-devel: []
       poppler-utils: []
   ```
3. **EC2/ECS with custom AMI**: Install Tesseract system packages:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

   # Amazon Linux 2/CentOS/RHEL
   sudo yum install -y epel-release
   sudo yum install -y tesseract tesseract-devel poppler-utils
   ```

#### Render/Railway/Heroku
1. **Using Docker**: Recommended approach - use the provided Dockerfile
2. **Using Buildpacks**: Add Tesseract via Aptfile or build script:
   ```bash
   # Aptfile (Render/Heroku)
   tesseract-ocr
   libtesseract-dev
   poppler-utils
   ```
3. **Environment Variable**: Set `TESSERACT_PATH` if tesseract is installed to a non-standard location:
   ```
   TESSERACT_PATH=/usr/bin/tesseract
   ```

#### Google Cloud Run/App Engine
1. **Docker**: Use the provided Dockerfile
2. **Custom Runtime**: Add Tesseract to your `Dockerfile` or `app.yaml`:
   ```yaml
   # app.yaml (App Engine Flex)
   runtime: custom
   env: flex
   ```
3. **Install via apt-get** in your Dockerfile as shown above

#### Azure App Service
1. **Docker**: Use the provided Dockerfile
2. **Custom Image**: Build with Tesseract pre-installed
3. **Startup Command**: Ensure Tesseract is in PATH

### Verification and Troubleshooting

#### Verify Tesseract Installation
```bash
# Check if tesseract is available
python -c "import pytesseract; print(f'Tesseract path: {pytesseract.pytesseract.tesseract_cmd}')"

# Test OCR functionality
python -c "
import pytesseract
from PIL import Image
import io
# Create a simple test image
from PIL import Image, ImageDraw
img = Image.new('RGB', (100, 50), color='white')
d = ImageDraw.Draw(img)
d.text((10, 10), 'Test', fill='black')
text = pytesseract.image_to_string(img)
print(f'OCR Test: {text}')
"
```

#### Common Issues and Solutions
1. **"Tesseract not found" error**:
   - Install Tesseract system package: `apt-get install tesseract-ocr` or `yum install tesseract`
   - Set `TESSERACT_PATH` environment variable to the full path of tesseract executable
   - On Windows cloud instances: Download Tesseract and set `TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe`

2. **Language support**:
   - Install additional language packs: `apt-get install tesseract-ocr-eng tesseract-ocr-hin`
   - For Indian languages (Hindi, Tamil, etc.): `apt-get install tesseract-ocr-hin tesseract-ocr-tam tesseract-ocr-tel`

3. **Memory/performance issues**:
   - Limit concurrent OCR operations in `document_processor.py`
   - Increase container memory allocation for large document processing

### Environment Variables for OCR
- `TESSERACT_PATH`: Override automatic tesseract detection (e.g., `/usr/bin/tesseract`)
- `OCR_ENABLED`: Set to `false` to disable OCR functionality entirely
- `MAX_OCR_THREADS`: Limit concurrent OCR operations (default: 3)

## Deployment

### Docker Deployment
The `docker-compose.yml` includes:
- PostgreSQL database with health checks
- Redis cache for Celery tasks
- FastAPI application with auto-reload in development
- Celery worker and beat services (planned)

### Cloud Deployment Options
- AWS: ECS/EKS with RDS PostgreSQL
- Render: Managed Python/PostgreSQL
- Railway: Easy deployment with PostgreSQL