# Tesseract OCR Cloud Deployment Guide

## Summary

For cloud deployment of the Legal Analysis SAAS with OCR functionality:

### 1. Docker Deployment (Recommended)
The provided `Dockerfile` already includes Tesseract installation:
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libmagic1
```
- Tesseract is automatically installed and added to PATH
- No additional configuration needed for Linux containers

### 2. Environment Variables
- `TESSERACT_PATH`: Optional - Set if Tesseract is installed in non-standard location
- `OCR_ENABLED`: Set to `false` to disable OCR entirely (default: `true`)

### 3. Cloud Platform Specific Instructions

#### AWS (ECS/EKS/Elastic Beanstalk)
- **With Docker**: Use the provided Dockerfile
- **Without Docker**: Add Tesseract to your instance:
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

  # Amazon Linux 2/CentOS/RHEL
  sudo yum install -y epel-release
  sudo yum install -y tesseract tesseract-devel poppler-utils
  ```

#### Render/Railway/Heroku
- **With Docker**: Use the provided Dockerfile
- **With Buildpacks**: Add `tesseract-ocr` to Aptfile:
  ```
  tesseract-ocr
  libtesseract-dev
  poppler-utils
  ```

#### Google Cloud Run / App Engine
- Use the provided Dockerfile
- Tesseract will be installed automatically

#### Azure App Service
- Use custom Docker image with the provided Dockerfile
- Ensure Tesseract is in PATH

### 4. Verification
Test Tesseract installation:
```bash
# Run the verification script
python test_tesseract.py

# Or manually check
python -c "import pytesseract; print(f'Tesseract path: {pytesseract.pytesseract.tesseract_cmd}')"
```

### 5. Troubleshooting

#### Common Issues
1. **Tesseract not found**: Install system package or set `TESSERACT_PATH`
2. **OCR fails silently**: Check logs for Tesseract errors
3. **Memory issues**: Limit concurrent OCR operations in cloud environments

#### Language Support
For Indian language OCR, install additional packages:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-tam

# Update Dockerfile
RUN apt-get install -y tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-tam
```

### 6. Windows Development Note
- The `python-magic` library may cause segfaults on Windows
- Install `python-magic-bin` for Windows: `pip install python-magic-bin`
- Install Tesseract manually from: https://github.com/UB-Mannheim/tesseract/wiki
- Set `TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe`

### 7. Performance Considerations
- OCR is CPU-intensive; size cloud instances appropriately
- Consider async processing with Celery for large documents
- Implement caching for frequently processed documents

## Files Updated
1. `src/config/settings.py` - Added TESSERACT_PATH and OCR_ENABLED settings
2. `src/services/document_processor.py` - Improved Tesseract detection and error handling
3. `CLAUDE.md` - Added comprehensive deployment documentation
4. `.env.example` - Added new environment variables
5. `test_tesseract.py` - Verification script
6. `example_ocr_test.py` - Example usage

## Quick Start for Cloud Deployment
```bash
# 1. Build and push Docker image
docker build -t legal-analysis-saas .
docker tag legal-analysis-saas your-registry/legal-analysis-saas
docker push your-registry/legal-analysis-saas

# 2. Set environment variables
# - DATABASE_URL (PostgreSQL connection)
# - DEEPSEEK_API_KEY
# - INDIAN_KANOON_API_KEY (optional)
# - TESSERACT_PATH (optional, default auto-detected)
# - OCR_ENABLED (optional, default true)

# 3. Deploy to your cloud platform
# Follow platform-specific deployment instructions
```

The application is now cloud-ready with robust OCR configuration.