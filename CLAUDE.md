# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Accounting Voucher Generation project is a bilingual (Chinese-English) web application and CLI tool designed to generate accounting vouchers from expense spreadsheets. It uses FastAPI for the web interface and pandas for data processing, with translation capabilities provided by ZhipuAI's GLM model.

## Tech Stack

- **Backend**: Python 3.10+ with FastAPI
- **Data Processing**: pandas, openpyxl, xlrd
- **Translation**: ZhipuAI GLM API
- **Frontend**: HTML + Tailwind CSS + Vanilla JavaScript
- **Package Management**: uv (modern Python package manager)
- **Build System**: setuptools

## Architecture Overview

### Dual Interface Design

1. **Web Interface** (`app/main.py`): FastAPI-based web application
2. **CLI Interface** (`main.py`, `src/accounting_voucher_generation/cli.py`): Command-line tool

### Core Components

#### 1. Pipeline Module (`src/accounting_voucher_generation/pipeline.py`)
- Contains the main business logic for voucher generation
- `VoucherConfig` dataclass for configuration management
- `generate_vouchers()` function that orchestrates the entire process
- Handles data loading, mapping, translation, and voucher generation

#### 2. Translation Module (`src/accounting_voucher_generation/chatglm.py`)
- ZhipuAI GLM integration for Chinese-to-English translation
- Rate-limited API calls with caching
- Batch translation capabilities
- Persistent translation mapping storage

#### 3. CLI Interface (`src/accounting_voucher_generation/cli.py`)
- Command-line argument parsing
- Integration with pipeline module
- Comprehensive parameter support

#### 4. Web Application (`app/main.py`)
- FastAPI server with file upload handling
- Multi-format Excel file support (.xlsx, .xls)
- Streaming response for generated files
- Jinja2 templates for frontend

## Key Directories and Files

```
D:\360MoveData\Users\long\Desktop\accounting-voucher-generation├── app/                          # Web application directory
│   └── main.py                   # FastAPI application entry point
├── src/
│   └── accounting_voucher_generation/
│       ├── __init__.py           # Package initialization
│       ├── pipeline.py           # Core voucher generation logic
│       ├── cli.py                # CLI interface
│       └── chatglm.py            # Translation and AI integration
├── data/                         # Input data and generated outputs
│   ├── Expense.xlsx             # Main expense file (required)
│   ├── 人员列表.xlsx             # Employee list (optional)
│   ├── 科目映射.csv              # Subject mapping (optional)
│   ├── translation_mapping.csv  # Translation cache (auto-generated)
│   └── output/                  # Generated vouchers directory
│       ├── vouchers.csv         # CSV output
│       └── vouchers.xlsx        # Excel output
├── templates/
│   └── index.html               # Main web interface
├── static/
│   └── js/
│       └── app.js               # Frontend JavaScript
├── main.py                      # CLI entry point
├── pyproject.toml               # Project configuration
├── uv.lock                      # uv lock file
├── README.md                    # Project documentation (Chinese)
├── start.bat                    # Windows start script
└── start.sh                     # Unix-like start script
```

## Development Workflow

### Setup Instructions

```bash
# Install dependencies
pip install -e .
# OR using uv
uv pip install -e .

# Set environment variable for translation API
export ZHIPUAI_API_KEY=your_api_key
# OR on Windows
set ZHIPUAI_API_KEY=your_api_key
```

### Running the Application

#### Web Interface (Recommended)
```bash
# Start FastAPI server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8888
```
- Access at http://localhost:8888
- Upload files via web interface
- Download generated voucher bundle

#### Command Line Interface
```bash
# Basic usage
python main.py --data-dir data --output-dir data/output

# Advanced usage with custom parameters
python main.py   --expense-file Expense.xlsx   --employee-file "人员列表.xlsx"   --subject-file "科目映射.csv"   --translation-map "data/translation_mapping.csv"   --preparer "cissy"   --voucher-category "记"   --credit-account "224104"   --start-seq 0
```

### Build Process
- No explicit build process required
- Uses setuptools for package management
- Python wheels are built automatically with `pip install`

## Testing Approach
- No formal test suite found in the codebase
- Manual testing through both web interface and CLI
- Error handling and validation in production code

## Key Architectural Patterns

### 1. Configuration Management
- Centralized `VoucherConfig` dataclass with default values
- Path resolution and validation
- Extensible parameter system

### 2. Data Processing Pipeline
- DataFrame-based processing with pandas
- Flexible column mapping and validation
- Progress tracking with tqdm integration

### 3. Translation System
- LRU caching for translation results
- Batch processing for efficiency
- Rate limiting to respect API constraints
- Persistent mapping storage

### 4. Error Handling
- Comprehensive exception handling in web interface
- Graceful fallbacks for missing optional files
- Detailed error messages in Chinese

### 5. File Format Support
- Multi-version Excel support (.xlsx with openpyxl, .xls with xlrd)
- CSV support for mappings and translations
- Streaming responses for large files

## Special Development Practices

### API Integration
- Rate-limited API calls to ZhipuAI
- Automatic retry logic for failed translations
- Translation cache to avoid redundant calls

### Data Validation
- Column name standardization (strip whitespace)
- Amount validation and coercion
- Missing data handling

### Output Generation
- Dual output format (CSV and Excel)
- Automatic file type detection
- Bundle packaging with translation mapping updates

## Environment Variables
- `ZHIPUAI_API_KEY`: ZhipuAI API key for translation
- `TRANSLATION_MAP_PATH`: Custom translation mapping file path

## Default Configuration
- **Default preparer**: "cissy"
- **Default voucher category**: "记"
- **Default credit account**: "224104"
- **Default port**: 8888
- **Translation workers**: 3
- **Translation RPS**: 0.6

## Working with This Codebase

### File Requirements
- **Expense.xlsx**: Required main expense file
- **人员列表.xlsx**: Optional employee list
- **科目映射.csv**: Optional subject mapping
- **translation_mapping.csv**: Auto-generated translation cache

### Key Entry Points
1. **Web Application**: `app/main.py` - FastAPI server
2. **CLI Tool**: `main.py` - Command-line interface
3. **Core Logic**: `src/accounting_voucher_generation/pipeline.py`

### Common Operations
1. **Start development server**: Use `start.bat` or `start.sh`
2. **Clear translation cache**:
   ```bash
   uv run python -c "from src.accounting_voucher_generation.chatglm import clear_translation_cache; clear_translation_cache(drop_mapping_cache=True)"
   ```
3. **Customize translation mapping**: Edit `data/translation_mapping.csv`

### Error Handling
- Check status messages in web interface for detailed errors
- Verify file formats and column names match expected structure
- Ensure ZHIPUAI_API_KEY is properly set

This codebase demonstrates a well-structured approach to financial data processing with modern Python practices, providing both web and CLI interfaces while maintaining clean separation of concerns and robust error handling.