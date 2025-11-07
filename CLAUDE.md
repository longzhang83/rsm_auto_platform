# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Accounting Voucher Generation project is a modern, bilingual (Chinese-English) web application for generating accounting vouchers from expense spreadsheets. It features a frontend-backend separation architecture with Vue.js SPA frontend and FastAPI REST API backend.

## Tech Stack

- **Backend**: Python 3.10+ with FastAPI (modern RESTful API)
- **Frontend**: Vue.js 3 + Vite + UnoCSS (SPA)
- **Data Processing**: pandas, openpyxl, xlrd
- **Translation**: ZhipuAI GLM API with multi-account support and caching
- **Package Management**: uv (modern Python package manager) + npm
- **Logging**: Custom enterprise-grade logging system with web API management
- **Architecture**: Layered architecture with service layer, API versioning

## Architecture Overview

### Frontend-Backend Separation

1. **Frontend** (`frontend/`): Vue.js SPA providing user interface
2. **Backend** (`backend/app/`): FastAPI RESTful API with layered architecture
3. **Core Logic** (`src/accounting_voucher_generation/`): Reusable business logic
4. **CLI Tool** (`main.py`): Command-line interface for automation

### Backend Architecture (FastAPI Best Practices)

#### Layered Structure:
- **API Layer** (`api/`): HTTP request handling, routing, and responses
- **Service Layer** (`services/`): Business logic implementation
- **Schema Layer** (`schemas/`): Data validation and serialization using Pydantic
- **Core Layer** (`core/`): Configuration and infrastructure
- **Utils Layer** (`utils/`): Utility functions

#### API Versioning:
- `/api/v1/` endpoints for current version
- Future-proof design for `/api/v2/`, etc.

### Core Components

#### 1. Business Logic (`src/accounting_voucher_generation/`)
- **pipeline.py**: Core voucher generation with `VoucherConfig` and `generate_vouchers()`
- **summary_translator.py**: Translation service with batch processing
- **chatglm_v2.py**: Updated async multi-account ZhipuAI GLM integration with rate limiting and caching
- **async_translator.py**: Enhanced async translation system with load balancing
- **translation_interface.py**: Unified translation interface for multiple providers
- **multi_account_translator.py**: Multi-account load balancing and error handling
- **bank_statement_pipeline.py**: Bank statement processing and voucher generation
- **cli.py**: Command-line interface

#### 2. Backend Services (`backend/app/services/`)
- **voucher_service.py**: Voucher generation business logic
- **translate_service.py**: Translation service orchestration with progress tracking

#### 3. API Endpoints (`backend/app/api/v1/endpoints/`)
- **vouchers.py**: Voucher generation endpoints
- **translate.py**: Translation endpoints
- **translate_v2.py**: Enhanced translation with SSE progress streaming
- **bank_statements.py**: Bank statement processing and voucher generation endpoints
- **progress.py**: Real-time progress tracking endpoints
- **logs.py**: Log management endpoints for enterprise monitoring

#### 4. Infrastructure (`backend/app/utils/`)
- **logger.py**: Enterprise-grade logging system with multiple outputs and web API management
- **progress_manager.py**: Task progress tracking with SSE streaming

#### 5. Data Models (`backend/app/schemas/`)
- **voucher.py**: Voucher-related Pydantic models
- **translate.py**: Translation-related Pydantic models

## Key Directories and Files

