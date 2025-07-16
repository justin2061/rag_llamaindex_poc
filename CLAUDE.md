# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure API key
cp .env.example .env
# Edit .env file to set your GROQ_API_KEY
```

### Running the Application
```bash
# Basic version (now includes auto PDF discovery)
streamlit run app.py
# or
python run.py

# Enhanced version (recommended for advanced features)
streamlit run enhanced_app.py
# or
python run.py enhanced
```

### Testing
```bash
# Run PDF discovery test
python test_pdf_discovery.py
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up --build

# Run with shell scripts
./docker-run.sh    # Linux/Mac
docker-run.bat     # Windows
```

## Architecture Overview

This is a **RAG (Retrieval-Augmented Generation) system** for Taiwanese tea knowledge built with **LlamaIndex** and **Streamlit**. The system automatically downloads and processes PDF documents from Taiwan Tea Research and Extension Station to create a specialized tea knowledge base.

### Core Architecture
- **Frontend**: Streamlit web application (`app.py`, `enhanced_app.py`)
- **RAG Engine**: LlamaIndex framework (`rag_system.py`)
- **Document Processing**: Automatic PDF discovery and download (`enhanced_pdf_downloader.py`)
- **Configuration**: Centralized settings (`config.py`)
- **Utilities**: Helper functions (`utils.py`)

### Technology Stack
- **LLM**: Groq Llama3-70B-Versatile (`llama-3.3-70b-versatile`)
- **Embeddings**: HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector Store**: SimpleVectorStore (LlamaIndex built-in, file-based storage)
- **PDF Processing**: PyMuPDF (primary), with PyPDF2/pdfplumber fallbacks
- **UI Framework**: Streamlit

### Key Components

#### RAGSystem Class (`rag_system.py`)
- Handles model initialization (LLM + embeddings)
- Manages document loading and indexing
- Provides query interface for Q&A
- Uses SimpleVectorStore for vector storage with file persistence

#### PDF Processing Pipeline
1. **Auto-Discovery**: Automatically discovers PDF links from WEB_SOURCES using EnhancedPDFDownloader
2. **Batch Download**: Downloads all discovered PDFs with progress tracking
3. **Document Parsing**: Extracts text using PyMuPDF with fallback options
4. **Text Chunking**: Splits documents into 1024-character chunks
5. **Vector Indexing**: Creates embeddings and builds searchable index

#### State Management
- Uses Streamlit session state for system persistence
- Tracks initialization status and RAG system instance
- Manages download progress and system readiness

### Data Flow
```
User Input → Streamlit UI → RAG System → Vector Search → LLM Generation → Response
```

1. **Initialization**: Downloads PDFs from configured sources
2. **Document Processing**: Parses PDFs and creates text chunks
3. **Indexing**: Generates embeddings and builds vector index using SimpleVectorStore
4. **Query Processing**: Converts questions to vectors, retrieves relevant chunks
5. **Answer Generation**: Uses Groq LLM to generate responses based on retrieved context

### File Structure
```
├── app.py / enhanced_app.py     # Streamlit applications
├── rag_system.py                # RAG core logic
├── pdf_downloader.py            # PDF processing
├── enhanced_pdf_downloader.py   # Advanced PDF discovery
├── config.py                    # Configuration settings
├── utils.py                     # Utility functions
├── data/
│   ├── pdfs/                    # Downloaded PDF files
│   └── index/                   # Vector index storage (SimpleVectorStore files)
└── requirements.txt             # Python dependencies
```

### Configuration Sources
- **WEB_SOURCES**: URLs for automatic PDF discovery from Taiwan Tea Research Station website
- **PDF_SOURCES**: Legacy predefined URLs (still available but not used by default)
- **Models**: Configurable LLM and embedding models via `config.py`
- **Storage**: Index files stored locally in `data/index/` directory

### Key Changes
Both `app.py` and `enhanced_app.py` now use **WEB_SOURCES** for automatic PDF discovery instead of fixed PDF_SOURCES. The system will:
1. Scan Taiwan Tea Research Station web pages for PDF links
2. Download all discovered PDF files automatically
3. Process and index the documents for the knowledge base

## Development Notes

### Vector Storage
The system uses **SimpleVectorStore** (LlamaIndex's built-in vector store) which:
- Stores vectors as JSON files in the local filesystem
- Provides automatic persistence without external database dependencies
- Suitable for small to medium-scale document collections
- Can be upgraded to ChromaDB, Pinecone, or other vector databases if needed

### Error Handling
- Graceful fallbacks for PDF processing libraries
- Network error handling for PDF downloads
- API error handling for LLM queries
- User-friendly error messages in Streamlit interface

### Performance Considerations
- Index persistence avoids recomputation on restart
- Chunked document processing for memory efficiency
- Progress tracking for long-running operations
- Session state management for UI responsiveness