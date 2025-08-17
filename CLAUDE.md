# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure API keys
cp .env.example .env
# Edit .env file to set:
# - GROQ_API_KEY (required for LLM)
# - GEMINI_API_KEY (optional for OCR)
```

### Running the Application
```bash
# Main application with modular UI components
streamlit run main_app.py
# or
python run.py

# Enhanced version with all features
streamlit run enhanced_app.py
# or
python run.py enhanced

# Basic version
streamlit run app.py

# Quick start for testing
python quick_start.py

# Ultra fast start (minimal setup)
python ultra_fast_start.py

# Graph RAG specific version
python run_graphrag.py
```

### Testing
```bash
# Run PDF discovery test
python test_pdf_discovery.py

# Benchmark startup performance
python benchmark_startup.py
```

### Docker Deployment
```bash
# Standard deployment
docker-compose up --build

# Light deployment (volume bind, faster builds)
docker-compose -f docker-compose.light.yml up --build

# Elasticsearch RAG deployment
docker-compose -f docker-compose.elasticsearch.yml up --build

# Shell scripts for deployment
./docker-run.sh        # Linux/Mac
./docker-deploy.sh     # Linux/Mac deployment
docker-run.bat         # Windows
docker-deploy.bat      # Windows deployment
```

### Performance Benchmarking
```bash
# Run RAG system performance comparison
streamlit run rag_system_benchmark.py

