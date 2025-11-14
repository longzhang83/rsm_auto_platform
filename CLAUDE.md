# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Accounting Voucher Generation project is a bilingual (Chinese-English) web application for generating accounting vouchers from expense spreadsheets and bank statements. It features a frontend-backend separation architecture with Vue.js SPA frontend and FastAPI REST API backend.

## Tech Stack

- **Backend**: Python 3.10+ with FastAPI, layered architecture with API versioning
- **Frontend**: Vue.js 3 + Vite + UnoCSS, Pinia state management
- **Data Processing**: pandas, openpyxl, xlrd
- **Translation**: ZhipuAI GLM API with async multi-account load balancing, rate limiting, and LRU+CSV caching
- **Authentication**: JWT tokens, email verification, optional WeWork SSO integration
- **Package Management**: uv (Python) + npm (frontend)
- **Logging**: Enterprise-grade system with rotation, web API management, and search capabilities

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

#### Business Logic (`src/accounting_voucher_generation/`)
Core voucher generation and translation logic that can be used standalone or through the API:
- **pipeline.py**: Main voucher generation with `VoucherConfig` and `generate_vouchers()`
- **bank_statement_pipeline.py**: Bank statement processing with triple subject mapping system
- **chatglm_v2.py**: Async multi-account ZhipuAI integration with rate limiting (18 RPS default)
- **async_translator.py**: Async translation with load balancing across API keys
- **summary_translator.py**: Batch translation with progress tracking

#### Backend Services (`backend/app/services/`)
Business logic layer separating API concerns from implementation:
- **voucher_service.py**: Voucher generation orchestration
- **translate_service.py**: Translation service with SSE progress streaming
- **auth_service.py**: User registration, login, password management
- **verification_service.py**: Email verification code generation and validation
- **wework_service.py**: WeWork SSO integration (optional)

#### API Endpoints (`backend/app/api/v1/endpoints/`)
RESTful endpoints with versioning support:
- **vouchers.py**: Voucher generation from expense files
- **translate.py, translate_v2.py**: Translation with progress streaming
- **bank_statements.py**: Bank statement voucher generation with async progress
- **auth.py**: Authentication, registration, email verification
- **progress.py**: Real-time SSE progress streams
- **logs.py**: Log management and search API