```
accounting-voucher-generation/
├── backend/                     # FastAPI backend application
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── core/               # Configuration and settings
│   │   ├── api/                # API routes and versioning
│   │   │   └── v1/             # API v1 endpoints
│   │   ├── services/           # Business logic layer
│   │   ├── schemas/            # Pydantic models
│   │   └── utils/              # Utility functions
│   ├── tests/                  # Backend tests
│   └── requirements.txt        # Backend dependencies
├── frontend/                   # Vue.js SPA frontend
│   ├── src/                    # Vue source code
│   ├── package.json            # Frontend dependencies
│   └── vite.config.js          # Vite configuration
├── src/                        # Core business logic (reusable)
│   └── accounting_voucher_generation/
│       ├── pipeline.py         # Voucher generation logic
│       ├── summary_translator.py
│       ├── chatglm.py          # Translation integration
│       └── cli.py              # CLI interface
├── data/                       # Data files
│   ├── Expense.xlsx           # Main expense file (required)
│   ├── 人员列表.xlsx           # Employee list (optional)
│   ├── 科目映射.csv            # Subject mapping (optional)
│   └── translation_mapping.csv # Translation cache
├── docs/                       # Documentation
│   └── BACKEND_STRUCTURE.md    # Architecture documentation
├── scripts/                    # Startup and utility scripts
│   ├── start-all.bat          # Start both frontend and backend
│   └── start-backend.bat      # Start backend only
├── main.py                     # CLI entry point
├── pyproject.toml              # Project configuration
└── README.md                   # Project documentation
```

## Development Workflow

### Setup Instructions

```bash
# Install uv (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install core business logic
pip install -e .

# Install backend dependencies (includes dev tools)
cd backend && uv sync

# Install frontend dependencies
cd frontend && npm install

# Create and configure environment variables (REQUIRED)
cp .env.example .env
# Edit .env with your configuration - NEVER use hardcoded parameters!
```

### Environment Configuration (.env)

**🚨 CRITICAL: Always use .env configuration - NEVER hardcode parameters in code!**

Create a `.env` file in the project root:

```bash
# Translation API Configuration (Required)
ZHIPUAI_API_KEY=your_single_api_key                                    # Single key (legacy)
ZHIPUAI_API_KEYS=key1,key2,key3                                       # Multiple keys (recommended)
ZHIPUAI_MODEL=glm-4.5-flash                                            # GLM model name
ZHIPUAI_SYSTEM_PROMPT=You are a professional translator...              # Custom system prompt
ZHIPUAI_RPS=18.0                                                       # Per-account rate limit

# Logging Configuration
LOG_LEVEL=INFO                                                         # DEBUG/INFO/WARNING/ERROR/CRITICAL
LOG_ENABLE_CONSOLE=true                                                # Console output
LOG_ENABLE_FILE=true                                                   # File output
LOG_ENABLE_JSON=false                                                  # JSON format logging
LOG_COLORED_CONSOLE=true                                               # Colored console output
LOG_MAX_FILE_SIZE=10485760                                             # 10MB max file size
LOG_BACKUP_COUNT=5                                                     # Number of backup files
LOG_RETENTION_DAYS=30                                                  # Days to retain logs

# Application Configuration
ENVIRONMENT=development                                                # development/production
DEBUG=false                                                           # Debug mode
HOST=0.0.0.0                                                         # Backend server host
PORT=8888                                                            # Backend server port

# File Processing Configuration
MAX_FILE_SIZE=52428800                                                # 50MB max file size
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv                                    # Allowed file extensions
UPLOAD_DIR=uploads                                                   # File upload directory
OUTPUT_DIR=outputs                                                   # Output directory
```

### Running the Application

#### Full Stack Application (Recommended)
```bash
# Use the convenience script
scripts\start-all.bat  # Windows
bash scripts/start-all.sh  # Linux/Mac
```

#### Individual Services
```bash
# Backend only
scripts\start-backend.bat          # Windows
bash scripts/start-backend.sh     # Linux/macOS
# OR
cd backend && uv run uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev
```

### Access Points

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8888
- **API Documentation**: http://localhost:8888/docs
- **Health Check**: http://localhost:8888/health

## API Design

### Current Endpoints

#### Voucher Management
- `POST /api/v1/vouchers/generate` - Generate accounting vouchers

#### Translation Service
- `POST /api/v1/translate/translate` - Translate summary texts
- `POST /api/v1/translate/batch` - Batch translation with SSE progress streaming