# Memory usage monitoring
python -c "from rag_system_benchmark import RAGSystemBenchmark; RAGSystemBenchmark().run_full_benchmark()"
```

## Architecture Overview

This is an **advanced RAG (Retrieval-Augmented Generation) system** built with **LlamaIndex** and **Streamlit**. The system supports multiple RAG approaches including traditional vector-based retrieval, enhanced RAG with conversation memory, and cutting-edge Graph RAG for knowledge graph construction and reasoning.

### Core Architecture
- **Frontend**: Modular Streamlit UI with component-based architecture
  - `main_app.py`: Main application with modular components
  - `enhanced_app.py`: Full-featured version with all capabilities
  - `app.py`: Basic version for simple use cases
- **RAG Engines**: Multiple RAG implementations
  - `rag_system.py`: Base RAG system
  - `enhanced_rag_system.py`: Enhanced with memory and file management
  - `graph_rag_system.py`: Graph RAG with knowledge graph construction
- **Document Processing**: Multi-format document handling
  - `enhanced_pdf_downloader.py`: Advanced PDF discovery and download
  - `user_file_manager.py`: User upload management
  - `gemini_ocr.py`: OCR processing for images
- **Storage Systems**: Multiple vector store options
  - `chroma_vector_store.py`: ChromaDB integration
  - Built-in SimpleVectorStore support
- **Memory & Context**: Conversation management
  - `conversation_memory.py`: Multi-turn conversation context
- **Configuration**: Centralized settings (`config.py`)
- **Utilities**: Helper functions (`utils.py`)

### Technology Stack
- **LLM**: Groq Llama3-70B-Versatile (`llama-3.3-70b-versatile`)
- **Embeddings**: HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector Stores**: 
  - ChromaDB (recommended for production)
  - SimpleVectorStore (file-based, good for development)
- **Graph Processing**: NetworkX, Python-Louvain for community detection
- **Document Processing**: 
  - PyMuPDF (primary PDF processor)
  - PyPDF2, pdfplumber (fallback options)
  - python-docx (Word documents)
  - Pillow (image processing)
- **OCR**: Google Gemini Vision API
- **UI Framework**: Streamlit with custom components
- **Visualization**: Pyvis for knowledge graph visualization

### Key Components

#### RAG System Hierarchy
1. **RAGSystem** (`rag_system.py`): Base class with core functionality
   - Model initialization (LLM + embeddings)
   - Document loading and indexing
   - Basic query interface

2. **EnhancedRAGSystem** (`enhanced_rag_system.py`): Extended capabilities
   - Conversation memory integration
   - Multi-format file processing (PDF, DOCX, images)
   - User file management
   - OCR processing via Gemini API
   - ChromaDB vector store support

3. **GraphRAGSystem** (`graph_rag_system.py`): Graph-based RAG
   - Knowledge graph construction from documents
   - Entity and relationship extraction
   - Community detection for knowledge clustering
   - Graph-based retrieval and reasoning
   - Interactive graph visualization
   - **Memory Usage**: High (requires significant RAM for graph processing)

4. **ElasticsearchRAGSystem** (`elasticsearch_rag_system.py`): Scalable RAG
   - High-performance vector storage with Elasticsearch
   - Horizontal scalability for large document collections
   - Advanced text search with Chinese analyzer support
   - Memory-efficient batch processing
   - Production-ready with monitoring and health checks
   - **Memory Usage**: Low to moderate (offloads storage to Elasticsearch)

#### RAG System Comparison

| Feature | Enhanced RAG | Graph RAG | Elasticsearch RAG |
|---------|--------------|-----------|-------------------|
| **Memory Usage** | 🟢 Low-Moderate | 🔴 High | 🟢 Low-Moderate |
| **Processing Speed** | 🟢 Fast | 🟡 Moderate | 🟢 Fast |
| **Scalability** | 🟡 Medium | 🔴 Limited | 🟢 Excellent |
| **Complex Queries** | 🟡 Good | 🟢 Excellent | 🟡 Good |
| **Setup Complexity** | 🟢 Simple | 🟡 Moderate | 🟡 Moderate |
| **Production Ready** | 🟢 Yes | 🟡 Limited | 🟢 Yes |
| **Document Size** | < 10k docs | < 1k docs | > 100k docs |

#### When to Use Each System

- **Enhanced RAG**: 
  - 適合中小型專案 (< 10,000 文檔)
  - 需要快速原型開發
  - 記憶體資源有限
  - 傳統問答應用

- **Graph RAG**: 
  - 需要理解複雜實體關係
  - 知識推理和連接發現
  - 小到中型文檔集合 (< 1,000 文檔)
  - 有充足記憶體資源 (>16GB RAM)

- **Elasticsearch RAG**:
  - 大型文檔集合 (> 100,000 文檔)
  - 高並發查詢需求
  - 需要水平擴展
  - 生產環境部署
  - 多語言文本搜索

#### Document Processing Pipeline
1. **Multi-Source Input**: 
   - Auto-discovery from web sources (Taiwan Tea Research Station)
   - User file uploads (PDF, DOCX, TXT, MD, images)
   - Batch processing with progress tracking

2. **Advanced Processing**:
   - Text extraction with fallback mechanisms
   - OCR for image-based content (via Gemini Vision)
   - Document chunking (configurable size)
   - Metadata preservation

3. **Knowledge Extraction** (Graph RAG only):
   - Entity extraction using LLM
   - Relationship identification
   - Triplet formation (subject-predicate-object)
   - Graph construction with NetworkX

4. **Vector Indexing**:
   - Multiple embedding strategies
   - ChromaDB or SimpleVectorStore backends
   - Persistent storage with automatic loading

#### UI Component System
Modular Streamlit components for clean separation of concerns:
- `MainLayout`: Overall page layout and navigation
- `ChatInterface`: Conversation management and display
- `UploadZone`: File upload handling with drag-and-drop
- `WelcomeFlow`: Onboarding and quick start guide
- `UserExperience`: User preference and state management

#### Memory & Context Management
- `ConversationMemory`: Multi-turn conversation context
- Configurable memory length (default: 5 turns)
- Context-aware query processing
- Automatic memory persistence

### Data Flow

#### Traditional RAG Flow
```
User Input → UI → Enhanced RAG → Vector Search → Context Retrieval → LLM → Response
```

#### Graph RAG Flow
```
User Input → UI → Graph RAG → Knowledge Graph → Entity/Relation Search → 
Community Context → LLM Reasoning → Response
```

#### Detailed Processing Steps
1. **System Initialization**:
   - Model loading (LLM + embeddings)
   - Vector store initialization (Chroma/Simple)
   - Memory system setup
   - Component initialization

2. **Document Ingestion**:
   - Multi-source document collection
   - Format-specific processing
   - OCR for images (if enabled)
   - Text chunking and preprocessing

3. **Knowledge Representation**:
   - **Traditional**: Vector embeddings in high-dimensional space
   - **Graph RAG**: Entity-relationship graphs with community structure

4. **Query Processing**:
   - User input analysis
   - Context integration from conversation memory
   - **Traditional**: Semantic similarity search
   - **Graph RAG**: Graph traversal and community-based retrieval

5. **Response Generation**:
   - Context compilation from retrieved information
   - LLM reasoning with retrieved context
   - Response formatting and source attribution

### File Structure
```
├── # Main Applications
├── main_app.py                  # Primary modular application
├── enhanced_app.py              # Full-featured application
├── app.py                       # Basic application
├── quick_start.py               # Quick testing version
├── ultra_fast_start.py          # Minimal setup version
├── run.py                       # Application launcher
├── run_graphrag.py              # Graph RAG specific launcher
│
├── # RAG Systems
├── rag_system.py                # Base RAG implementation
├── enhanced_rag_system.py       # Enhanced RAG with memory
├── graph_rag_system.py          # Graph RAG implementation
│
├── # Document Processing
├── pdf_downloader.py            # Basic PDF processing
├── enhanced_pdf_downloader.py   # Advanced PDF discovery
├── user_file_manager.py         # User upload management
├── gemini_ocr.py                # OCR processing
│
├── # Storage & Memory
├── chroma_vector_store.py       # ChromaDB integration
├── conversation_memory.py       # Conversation context
│
├── # UI Components
├── components/
│   ├── layout/
│   │   └── main_layout.py       # Main layout manager
│   ├── chat/
│   │   └── chat_interface.py    # Chat UI component
│   ├── knowledge_base/
│   │   └── upload_zone.py       # File upload component
│   ├── onboarding/
│   │   └── welcome_flow.py      # Onboarding flow
│   ├── upload/
│   │   └── drag_drop_zone.py    # Drag-drop upload
│   └── user_experience.py       # User experience management
│
├── # Configuration & Utilities
├── config.py                    # Configuration settings
├── utils.py                     # Utility functions
│
├── # Testing & Benchmarking
├── test_pdf_discovery.py        # PDF discovery tests
├── benchmark_startup.py         # Performance benchmarking
│
├── # Data Storage
├── data/
│   ├── pdfs/                    # Downloaded PDF files
│   ├── index/                   # SimpleVectorStore files
│   ├── chroma_db/               # ChromaDB storage
│   ├── user_uploads/            # User uploaded files
│   └── user_preferences.json   # User preferences
│
├── # Deployment
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container definition
├── docker-run.sh/.bat           # Run scripts
├── docker-deploy.sh/.bat        # Deployment scripts
│
└── # Dependencies & Documentation
    ├── requirements.txt         # Python dependencies
    ├── CLAUDE.md                # Development guide
    ├── README.md                # Project overview
    ├── GEMINI.md                # Gemini API guide
    ├── SYSTEM_DOCUMENTATION.md  # System documentation
    └── project_structure.md     # Project structure
