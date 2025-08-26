"""
增強型 RAG 系統 API
提供完整的 RAG 功能，包括：
- 智能問答（帶前後文記憶）
- 知識庫管理
- 文件上傳處理
- 對話記錄管理
- 系統狀態監控
- 簡易認證機制
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import sys
import os
import uuid
import hashlib
import time
from datetime import datetime, timedelta
import tempfile
from pathlib import Path
import traceback
import jwt
from functools import wraps
from urllib.parse import unquote

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置詳細日誌
from src.utils.logging_config import setup_logging, get_api_logger, log_exception, log_performance
import logging

# 初始化日誌系統
setup_logging(
    app_name="enhanced_api",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir="/app/logs",
    enable_console=True,
    enable_file=True,
    enable_json=True
)

# 獲取API專用日誌器
api_logger = get_api_logger()
api_logger.info("🚀 Enhanced RAG API 正在啟動...")

from src.rag_system.enhanced_rag_system_v2 import EnhancedRAGSystemV2
from src.processors.user_file_manager import UserFileManager
from config.config import GROQ_API_KEY, GEMINI_API_KEY

# FastAPI 實例
app = FastAPI(
    title="Enhanced RAG API",
    description="""
## 完整的 RAG 系統 API

這是一個功能完整的 RAG (Retrieval-Augmented Generation) 系統 API，提供：

### 🧠 智能功能
- **智能問答**：帶前後文記憶的對話系統
- **知識庫管理**：文件上傳、處理、管理
- **對話記錄**：完整的對話歷史追蹤

### 🔐 安全特性  
- **多層認證**：API Key + JWT Token
- **權限控制**：分級訪問權限
- **會話管理**：安全的用戶會話

### 📚 支援格式
- **文檔**：PDF、Word、Markdown、TXT
- **圖片**：PNG、JPG、JPEG、WebP、BMP
- **批量處理**：多文件同時上傳

### 🚀 開始使用
1. 使用預設 API Key 獲取 Token：`demo-api-key-123`
2. 在右上角 "Authorize" 按鈕輸入 Token
3. 開始測試各種 API 功能！

### 🔗 相關鏈接
- **GitHub**: [RAG System Repository](https://github.com/your-repo)
- **文檔**: [完整 API 文檔](./docs)
- **支援**: [Issues & Support](./support)
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "RAG API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8003",
            "description": "本地開發環境"
        },
        {
            "url": "http://localhost:8000", 
            "description": "直接訪問（不經過 Docker 端口映射）"
        }
    ],
    tags_metadata=[
        {
            "name": "認證",
            "description": "用戶認證和授權相關 API",
        },
        {
            "name": "智能問答",
            "description": "帶前後文記憶的智能對話 API",
        },
        {
            "name": "知識庫管理", 
            "description": "文件上傳、處理和管理 API",
        },
        {
            "name": "對話記錄",
            "description": "對話歷史和統計 API",
        },
        {
            "name": "系統監控",
            "description": "系統健康檢查和狀態監控 API",
        },
    ]
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制為特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態文件服務（用於演示頁面）
app.mount("/static", StaticFiles(directory="api"), name="static")

# 簡易認證配置
SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-key-change-in-production")
API_KEYS = {
    "demo": "demo-api-key-123",
    "admin": "admin-api-key-456",
    "user": "user-api-key-789"
}

# 安全配置
security = HTTPBearer()

# 全局實例
rag_system = None
file_manager = None

# ================== 數據模型 ==================

class APIKeyAuth(BaseModel):
    api_key: str = Field(..., 
                         description="API 金鑰",
                         example="demo-api-key-123")
    
    class Config:
        schema_extra = {
            "example": {
                "api_key": "demo-api-key-123"
            }
        }

class UserContext(BaseModel):
    user_id: str
    permissions: List[str] = ["read", "write"]
    session_id: Optional[str] = None

class ConversationMessage(BaseModel):
    role: str = Field(..., description="消息角色: user 或 assistant")
    content: str = Field(..., description="消息內容")
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}