#### Infrastructure (`backend/app/`)
- **utils/logger.py**: Multi-output logging with rotation and web API
- **utils/progress_manager.py**: SSE-based progress tracking
- **core/config.py**: Pydantic settings with .env support
- **db/**: SQLAlchemy models and database setup

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

### Key Endpoints (Full list at http://localhost:8888/docs)

#### Authentication & User Management
- `POST /api/v1/auth/register` - User registration with email verification
- `POST /api/v1/auth/login` - JWT token authentication
- `POST /api/v1/auth/send-verification-code` - Send email verification code
- `GET /api/v1/auth/email-domains` - Get allowed email domains (configured via .env)
- `POST /api/v1/auth/wework/callback` - WeWork SSO callback

#### Voucher & Translation
- `POST /api/v1/vouchers/generate` - Generate vouchers from expense files
- `POST /api/v1/translate/batch` - Batch translation with SSE progress
- `POST /api/v1/bank-statements/generate/start` - Async bank statement processing
- `GET /api/v1/bank-statements/download/{task_id}` - Download generated Excel

#### Monitoring
- `GET /api/v1/progress/{task_id}/stream` - SSE stream for real-time progress
- `GET /api/v1/logs/search` - Search logs with filtering
- `GET /health` - Health check

### Key API Features

- **SSE Progress Streaming**: Long-running tasks report progress via Server-Sent Events
- **Multi-format File Upload**: .xlsx, .xls, .csv with validation and size limits
- **In-Memory Processing**: Bank statements processed entirely in memory, no temp files
- **JWT Authentication**: Token-based auth with optional WeWork SSO
- **API Versioning**: `/api/v1/` prefix for future compatibility

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
# Backend tests with coverage
cd backend && uv run pytest --cov=app --cov-report=html

# Code formatting
uv run black .
uv run isort .

# Type checking
uv run mypy app/

# Specific test
uv run pytest tests/test_api/test_vouchers.py -v
```

## Special Features & Architecture Insights

### Translation System Architecture
**Multi-Account Load Balancing**: The translation system distributes requests across multiple ZhipuAI API keys for higher throughput. Key implementation details:
- `chatglm_v2.py`: Async client with per-account rate limiting (configurable RPS)
- `async_translator.py`: Load balancer managing multiple API key instances
- **Caching Strategy**: Two-level cache (LRU in-memory + CSV persistence) to minimize API calls
- **Progress Tracking**: Integration with `progress_manager.py` for SSE streaming
- **Format**: Output as "中文-English translation" (e.g., "差旅费-Business travel expenses")

### Bank Statement Processing Architecture
**Triple Subject Mapping System** - Critical to understand for bank statement features:

1. **Data Standardization Pipeline** (`standardize_bank_statement_data()`):
   - Handles both dual columns (借方/贷方) and single column (正负数) formats
   - Auto-determines transaction direction from amount signs
   - Maps payer/payee to counterparty based on direction (debit uses payer, credit uses payee)

2. **Subject Mapping Cascade**:
   - `map_bank_account_subject()`: Bank account → Bank科目 (for "bank科目" field)
   - `map_subject_by_counterparty_or_summary()`: Counterparty/Summary → Accounting科目
   - Priority: Counterparty name → Summary keywords → Default

3. **In-Memory Processing**: `generate_bank_statement_vouchers_from_bytes()` processes entirely in memory without temp files, returns Excel bytes directly for streaming download

### Authentication Architecture
**Dual Login System**:
- **Primary**: Email + password with JWT tokens
- **Secondary**: WeWork SSO integration (optional, configured via .env)
- **Email Verification**: Random 6-digit codes stored in database with expiry
- **Domain Restriction**: `ALLOWED_EMAIL_DOMAINS` enforced at both frontend and backend
- Frontend fetches allowed domains dynamically from `/api/v1/auth/email-domains` (no hardcoding)

### Progress Tracking Architecture
**SSE-Based Real-Time Progress**:
- `ProgressManager` class maintains in-memory progress state per task_id
- Progress updates via `update_progress(task_id, percentage, message)`
- Frontend connects to `/api/v1/progress/{task_id}/stream` for SSE events
- **Critical Pattern**: Always wrap callbacks with proper exception handling to prevent progress interruption (see `docs/MEMORY_CHECKLIST.md`)

### Logging Architecture
**Enterprise-Grade Multi-Output System**:
- Configured entirely via `.env` (levels, outputs, rotation, retention)
- **Multiple Outputs**: Console (with color), file (with rotation), JSON (for log analysis)
- **Module-Specific**: Each major component has its own logger (`logger.get_logger(__name__)`)
- **Web API**: Search, download, and cleanup endpoints for operational management
- **Chinese Character Support**: Proper UTF-8 encoding throughout

## Environment Variables

**🚨 CRITICAL: Never hardcode configuration - always use .env file (see `.env.example` for all options)**

### Key Configuration Groups

#### Translation API (Required for translation features)
- `ZHIPUAI_API_KEYS`: Multiple API keys for load balancing (comma-separated, **recommended**)
- `ZHIPUAI_API_KEY`: Single API key (legacy, still supported)
- `ZHIPUAI_MODEL`: GLM model (default: glm-4.5-flash)
- `ZHIPUAI_RPS`: Per-account rate limit (default: 18.0)

#### Authentication & Email (Required for user features)
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Email verification config
- `ALLOWED_EMAIL_DOMAINS`: Allowed registration domains (comma-separated, e.g., "rsmchina.com.cn,example.com")
- `VERIFICATION_CODE_EXPIRY`: Code validity in seconds (default: 300)

#### WeWork SSO (Optional)
- `WEWORK_ENABLED`: Enable WeWork login (default: false)
- `WEWORK_CORP_ID`, `WEWORK_AGENT_ID`, `WEWORK_SECRET`, `WEWORK_CALLBACK_URL`

#### Logging (Optional, has sensible defaults)
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR/CRITICAL (default: INFO)
- `LOG_ENABLE_CONSOLE`, `LOG_ENABLE_FILE`, `LOG_ENABLE_JSON`
- `LOG_MAX_FILE_SIZE`, `LOG_BACKUP_COUNT`, `LOG_RETENTION_DAYS`

#### Application (Optional)
- `ENVIRONMENT`: development/production (default: development)
- `HOST`, `PORT`: Server binding (defaults: 0.0.0.0:8888)
- `MAX_FILE_SIZE`: Upload limit (default: 50MB)

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

**Add New API Endpoint**:
1. Create endpoint function in `backend/app/api/v1/endpoints/<module>.py`
2. Add Pydantic request/response schemas in `backend/app/schemas/`
3. Implement business logic in `backend/app/services/<service>.py`
4. Register route in `backend/app/api/v1/router.py`
5. Test at http://localhost:8888/docs

**Add Translation Feature**:
- Use `async_translator.py` for multi-account load balancing
- Always integrate with `progress_manager.py` for long-running tasks
- Leverage CSV cache in `data/translation_mapping.csv`

**Add Bank Statement Mapping**:
- Edit customer configs in `data/bank_statements/<customer>/` directories
- Update `standardize_bank_statement_data()` if adding new bank format
- Test with `/api/v1/bank-statements/preview` before full generation

**Clear Translation Cache**:
```bash
uv run python -c "from src.accounting_voucher_generation.chatglm_v2 import clear_translation_cache; clear_translation_cache(drop_mapping_cache=True)"
```

**Search Logs for Debugging**:
```bash
curl "http://localhost:8888/api/v1/logs/search?query=error&level=ERROR"
```

### Critical Development Patterns

**Configuration Management**:
- ✅ Always use `.env` file and `backend/app/core/config.py` Pydantic Settings
- ✅ Provide sensible defaults for optional settings
- ❌ NEVER hardcode API keys, domains, or configuration values

**Error Handling**:
- ✅ Use FastAPI's `HTTPException` with proper status codes
- ✅ Provide Chinese error messages for user-facing errors
- ✅ Log exceptions with full context using `logger.error(f"...", exc_info=True)`
- ❌ Never let callback exceptions interrupt main flow (wrap in try-except)

**File Operations**:
- ✅ Always use `with` statements for file operations
- ✅ Always specify `encoding='utf-8'` for text files
- ✅ Process bank statements entirely in memory (no temp files)
- ❌ Never leave file handles open

**Progress Tracking**:
- ✅ Use `progress_manager.update_progress(task_id, percentage, message)`
- ✅ Wrap callbacks with exception handling to prevent interruption
- ✅ Verify math formulas before debugging complex issues (see `docs/MEMORY_CHECKLIST.md`)
- ❌ Don't assume SSE issues are concurrency problems - check the math first

This codebase demonstrates modern Python web development with FastAPI, Vue.js, enterprise-grade logging, and clean architecture principles.