#### Bank Statement Processing
- `POST /api/v1/bank-statements/generate/start` - Start bank statement voucher generation (async with progress)
- `POST /api/v1/bank-statements/generate/cancel/{task_id}` - Cancel bank statement generation task
- `GET /api/v1/bank-statements/generate/result/{task_id}` - Get bank statement generation result
- `POST /api/v1/bank-statements/generate` - Generate bank statement vouchers (sync)
- `GET /api/v1/bank-statements/customers` - Get available customers
- `GET /api/v1/bank-statements/mapping/{customer_name}` - Get customer field mapping configuration
- `POST /api/v1/bank-statements/preview` - Preview bank statement data
- `GET /api/v1/bank-statements/download/{task_id}` - Download generated Excel file
- `GET /api/v1/bank-statements/download-file/{filename}` - Download bank statement result file
- `GET /api/v1/bank-statements/info` - Get bank statement feature information
- `POST /api/v1/bank-statements/validate` - Validate bank statement file format

#### Progress Tracking
- `GET /api/v1/progress/{task_id}` - Get task progress
- `GET /api/v1/progress/{task_id}/stream` - SSE stream for real-time progress

#### Log Management
- `GET /api/v1/logs/info` - Get logging system configuration
- `GET /api/v1/logs/files` - List all log files
- `GET /api/v1/logs/view/{filename}` - View log file content
- `GET /api/v1/logs/search` - Search across log files
- `GET /api/v1/logs/download/{filename}` - Download log file
- `DELETE /api/v1/logs/cleanup` - Clean up old log files

#### System
- `GET /` - Root information
- `GET /health` - Health check endpoint

### API Architecture Features

- **CORS Configuration**: Supports frontend development server
- **File Upload Handling**: Multi-format support (.xlsx, .xls, .csv) with validation
- **Streaming Responses**: Efficient file downloads and SSE progress streaming
- **Error Handling**: Comprehensive HTTP exception handling with internationalization
- **Auto Documentation**: OpenAPI/Swagger generation with interactive docs
- **Enterprise Logging**: Integrated logging system with web API management
- **Progress Tracking**: Real-time task progress monitoring with Server-Sent Events

## Development Patterns

### Backend Development
1. **Layered Architecture**: Clear separation between API, service, and model layers
2. **Dependency Injection**: FastAPI's dependency system for reusable components
3. **Type Safety**: Full type hints with Pydantic validation
4. **Async Programming**: Non-blocking request handling
5. **Configuration Management**: Environment-based configuration with Pydantic Settings

### Frontend Development
1. **Component-Based**: Vue.js composition API
2. **State Management**: Pinia for application state
3. **API Communication**: Axios with proxy configuration
4. **Styling**: UnoCSS for utility-first styling

### Testing and Quality Assurance

```bash
# Run backend tests
cd backend && uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Code formatting and linting
uv run black .
uv run isort .
uv run mypy app/

# Run specific test
uv run pytest tests/test_api/test_vouchers.py -v
```

### Testing Strategy
1. **Backend Tests**: pytest with async support and coverage reporting
2. **API Testing**: Integration tests for endpoints
3. **Error Handling**: Comprehensive exception testing
4. **Code Quality**: Black formatting, isort imports, mypy type checking

## Special Features

### Translation System
- **Multi-Account Support**: Load balancing across multiple ZhipuAI API keys
- **Rate Limiting**: Configurable per-account rate limiting (0.6 RPS default per account)
- **Caching**: LRU cache + persistent CSV mapping for performance
- **Batch Processing**: Efficient bulk translation with progress tracking
- **Format Support**: Chinese-English format (e.g., "差旅费-Business travel expenses")
- **SSE Streaming**: Real-time progress updates via Server-Sent Events

### Bank Statement Processing (Updated per PRD)
- **Data Standardization**: Automatically handles different bank statement formats
  - Supports dual amount columns (debit/credit) or single amount column (positive=debit, negative=credit)
  - Auto-maps payer/payee names to counterparty based on transaction direction
  - Auto-maps payer/payee accounts to bank account based on transaction direction
