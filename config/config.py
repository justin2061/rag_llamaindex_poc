import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# API 設定
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # 可選，用於 OCR 功能
JINA_API_KEY = os.getenv("JINA_API_KEY")      # 可選，用於優化 embedding 效果

# UI/UX 設定
SHOW_TECHNICAL_MESSAGES = os.getenv("SHOW_TECHNICAL_MESSAGES", "false").lower() == "true"  # 是否顯示技術訊息
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"  # 除錯模式

# 模型設定
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq 模型

# PDF 來源網址
PDF_SOURCES = {
    "茶業研究彙報": [
        "https://www.tbrs.gov.tw/files/tbrs/web_structure/4399/A01_1.pdf",  # 第1期
        "https://www.tbrs.gov.tw/files/tbrs/web_structure/4410/A01_1.pdf",  # 第2期
        "https://www.tbrs.gov.tw/files/tbrs/web_structure/4427/A01_1.pdf",  # 第3期
    ],
    "茶業專訊與其他文件": [
        # 這裡可以加入更多從網頁上找到的PDF連結
    ]
}

# 網頁來源 - 用於自動發現PDF連結
WEB_SOURCES = [
    "https://www.tbrs.gov.tw/ws.php?id=4189",  # 台灣茶業研究彙報摘要
    "https://www.tbrs.gov.tw/ws.php?id=1569",  # 其他茶業相關頁面
]

# 模型設定
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "jina").lower() # 'jina' or 'local'
EMBEDDING_MODEL = "jina-embeddings-v3"
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq 模型

# 檔案路徑設定
DATA_DIR = "data"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
INDEX_DIR = os.path.join(DATA_DIR, "index")

# 建立目錄
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

# Google Gemini設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ENABLE_OCR = os.getenv("ENABLE_OCR", "true").lower() == "true"

# 檔案上傳設定
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 5))
SUPPORTED_FILE_TYPES = os.getenv("SUPPORTED_FILE_TYPES", "pdf,txt,docx,md,png,jpg,jpeg,webp,bmp").split(',')
MAX_UPLOAD_FILES = int(os.getenv("MAX_UPLOAD_FILES", 50))

# Graph RAG 設定
ENABLE_GRAPH_RAG = os.getenv("ENABLE_GRAPH_RAG", "true").lower() == "true"
MAX_TRIPLETS_PER_CHUNK = int(os.getenv("MAX_TRIPLETS_PER_CHUNK", 10))
GRAPH_COMMUNITY_SIZE = int(os.getenv("GRAPH_COMMUNITY_SIZE", 5))

# 對話記憶設定
CONVERSATION_MEMORY_STEPS = int(os.getenv("CONVERSATION_MEMORY_STEPS", 5))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", 4000))
ENABLE_CONVERSATION_MEMORY = os.getenv("ENABLE_CONVERSATION_MEMORY", "true").lower() == "true"

# 檔案路徑設定
USER_UPLOADS_DIR = os.path.join(DATA_DIR, "user_uploads")

# 建立目錄
os.makedirs(USER_UPLOADS_DIR, exist_ok=True)

# Streamlit 設定
PAGE_TITLE = "RAG智能問答系統"
PAGE_ICON = "🤖"

# Elasticsearch 設定
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
ELASTICSEARCH_SCHEME = os.getenv("ELASTICSEARCH_SCHEME", "http")  # http or https
ELASTICSEARCH_INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_NAME", "rag_intelligent_assistant")
ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_TIMEOUT = int(os.getenv("ELASTICSEARCH_TIMEOUT", 30))
ELASTICSEARCH_MAX_RETRIES = int(os.getenv("ELASTICSEARCH_MAX_RETRIES", 3))
ELASTICSEARCH_VERIFY_CERTS = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "false").lower() == "true"

# Elasticsearch 索引設定
ELASTICSEARCH_SHARDS = int(os.getenv("ELASTICSEARCH_SHARDS", 1))
ELASTICSEARCH_REPLICAS = int(os.getenv("ELASTICSEARCH_REPLICAS", 0))
ELASTICSEARCH_VECTOR_DIMENSION = int(os.getenv("ELASTICSEARCH_VECTOR_DIMENSION", 512))  # Enhanced dimension for better semantic representation
ELASTICSEARCH_SIMILARITY = os.getenv("ELASTICSEARCH_SIMILARITY", "cosine")

# 向量存儲優先順序設定
ENABLE_ELASTICSEARCH = os.getenv("ENABLE_ELASTICSEARCH", "true").lower() == "true"  # 預設啟用
VECTOR_STORE_PRIORITY = os.getenv("VECTOR_STORE_PRIORITY", "elasticsearch,simple").split(",")  # 優先順序

# Phase 1 優化設定 - 智能切割與結構識別
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))  # 基礎切割大小
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))  # 重疊字符數
ENABLE_HIERARCHICAL_CHUNKING = os.getenv("ENABLE_HIERARCHICAL_CHUNKING", "false").lower() == "true"
ENABLE_DOCUMENT_STRUCTURE_DETECTION = os.getenv("ENABLE_DOCUMENT_STRUCTURE_DETECTION", "false").lower() == "true"

# Phase 2 優化設定 - 混合檢索
ENABLE_HYBRID_SEARCH = os.getenv("ENABLE_HYBRID_SEARCH", "false").lower() == "true"
ENABLE_QUERY_REWRITING = os.getenv("ENABLE_QUERY_REWRITING", "false").lower() == "true"
HYBRID_SEARCH_WEIGHTS = {
    "vector": float(os.getenv("VECTOR_SEARCH_WEIGHT", 0.6)),
    "keyword": float(os.getenv("KEYWORD_SEARCH_WEIGHT", 0.3)),
    "semantic": float(os.getenv("SEMANTIC_SEARCH_WEIGHT", 0.1))
}

# Phase 3 優化設定 - 多模型策略
ENABLE_MULTI_EMBEDDING = os.getenv("ENABLE_MULTI_EMBEDDING", "false").lower() == "true"
ENABLE_CONTEXTUAL_RERANKING = os.getenv("ENABLE_CONTEXTUAL_RERANKING", "false").lower() == "true"
RERANKING_MODEL = os.getenv("RERANKING_MODEL", "bge-reranker-base")

# 多粒度切割配置
CHUNK_STRATEGIES = {
    "short": {"size": 512, "overlap": 100},   # 短文本精確搜索
    "medium": {"size": 1024, "overlap": 200}, # 中等文本上下文  
    "long": {"size": 2048, "overlap": 400}    # 長文本整體理解
}

# RAG 系統選擇
RAG_SYSTEM_TYPE = os.getenv("RAG_SYSTEM_TYPE", "enhanced").lower()  # enhanced, graph, elasticsearch

# 應用程式模式
APP_MODE = os.getenv("APP_MODE", "full").lower() # full, quick, ultra_fast