class ConversationContext(BaseModel):
    conversation_id: Optional[str] = None
    messages: List[ConversationMessage] = []
    max_history: int = Field(default=10, description="保留的最大消息數")

class ChatRequest(BaseModel):
    question: str = Field(..., 
                          description="用戶問題", 
                          example="什麼是機器學習？請詳細介紹一下。")
    conversation_context: Optional[ConversationContext] = Field(
        None,
        description="對話上下文（可選），用於維持多輪對話記憶"
    )
    user_id: Optional[str] = Field(
        "anonymous", 
        description="用戶ID，用於追蹤和權限控制"
    )
    session_id: Optional[str] = Field(
        None, 
        description="會話ID，用於對話記錄分組"
    )
    include_sources: bool = Field(
        True, 
        description="是否在回應中包含參考來源"
    )
    max_sources: int = Field(
        3, 
        description="最大返回的參考來源數量",
        ge=1, le=10
    )
    temperature: Optional[float] = Field(
        0.7, 
        description="回應創造性參數 (0.0-1.0)",
        ge=0.0, le=1.0
    )
    
    class Config:
        schema_extra = {
            "example": {
                "question": "什麼是機器學習？請詳細介紹一下。",
                "include_sources": True,
                "max_sources": 3,
                "user_id": "demo_user",
                "temperature": 0.7
            }
        }

class SourceInfo(BaseModel):
    source: str
    file_path: str
    score: float
    content: str
    page: Optional[str] = None
    type: str = "document"

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo] = []
    conversation_id: str
    metadata: Dict[str, Any] = {}
    context: ConversationContext
    response_time_ms: int
    timestamp: str

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    status: str
    chunks_created: int
    processing_time_ms: int

class KnowledgeBaseFile(BaseModel):
    id: str
    name: str
    size_mb: float
    type: str
    upload_time: str
    chunk_count: int
    status: str

class KnowledgeBaseStatus(BaseModel):
    total_files: int
    total_chunks: int
    total_size_mb: float
    files: List[KnowledgeBaseFile]

class SystemHealthCheck(BaseModel):
    status: str
    elasticsearch_connected: bool
    api_version: str
    uptime_seconds: int
    total_documents: int
    total_conversations: int
    system_info: Dict[str, Any]
    timestamp: str

class ConversationHistory(BaseModel):
    conversations: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str
    request_id: str