- **Triple Subject Mapping System**:
  1. **Bank Account Mapping**: Maps bank accounts to bank accounting subjects (for bank科目)
  2. **Summary Keyword Mapping**: Maps summary keywords to transaction counterparty subjects
  3. **Counterparty Name Mapping**: Maps counterparty names to accounting subjects
- **In-Memory Processing**: Complete memory-based processing with no temporary files
- **Excel Output Format**: PRD-compliant output (row 1 empty, row 2 headers, rows 3-4 sample data, actual data from row 5)

### Enterprise Logging System
- **Multiple Outputs**: Console, file, and JSON format logging
- **Log Rotation**: Automatic file rotation with configurable size and retention
- **Web API Management**: RESTful endpoints for log viewing, searching, and management
- **Module-specific Loggers**: Dedicated loggers for different components
- **Structured Logging**: JSON format support for log analysis tools
- **Auto-cleanup**: Configurable automatic cleanup of old log files

### File Processing
- **Multi-format Support**: .xlsx, .xls, .csv files
- **Fallback Parsing**: Multiple Excel engines (openpyxl, xlrd)
- **Validation**: File type and size validation
- **Streaming**: Memory-efficient large file handling

### Configuration Management
- **Environment Variables**: Support for .env files
- **Default Values**: Sensible defaults for all settings
- **Validation**: Pydantic-based configuration validation

## Environment Variables

**🚨 All configuration should be managed via .env file - see Environment Configuration (.env) section above.**

### Required Environment Variables

#### Translation API Configuration (Required)
- `ZHIPUAI_API_KEY`: Single ZhipuAI API key for translation (legacy support)
- `ZHIPUAI_API_KEYS`: Multiple API keys for load balancing (recommended, comma-separated)
- `ZHIPUAI_MODEL`: GLM model name (default: glm-4.5-flash)
- `ZHIPUAI_SYSTEM_PROMPT`: Custom system prompt for translation
- `ZHIPUAI_RPS`: Per-account rate limit (default: 18.0 for multi-account)

#### Logging Configuration (Optional)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL, default: INFO)
- `LOG_ENABLE_CONSOLE`: Enable console output (default: true)
- `LOG_ENABLE_FILE`: Enable file output (default: true)
- `LOG_ENABLE_JSON`: Enable JSON format logging (default: false)
- `LOG_COLORED_CONSOLE`: Enable colored console output (default: true)
- `LOG_MAX_FILE_SIZE`: Max log file size in bytes (default: 10MB)
- `LOG_BACKUP_COUNT`: Number of backup files to keep (default: 5)
- `LOG_RETENTION_DAYS`: Days to retain log files (default: 30)

#### Application Configuration (Optional)
- `ENVIRONMENT`: Application environment (development/production, default: development)
- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Backend server host (default: 0.0.0.0)
- `PORT`: Backend server port (default: 8888)

#### File Processing Configuration (Optional)
- `MAX_FILE_SIZE`: Maximum file size for uploads (default: 50MB)
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions
- `UPLOAD_DIR`: Directory for file uploads (default: uploads)
- `OUTPUT_DIR`: Directory for generated files (default: outputs)

## Working with This Codebase

### 🚨 Critical Memory Requirements
**Before starting any development work, you MUST read:**
1. **`docs/MEMORY_CHECKLIST.md`** - Essential memory checklist for avoiding past mistakes
2. **`docs/TROUBLESHOOTING_GUIDE.md`** - Common problems and solutions
3. **`docs/DEVELOPMENT_PATTERNS.md`** - Best practices and anti-patterns

### 📋 Bank Statement Processing Architecture
**Key Understanding for Bank Statement Module:**
1. **Triple Subject Mapping System**:
   - `map_bank_account_subject()`: Maps bank accounts → bank accounting subjects (for bank科目)
   - `map_subject_by_counterparty_or_summary()`: Maps transaction counterparty → accounting subjects