```

### Configuration System

#### Environment Variables (.env)
```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
GEMINI_API_KEY=your_gemini_api_key  # For OCR functionality
ENABLE_OCR=true
ENABLE_GRAPH_RAG=true
ENABLE_CONVERSATION_MEMORY=true

# File Upload Limits
MAX_FILE_SIZE_MB=10
MAX_IMAGE_SIZE_MB=5
MAX_UPLOAD_FILES=50
SUPPORTED_FILE_TYPES=pdf,txt,docx,md,png,jpg,jpeg,webp,bmp

# Graph RAG Settings
MAX_TRIPLETS_PER_CHUNK=10
GRAPH_COMMUNITY_SIZE=5

# Memory Settings
CONVERSATION_MEMORY_STEPS=5
MAX_CONTEXT_LENGTH=4000
```

#### Configuration Sources
- **WEB_SOURCES**: URLs for automatic PDF discovery from Taiwan Tea Research Station
- **PDF_SOURCES**: Legacy predefined URLs (backup option)
- **Models**: Configurable LLM and embedding models
- **Storage**: Multiple backend options (ChromaDB, SimpleVectorStore)
- **Features**: Toggle-able capabilities (Graph RAG, OCR, Memory)

### System Modes

#### 1. Traditional RAG Mode
- Vector-based semantic search
- SimpleVectorStore or ChromaDB
- Fast and reliable
- Good for straightforward Q&A

#### 2. Enhanced RAG Mode
- Includes conversation memory
- Multi-format file support
- OCR capabilities
- User file management
- Improved context awareness

#### 3. Graph RAG Mode (Advanced)
- Knowledge graph construction
- Entity and relationship extraction
- Community-based retrieval
- Graph visualization
- Complex reasoning capabilities
- Best for understanding relationships and complex queries

## Development Notes

### Vector Storage Options

#### ChromaDB (Recommended)
- High-performance vector database
- Persistent storage with SQLite backend
- Supports filtering and metadata queries
- Better scalability for large document collections
- Automatic cleanup and optimization

#### SimpleVectorStore (Development)
- LlamaIndex built-in vector store
- Stores vectors as JSON files
- No external dependencies
- Good for development and small datasets
- Easy backup and version control

### Performance Optimizations

#### System Initialization
- Lazy loading of components
- Model caching to avoid reinitialization
- Session state persistence
- Background processing for file uploads

#### Memory Management
- Conversation context trimming
- Automatic cleanup of temporary files
- Efficient document chunking
- Resource monitoring and cleanup

#### Graph RAG Optimizations
- Community-based retrieval reduces search space
- Parallel processing for entity extraction
- Graph caching for repeated queries
- Incremental graph updates

### Error Handling & Resilience

#### Multi-level Fallbacks
- PDF processing: PyMuPDF → PyPDF2 → pdfplumber
- Vector storage: ChromaDB → SimpleVectorStore
- OCR processing: Gemini Vision → skip OCR
- Model initialization with retry mechanisms

#### User Experience
- Graceful degradation when features are unavailable
- Clear error messages and recovery suggestions
- Progress indicators for long-running operations
- Automatic retry for transient failures

#### API Error Handling
- Rate limiting awareness
- API key validation
- Timeout handling
- Fallback responses for service unavailability

### Development Best Practices

#### Code Organization
- Modular component architecture
- Clear separation of concerns
- Dependency injection for testability
- Configuration-driven behavior

#### Testing Strategy
- Unit tests for core functionality
- Integration tests for end-to-end workflows
- Performance benchmarking
- Error condition testing

#### Deployment Considerations
- Docker containerization for consistency
- Environment-specific configurations
- Resource requirement documentation
- Monitoring and logging setup

### Extending the System

#### Adding New RAG Methods
1. Inherit from `RAGSystem` base class
2. Implement required abstract methods
3. Add configuration options in `config.py`
4. Update UI components as needed

#### Custom Document Processors
1. Implement document loading interface
2. Add to `UserFileManager` supported types
3. Update file validation logic
4. Test with various document formats

#### New Vector Store Backends
1. Create manager class (similar to `ChromaVectorStoreManager`)
2. Implement LlamaIndex vector store interface
3. Add configuration options
4. Update system initialization logic

---
## 專案現況分析與改善建議 (2025-08-17)

### 專案現況分析

這是一個基於 LlamaIndex 和 Streamlit 的多模態、多後端 RAG 智能問答系統。

*   **核心目標**：提供一個能夠處理多種文件格式（PDF, DOCX, 圖片等），並透過先進的 RAG 技術（包括傳統向量檢索、知識圖譜 Graph RAG、Elasticsearch）來回答使用者問題的智能助理。
*   **技術堆疊**：
    *   **前端**：Streamlit，並有模組化的 UI 元件。
    *   **AI 框架**：LlamaIndex。
    *   **LLM**：Groq 上的 Llama 3.3。
    *   **嵌入模型**：HuggingFace `all-MiniLM-L6-v2`。
    *   **向量儲存**：支援多種後端，包括 LlamaIndex 內建的 `SimpleVectorStore`（檔案型）、`ChromaDB` �� `Elasticsearch`。
    *   **OCR**：使用 Google Gemini API 進行圖片文字識別。
    *   **部署**：提供完整的 Docker 和 Docker Compose 設定，支援多種部署模式（標準、輕量、Elasticsearch）。
*   **主要功能**：
    *   **多 RAG 引擎**：`enhanced_rag_system`（基礎功能+對話記憶+OCR）、`graph_rag_system`（知識圖譜）、`elasticsearch_rag_system`（可擴展的生產級檢索）。
    *   **自動化資料處理**：能自動從指定網站爬取並下載 PDF 文件。
    *   **多模態輸入**：支援使用者上傳文件（PDF, DOCX, TXT, MD）和圖片。
    *   **對話記憶**：能夠記住上下文，進行多輪對話。
    *   **知識圖譜**：能夠從文件中提取實體和關係，建立知識圖譜並進行視覺化展示。
*   **專案結構**：
    *   結構清晰，按功能模組化（`components`, `config`, `utils` 等）。
    *   存在多個應用程式入口點（`app.py`, `main_app.py`, `enhanced_app.py`, `quick_start.py` 等），可能是為了不同的啟動模式或開發階段。

總體來說，這是一個非常完整且強大的 POC 專案，不僅實現了核心功���，還考慮了部署、擴展性和多種使用場景。

---

### 潛在問題與建議

#### 1. 程式碼重複與檔案結構混亂

*   **問題描述**：
    *   存在多個功能類似的應用程式入口檔案，例如 `app.py`, `enhanced_app.py`, `main_app.py`。這會讓新接手的開發者感到困惑，不確定應該從哪個檔案啟動，也增加了維護成本。
    *   `rag_system.py` 和 `enhanced_rag_system.py` 存在繼承關係，但 `app.py` 卻直接使用了 `EnhancedRAGSystem`，使得 `rag_system.py` 的定位變得模糊，似乎有些功能被重複實現。
*   **潛在風險**：維護困難、程式碼不一致、新人上手門檻高。
*   **修改建議**：
    *   **合併應用入口**：將 `app.py`, `enhanced_app.py`, `main_app.py` 的功能合併到一個主要的 `app.py` 或 `main.py` 中。使用 `config.py` 或環境變數來控制要啟用哪些功能（例如，是否啟用 Graph RAG、是否使用對話記憶等）。這樣可以簡化專案結構，使入口唯一。
    *   **清晰化 RAG 系統繼承鏈**：明確 `RAGSystem` 為基底類別，`EnhancedRAGSystem` 為擴展類別。確保基礎功能都在基底類別中實現，擴展類別只添加新功能，避免功能覆蓋或混亂。

#### 2. Elasticsearch 整合問題

*   **問題描述**：
    *   在 `elasticsearch_rag_system.py` 中，`create_index` 方法的邏輯非常複雜，包含了 `try-except` 嵌套和兩種不同的索引建立方法（`from_documents` 和逐個 `insert`）。這通常意味著主要的 `from_documents` 方法可能存在不穩定或失敗的情況。
    *   程式碼中使用了 `custom_elasticsearch_store.py`，但這個檔案並未提供，我無法檢視其內容。如果這個自定義存儲有問題，會直接影響 Elasticsearch 的功能。
    *   在 `search_documents` 方法中，文本搜索的分析器被硬編碼為 `"chinese_analyzer"`，但這個分析器在 `_create_elasticsearch_index` 方法中並未被定義（定義的是 `text_analyzer`）。這會導致搜索時出錯。
*   **潛在風險**：Elasticsearch 索引建立失敗、搜索功能異常、系統不穩定。
*   **修改建議**：
    *   **簡化索引建立邏輯**：深入排查 `VectorStoreIndex.from_documents` 失敗的原因，並嘗試修復它，而不是依賴備用方案。可能是 LlamaIndex 版本與 Elasticsearch Store 的兼容性問題。
    *   **統一分析器名稱**：將 `search_documents` 中使用的分析器名稱從 `"chinese_analyzer"` 改為 `_create_elasticsearch_index` 中定義的 `"text_analyzer"`，或是在索引建立時就定義好 `chinese_analyzer`。
    *   **提供自定義模組**：確保 `custom_elasticsearch_store.py` 檔案存在且功能正確。

#### 3. 相依性管理 (requirements.txt)

*   **問題描述**：
    *   `requirements.txt` 中包含了一些被註解掉的套件，如 `streamlit-agraph` 和 `streamlit-elements`，並註明「可能不存在」。這表示這些 UI 功能可能無法正常運作。
    *   同樣，一些效能或社群檢測相關的套件也被註解，如 `graspologic` 和 `gc3pie`。
*   **潛在風險**：功能不完整、部署時可能因缺少套件而失敗。
*   **修改建議**：
    *   **確認並清理相依性**：找到被註解套件的替代方案，或者如果功能不再需要，就從程式碼中移除相關的 import 和呼叫，並清理 `requirements.txt`。
    *   **版本鎖定**：建議使用 `pip freeze > requirements.txt` 來產生一��包含所有子相依性且版本被鎖定的檔案，或使用 `poetry`, `pipenv` 等工具來更好地管理相依性，以確保環境的一致性。

#### 4. 設定管理 (config.py)

*   **問題描述**：
    *   `config.py` 中有一個 `RAG_SYSTEM_TYPE` 的環境變數，用於在 `enhanced`, `graph`, `elasticsearch` 之間切換。但在任何一個應用程式入口（如 `app.py`）中，都沒有看到讀取這個變數來動態載入對應 RAG 系統的邏輯。目前似乎是寫死的。
*   **潛在風險**：設定與實際行為不符，使用者無法透過環境變數切換 RAG 模式。
*   **修改建議**：
    *   在應用程式啟動時，增加一個工廠函式 (factory function) 或判斷邏輯，根據 `RAG_SYSTEM_TYPE` 的值來實例化對應的 RAG 系統類別。