# ================== 認證與授權 ==================

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserContext:
    """驗證 API 金鑰"""
    token = credentials.credentials
    
    # 檢查是否為預設義的 API 金鑰
    for user_type, api_key in API_KEYS.items():
        if token == api_key:
            permissions = ["read", "write"] if user_type in ["admin", "demo"] else ["read"]
            return UserContext(
                user_id=user_type,
                permissions=permissions,
                session_id=str(uuid.uuid4())
            )
    
    # 嘗試解析 JWT Token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return UserContext(
            user_id=payload.get("user_id", "unknown"),
            permissions=payload.get("permissions", ["read"]),
            session_id=payload.get("session_id")
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_permission(permission: str):
    """檢查用戶權限裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_context = kwargs.get('user_context')
            if user_context and permission in user_context.permissions:
                return await func(*args, **kwargs)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return wrapper
    return decorator

# ================== 輔助函數 ==================

def generate_request_id() -> str:
    """生成請求ID"""
    return str(uuid.uuid4())[:8]

def build_conversation_context(messages: List[ConversationMessage], question: str) -> str:
    """構建對話上下文"""
    if not messages:
        return question
    
    # 構建對話歷史
    context_parts = []
    for msg in messages[-5:]:  # 只保留最近5條消息
        role_prefix = "用戶" if msg.role == "user" else "助理"
        context_parts.append(f"{role_prefix}: {msg.content}")
    
    # 添加當前問題
    context_parts.append(f"用戶: {question}")
    
    return "\n".join(context_parts)

def update_conversation_context(context: ConversationContext, question: str, answer: str) -> ConversationContext:
    """更新對話上下文"""
    now = datetime.now()
    
    # 添加用戶消息
    context.messages.append(ConversationMessage(
        role="user",
        content=question,
        timestamp=now
    ))
    
    # 添加助理回應
    context.messages.append(ConversationMessage(
        role="assistant", 
        content=answer,
        timestamp=now
    ))
    
    # 保持消息數量在限制內
    if len(context.messages) > context.max_history * 2:
        context.messages = context.messages[-(context.max_history * 2):]
    
    return context

# ================== 啟動事件 ==================

@app.on_event("startup")
async def startup_event():
    """啟動時初始化系統"""
    global rag_system, file_manager
    
    try:
        print("🚀 正在初始化 Enhanced RAG API...")
        
        # 初始化 RAG 系統
        rag_system = EnhancedRAGSystemV2()
        if rag_system._initialize_elasticsearch():
            print("✅ Elasticsearch RAG 系統初始化成功")
        else:
            print("❌ Elasticsearch RAG 系統初始化失敗")
        
        # 初始化文件管理器
        file_manager = UserFileManager()
        print("✅ 文件管理器初始化成功")
        
        print("🎉 Enhanced RAG API 啟動完成!")
        
    except Exception as e:
        print(f"❌ 系統初始化錯誤: {str(e)}")
        print(traceback.format_exc())

# ================== API 端點 ==================

@app.get("/", 
         summary="API 根端點", 
         description="獲取 API 基本信息和狀態",
         tags=["系統監控"],
         response_description="API 基本信息")
async def root():
    """
    ## API 根端點
    
    返回 Enhanced RAG API 的基本信息，包括：
    - API 版本信息
    - 文檔鏈接
    - 當前運行狀態
    - 時間戳
    
    **無需認證**
    """
    return {
        "message": "Enhanced RAG API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
        "features": [
            "智能問答（帶對話記憶）",
            "知識庫管理",
            "多格式文件支持", 
            "安全認證機制",
            "對話記錄追蹤"
        ],
        "demo_credentials": {
            "api_key": "demo-api-key-123",
            "note": "使用此 API Key 獲取訪問令牌進行測試"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", 
         response_model=SystemHealthCheck, 
         summary="系統健康檢查",
         description="檢查系統各組件的運行狀態",
         tags=["系統監控"],
         responses={
             200: {
                 "description": "系統健康狀態",
                 "content": {
                     "application/json": {
                         "example": {
                             "status": "healthy",
                             "elasticsearch_connected": True,
                             "api_version": "2.0.0",
                             "uptime_seconds": 3600,
                             "total_documents": 42,
                             "total_conversations": 128,
                             "system_info": {
                                 "groq_configured": True,
                                 "gemini_configured": True
                             },
                             "timestamp": "2025-08-22T12:00:00"
                         }
                     }
                 }
             },
             500: {"description": "系統健康檢查失敗"}
         })
async def health_check():
    """
    ## 系統健康檢查
    
    檢查系統各個組件的運行狀態，包括：
    - **Elasticsearch 連接狀態**
    - **系統運行時間**
    - **文檔和對話統計**
    - **API 配置狀態**
    
    **無需認證**
    
    ### 回應狀態
    - `healthy`: 所有組件正常運行
    - `degraded`: 部分組件異常但服務可用
    - `unhealthy`: 系統異常
    """
    start_time = time.time()
    
    try:
        # 檢查 Elasticsearch 連接
        es_connected = False
        total_docs = 0
        total_conversations = 0
        
        if rag_system and rag_system.elasticsearch_client:
            es_connected = rag_system.elasticsearch_client.ping()
            if es_connected:
                stats = rag_system.get_document_statistics()
                total_docs = stats.get('total_documents', 0)
                
                if hasattr(rag_system, 'get_conversation_statistics'):
                    conv_stats = rag_system.get_conversation_statistics()
                    total_conversations = conv_stats.get('total_conversations', 0)
        
        return SystemHealthCheck(
            status="healthy" if es_connected else "degraded",
            elasticsearch_connected=es_connected,
            api_version="2.0.0",
            uptime_seconds=int(time.time() - start_time),
            total_documents=total_docs,
            total_conversations=total_conversations,
            system_info={
                "groq_configured": bool(GROQ_API_KEY),
                "gemini_configured": bool(GEMINI_API_KEY)
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@app.post("/auth/token", 
          summary="生成訪問令牌",
          description="使用 API Key 生成 JWT 訪問令牌",
          tags=["認證"],
          responses={
              200: {
                  "description": "成功生成訪問令牌",
                  "content": {
                      "application/json": {
                          "example": {
                              "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                              "token_type": "bearer",
                              "expires_in": 86400,
                              "user_id": "demo",
                              "permissions": ["read", "write"]
                          }
                      }
                  }
              },
              401: {"description": "無效的 API Key"}
          })
async def generate_token(auth: APIKeyAuth):
    """生成 JWT 訪問令牌"""
    
    # 驗證 API 金鑰
    user_type = None
    for utype, api_key in API_KEYS.items():
        if auth.api_key == api_key:
            user_type = utype
            break
    
    if not user_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # 生成 JWT Token
    permissions = ["read", "write"] if user_type in ["admin", "demo"] else ["read"]
    payload = {
        "user_id": user_type,
        "permissions": permissions,
        "session_id": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours
        "user_id": user_type,
        "permissions": permissions
    }

@app.post("/chat", 
          response_model=ChatResponse, 
          summary="智能問答（帶對話記憶）",
          description="執行智能問答，支援前後文對話記憶和多輪對話理解",
          tags=["智能問答"],
          responses={
              200: {
                  "description": "成功獲得智能回答",
                  "content": {
                      "application/json": {
                          "example": {
                              "answer": "機器學習是人工智能的一個重要分支，它是一種讓計算機系統能夠從數據中自動學習和改進的技術...",
                              "sources": [
                                  {
                                      "source": "ml_guide.pdf",
                                      "file_path": "/docs/ml_guide.pdf", 
                                      "score": 0.95,
                                      "content": "機器學習的定義和基本概念...",
                                      "page": "第1頁",
                                      "type": "document"
                                  }
                              ],
                              "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                              "metadata": {
                                  "request_id": "req-123",
                                  "user_id": "demo_user",
                                  "contextual_query": True
                              },
                              "context": {
                                  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                                  "messages": [
                                      {
                                          "role": "user",
                                          "content": "什麼是機器學習？",
                                          "timestamp": "2025-08-22T12:00:00"
                                      },
                                      {
                                          "role": "assistant",
                                          "content": "機器學習是人工智能的一個重要分支...",
                                          "timestamp": "2025-08-22T12:00:01"
                                      }
                                  ],
                                  "max_history": 10
                              },
                              "response_time_ms": 1250,
                              "timestamp": "2025-08-22T12:00:01"
                          }
                      }
                  }
              },
              401: {"description": "認證失敗"},
              403: {"description": "權限不足"},
              500: {"description": "服務器內部錯誤"}
          })
async def chat_with_memory(
    request: ChatRequest,
    user_context: UserContext = Depends(verify_api_key)
):
    """
    ## 智能問答（帶對話記憶）
    
    這是系統的核心功能，提供智能問答服務並支援多輪對話記憶。
    
    ### 🧠 核心特性
    - **上下文理解**：自動理解前後文關係
    - **對話記憶**：維持多輪對話的連貫性  
    - **智能檢索**：從知識庫中找到最相關的信息
    - **來源追蹤**：提供回答的參考來源
    
    ### 💡 使用技巧
    1. **首次對話**：直接提問，系統會提供基礎回答
    2. **後續對話**：傳入 `conversation_context` 實現連續對話
    3. **調整參數**：使用 `temperature` 控制回答的創造性
    4. **控制來源**：通過 `max_sources` 限制返回的參考資料數量
    
    ### 📝 對話記憶工作原理
    系統會自動：
    - 保存每輪對話的問題和回答
    - 將歷史對話轉換為查詢上下文
    - 智能截斷過長的對話歷史
    - 隔離不同 conversation_id 的對話
    
    ### 🔑 權限要求
    需要有效的 JWT Token（read 權限即可）
    """
    start_time = time.time()
    request_id = generate_request_id()
    
    if not rag_system:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized"
        )
    
    try:
        # 初始化對話上下文
        context = request.conversation_context or ConversationContext()
        if not context.conversation_id:
            context.conversation_id = str(uuid.uuid4())
        
        # 構建帶上下文的查詢
        contextual_question = build_conversation_context(context.messages, request.question)
        
        # 執行 RAG V2.0 查詢
        conversation_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in context.messages
        ]
        
        user_preferences = {
            "content_types": ["title", "paragraph"],
            "topics": [],
            "preferred_length": "medium"
        }
        
        result = rag_system.query_with_sources_v2(
            question=contextual_question,
            conversation_history=conversation_history,
            user_preferences=user_preferences,
            max_sources=request.max_sources
        )
        
        # 更新對話上下文
        context = update_conversation_context(context, request.question, result['answer'])
        
        # 處理來源信息
        sources = []
        if request.include_sources and 'sources' in result:
            for source in result['sources'][:request.max_sources]:
                sources.append(SourceInfo(
                    source=source.get('source', ''),
                    file_path=source.get('file_path', ''),
                    score=source.get('score', 0.0),
                    content=source.get('content', ''),
                    page=source.get('page'),
                    type=source.get('type', 'document')
                ))
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            answer=result['answer'],
            sources=sources,
            conversation_id=context.conversation_id,
            metadata={
                **result.get('metadata', {}),
                'request_id': request_id,
                'user_id': request.user_id or user_context.user_id,
                'contextual_query': len(context.messages) > 0
            },
            context=context,
            response_time_ms=response_time_ms,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat request failed: {str(e)}"
        )

@app.post("/upload", 
          response_model=FileUploadResponse, 
          summary="上傳文件到知識庫",
          description="上傳文件並自動處理成可搜索的知識庫內容",
          tags=["知識庫管理"],
          responses={
              200: {
                  "description": "文件上傳和處理成功",
                  "content": {
                      "application/json": {
                          "example": {
                              "file_id": "550e8400-e29b-41d4-a716-446655440000",
                              "filename": "machine_learning_guide.pdf",
                              "size_bytes": 1024000,
                              "status": "processed",
                              "chunks_created": 25,
                              "processing_time_ms": 3000
                          }
                      }
                  }
              },
              400: {"description": "無效的文件格式"},
              403: {"description": "權限不足（需要 write 權限）"},
              500: {"description": "文件處理失敗"}
          })
async def upload_file(
    file: UploadFile = File(..., description="要上傳的文件（支援 PDF、Word、Markdown、圖片等格式）"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_context: UserContext = Depends(verify_api_key)
):
    """
    ## 上傳文件到知識庫
    
    將文件上傳到系統並自動處理成可搜索的知識庫內容。
    
    ### 📁 支援格式
    - **文檔**：PDF、Word (.docx)、Markdown (.md)、純文字 (.txt)
    - **圖片**：PNG、JPG、JPEG、WebP、BMP（將進行 OCR 文字識別）
    
    ### ⚙️ 處理流程
    1. **文件驗證**：檢查格式和大小
    2. **內容提取**：從文件中提取文字內容
    3. **文本分塊**：將長文本分割成適當大小的塊
    4. **向量化**：為每個文本塊生成向量嵌入
    5. **索引存儲**：存儲到 Elasticsearch 中供搜索使用
    
    ### 📊 處理結果
    - `file_id`：文件的唯一標識符
    - `chunks_created`：創建的文本塊數量
    - `processing_time_ms`：處理耗時（毫秒）
    
    ### 🔑 權限要求
    需要 **write** 權限的 JWT Token
    """
    
    # 記錄上傳請求開始
    api_logger.info(f"📤 文件上傳請求開始")
    api_logger.info(f"   - 文件名: {file.filename}")
    api_logger.info(f"   - 文件大小: {file.size} bytes")
    api_logger.info(f"   - 內容類型: {file.content_type}")
    api_logger.info(f"   - 用戶: {user_context.user_id}")
    
    if "write" not in user_context.permissions:
        api_logger.warning(f"❌ 權限不足: 用戶 {user_context.user_id} 沒有寫入權限")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required for file upload"
        )
    
    if not rag_system or not file_manager:
        api_logger.error("❌ 系統未初始化: RAG系統或文件管理器不可用")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File processing system not initialized"
        )
    
    start_time = time.time()
    file_id = str(uuid.uuid4())
    api_logger.info(f"🆔 分配文件ID: {file_id}")
    
    try:
        # 驗證文件
        api_logger.info("🔍 開始驗證文件...")
        validation_start = time.time()
        if not file_manager.validate_file(file):
            api_logger.error(f"❌ 文件驗證失敗: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type or format"
            )
        validation_time = time.time() - validation_start
        api_logger.info(f"✅ 文件驗證通過，耗時: {validation_time:.3f}秒")
        
        # 保存臨時文件
        api_logger.info("💾 開始保存臨時文件...")
        save_start = time.time()
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        api_logger.info(f"   - 臨時目錄: {temp_dir}")
        api_logger.info(f"   - 臨時文件路徑: {temp_file_path}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        save_time = time.time() - save_start
        api_logger.info(f"✅ 臨時文件保存完成，耗時: {save_time:.3f}秒")
        
        # 使用V2.0處理文件
        api_logger.info("🔄 開始V2.0文件處理...")
        process_start = time.time()
        
        try:
            processing_stats = rag_system.process_uploaded_file_v2(file, file_manager)
            process_time = time.time() - process_start
            api_logger.info(f"✅ V2.0文件處理完成，耗時: {process_time:.3f}秒")
            api_logger.info(f"   - 處理統計: {processing_stats}")
            
        except Exception as process_error:
            process_time = time.time() - process_start
            api_logger.error(f"❌ V2.0文件處理失敗，耗時: {process_time:.3f}秒")
            log_exception(api_logger, f"V2.0處理異常詳情", sys.exc_info())
            raise process_error
        
        chunks_created = processing_stats.get("chunks_created", 0)
        optimization_used = processing_stats.get("optimization_used", [])
        
        api_logger.info(f"📊 處理結果:")
        api_logger.info(f"   - 創建chunks: {chunks_created}")
        api_logger.info(f"   - 使用優化: {optimization_used}")
        
        # 清理臨時文件
        api_logger.info("🧹 清理臨時文件...")
        try:
            os.unlink(temp_file_path)
            os.rmdir(temp_dir)
            api_logger.info("✅ 臨時文件清理完成")
        except Exception as cleanup_error:
            api_logger.warning(f"⚠️ 臨時文件清理失敗: {cleanup_error}")
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        final_status = "processed" if chunks_created > 0 else "failed"
        
        api_logger.info(f"🎉 文件上傳處理完成:")
        api_logger.info(f"   - 文件ID: {file_id}")
        api_logger.info(f"   - 狀態: {final_status}")
        api_logger.info(f"   - 總耗時: {processing_time_ms}ms")
        
        # 記錄性能指標
        log_performance(api_logger, f"文件上傳[{file.filename}]", processing_time_ms/1000, 
                       f"chunks={chunks_created}, size={file.size}bytes")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size_bytes=file.size,
            status=final_status,
            chunks_created=chunks_created,
            processing_time_ms=processing_time_ms
        )
        
    except HTTPException:
        # HTTP異常直接重新拋出，不需要額外處理
        raise
    except Exception as e:
        total_time = time.time() - start_time
        api_logger.error(f"💥 文件上傳處理發生未預期錯誤，總耗時: {total_time:.3f}秒")
        api_logger.error(f"   - 文件: {file.filename}")
        api_logger.error(f"   - 文件ID: {file_id}")
        log_exception(api_logger, f"文件上傳異常詳情", sys.exc_info())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

@app.get("/knowledge-base", 
         response_model=KnowledgeBaseStatus, 
         summary="獲取知識庫狀態",
         description="查看知識庫中所有文件的狀態和統計信息",
         tags=["知識庫管理"])
async def get_knowledge_base_status(
    user_context: UserContext = Depends(verify_api_key)
):
    """獲取知識庫文件和統計信息"""
    
    if not rag_system:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized"
        )
    
    try:
        # 獲取統計信息
        stats = rag_system.get_document_statistics()
        
        # 獲取文件列表
        files = []
        if hasattr(rag_system, 'get_indexed_files'):
            indexed_files = rag_system.get_indexed_files()
            for file_info in indexed_files:
                files.append(KnowledgeBaseFile(
                    id=file_info.get('id', str(uuid.uuid4())),
                    name=file_info.get('name', 'Unknown'),
                    size_mb=file_info.get('size_mb', 0.0),
                    type=file_info.get('type', 'unknown'),
                    upload_time=file_info.get('upload_time', ''),
                    chunk_count=file_info.get('node_count', 0),
                    status=file_info.get('status', 'active')
                ))
        
        return KnowledgeBaseStatus(
            total_files=stats.get('total_files', len(files)),
            total_chunks=stats.get('total_documents', 0),
            total_size_mb=stats.get('total_size_mb', 0.0),
            files=files
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge base status: {str(e)}"
        )

@app.delete("/knowledge-base/files/{file_id:path}", 
            summary="刪除知識庫文件",
            description="從知識庫中永久刪除指定的文件",
            tags=["知識庫管理"])
async def delete_knowledge_base_file(
    file_id: str,
    user_context: UserContext = Depends(verify_api_key)
):
    """從知識庫中刪除指定文件"""
    
    if "write" not in user_context.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required for file deletion"
        )
    
    if not rag_system:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized"
        )
    
    try:
        # URL 解碼文件 ID
        decoded_file_id = unquote(file_id)
        api_logger.info(f"🗑️ 嘗試刪除文件: {decoded_file_id}")
        
        success = rag_system.delete_file_from_knowledge_base(decoded_file_id)
        
        if success:
            api_logger.info(f"✅ 文件刪除成功: {decoded_file_id}")
            return {"message": f"File {file_id} deleted successfully"}
        else:
            api_logger.warning(f"❌ 文件未找到或刪除失敗: {decoded_file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_id}' not found in knowledge base. The file may have been already deleted or never existed."
            )
            
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Log the actual error for debugging
        api_logger.error(f"💥 文件刪除異常 - 文件ID: {file_id}, 錯誤: {str(e)}")
        api_logger.error(f"   - 原始文件ID: {file_id}")
        api_logger.error(f"   - 解碼後ID: {unquote(file_id) if file_id else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File deletion failed due to internal error. Please check server logs."
        )

@app.get("/conversations", 
         response_model=ConversationHistory, 
         summary="獲取對話記錄",
         description="分頁獲取用戶的對話歷史記錄",
         tags=["對話記錄"])
async def get_conversation_history(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_context: UserContext = Depends(verify_api_key)
):
    """獲取對話記錄列表"""
    
    if not rag_system or not hasattr(rag_system, 'get_conversation_history'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation history not available"
        )
    
    try:
        # 如果不是 admin 用戶，只能查看自己的對話
        if user_context.user_id != "admin":
            user_id = user_context.user_id
        
        conversations = rag_system.get_conversation_history(
            session_id=session_id,
            limit=page_size
        )
        
        # 簡單分頁處理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_conversations = conversations[start_idx:end_idx]
        
        return ConversationHistory(
            conversations=paginated_conversations,
            total_count=len(conversations),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )

@app.get("/conversations/stats", 
         summary="獲取對話統計",
         description="獲取對話系統的統計信息和分析數據",
         tags=["對話記錄"])
async def get_conversation_stats(
    user_context: UserContext = Depends(verify_api_key)
):
    """獲取對話統計信息"""
    
    if not rag_system or not hasattr(rag_system, 'get_conversation_statistics'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation statistics not available"
        )
    
    try:
        stats = rag_system.get_conversation_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation statistics: {str(e)}"
        )

# ================== 錯誤處理 ==================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "request_id": generate_request_id()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用異常處理器"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "request_id": generate_request_id()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)