2. **Data Standardization Pipeline**:
   - `standardize_bank_statement_data()`: Handles different bank statement formats automatically
   - Supports single amount column (positive=debit, negative=credit) or dual debit/credit columns
   - Auto-maps payer/payee based on transaction direction
3. **In-Memory Processing**:
   - `generate_bank_statement_vouchers_from_bytes()`: Complete memory-based processing
   - No temporary files saved to disk
   - Direct Excel streaming to client

### 🎯 Key Lessons to Remember
1. **Function Parameter Matching**: Always check callback function signatures before calling
2. **Exception Handling**: Never let exceptions in callbacks interrupt the main flow
3. **File Resource Management**: Always use `with` statements for file operations
4. **Encoding Management**: Always specify `encoding='utf-8'` for text operations
5. **Structured Logging**: Include context, use proper encoding, handle Chinese characters

### 📋 Pre-Development Checklist
- [ ] Read `docs/MEMORY_CHECKLIST.md`
- [ ] Check function signatures for all callbacks
- [ ] Verify exception handling for all operations
- [ ] Ensure all file operations use `with` statements
- [ ] Review dependency requirements

### 🔧 Development Memory Prompts
When you encounter these keywords, immediately check the relevant documentation:
- "callback" → Check function parameter matching in MEMORY_CHECKLIST.md
- "async" → Review async patterns in DEVELOPMENT_PATTERNS.md
- "file" → Check file operation patterns in DEVELOPMENT_PATTERNS.md
- "progress" → Check progress callback patterns in TROUBLESHOOTING_GUIDE.md
- "encoding" → Always specify encoding='utf-8' for text operations

### Key Entry Points
1. **Backend Server**: `backend/app/main.py`
2. **Frontend Application**: `frontend/src/main.js`
3. **CLI Tool**: `main.py`
4. **Core Logic**: `src/accounting_voucher_generation/pipeline.py`

### Common Development Tasks
1. **Start Development**: Use `scripts\start-all.bat`
2. **API Testing**: Visit http://localhost:8888/docs
3. **Log Management**: Use endpoints at http://localhost:8888/api/v1/logs/
4. **Add New Endpoints**: Create in `backend/app/api/v1/endpoints/` and update `router.py`
5. **Add Business Logic**: Implement in `backend/app/services/`
6. **Frontend Features**: Develop in `frontend/src/`
7. **Clear Translation Cache**: `uv run python -c "from src.accounting_voucher_generation.chatglm_v2 import clear_translation_cache; clear_translation_cache(drop_mapping_cache=True)"`

### Configuration Management Best Practices
- **🚨 NEVER hardcode API keys, passwords, or configuration values in code**
- **Always use environment variables via .env file for configuration**
- **Use `backend/app/core/config.py` Pydantic settings for type-safe configuration**
- **Validate all environment variables on application startup**
- **Provide sensible defaults for optional configuration values**

### Error Handling Guidelines
- Use FastAPI's `HTTPException` for API errors with proper status codes
- Provide detailed error messages in Chinese for user-facing errors
- Log technical errors using the enterprise logging system with appropriate levels
- Implement graceful fallbacks for optional features
- Use structured logging for complex error scenarios

### Translation Performance Optimization
- Use multi-account API keys for high-throughput translation
- Monitor progress via SSE streaming endpoints for long-running tasks
- Configure appropriate rate limits based on API quota
- Leverage translation caching to reduce API calls

### Log Management
- Monitor application health via `/api/v1/logs/info`
- Search logs via `/api/v1/logs/search` for debugging
- Configure log retention based on storage constraints
- Use JSON logging for integration with log analysis tools

This codebase demonstrates modern Python web development with FastAPI, Vue.js, enterprise-grade logging, and clean architecture principles, with comprehensive bank statement processing capabilities following PRD specifications.
