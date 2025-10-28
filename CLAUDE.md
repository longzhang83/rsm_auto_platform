# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Accounting Voucher Generation project is a modern, bilingual (Chinese-English) web application for generating accounting vouchers from expense spreadsheets. It features a frontend-backend separation architecture with Vue.js SPA frontend and FastAPI REST API backend.

## Tech Stack

- **Backend**: Python 3.10+ with FastAPI (modern RESTful API)
- **Frontend**: Vue.js 3 + Vite + UnoCSS (SPA)
- **Data Processing**: pandas, openpyxl, xlrd
- **Translation**: ZhipuAI GLM API with caching
- **Package Management**: uv (modern Python package manager) + npm
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
- **chatglm.py**: ZhipuAI GLM integration with rate limiting and caching
- **cli.py**: Command-line interface

#### 2. Backend Services (`backend/app/services/`)
- **voucher_service.py**: Voucher generation business logic
- **translate_service.py**: Translation service orchestration

#### 3. API Endpoints (`backend/app/api/v1/endpoints/`)
- **vouchers.py**: Voucher generation endpoints
- **translate.py**: Translation endpoints

#### 4. Data Models (`backend/app/schemas/`)
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

# Install backend dependencies
cd backend && uv sync

# Install frontend dependencies
cd frontend && npm install

# Set environment variable for translation API
export ZHIPUAI_API_KEY=your_api_key  # Linux/Mac
# OR
set ZHIPUAI_API_KEY=your_api_key     # Windows
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

#### System
- `GET /` - Root information
- `GET /health` - Health check endpoint

### API Architecture Features

- **CORS Configuration**: Supports frontend development server
- **File Upload Handling**: Multi-format support (.xlsx, .xls, .csv)
- **Streaming Responses**: Efficient file downloads
- **Error Handling**: Comprehensive HTTP exception handling
- **Auto Documentation**: OpenAPI/Swagger generation

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

### Testing Strategy
1. **Backend Tests**: pytest with async support
2. **API Testing**: Integration tests for endpoints
3. **Error Handling**: Comprehensive exception testing

## Special Features

### Translation System
- **Rate Limiting**: Respects API rate limits (0.6 RPS default)
- **Caching**: LRU cache + persistent CSV mapping
- **Batch Processing**: Efficient bulk translation
- **Format Support**: Chinese-English format (e.g., "差旅费-Business travel expenses")

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

- `ZHIPUAI_API_KEY`: ZhipuAI API key for translation (required)
- `DEBUG`: Enable debug mode
- `HOST`: Backend server host (default: 0.0.0.0)
- `PORT`: Backend server port (default: 8888)

## Working with This Codebase

### Key Entry Points
1. **Backend Server**: `backend/app/main.py`
2. **Frontend Application**: `frontend/src/main.js`
3. **CLI Tool**: `main.py`
4. **Core Logic**: `src/accounting_voucher_generation/pipeline.py`

### Common Development Tasks
1. **Start Development**: Use `scripts\start-all.bat`
2. **API Testing**: Visit http://localhost:8888/docs
3. **Add New Endpoints**: Create in `backend/app/api/v1/endpoints/`
4. **Add Business Logic**: Implement in `backend/app/services/`
5. **Frontend Features**: Develop in `frontend/src/`

### Error Handling Guidelines
- Use FastAPI's `HTTPException` for API errors
- Provide detailed error messages in Chinese for user-facing errors
- Log technical errors for debugging
- Graceful fallbacks for optional features

This codebase demonstrates modern Python web development with FastAPI, Vue.js, and clean architecture principles.