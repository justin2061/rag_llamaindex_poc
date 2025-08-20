"""
智能問答 FastAPI 接口
提供 RESTful API 服務於智能問答系統
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
from datetime import datetime
import traceback

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem

# FastAPI 實例
app = FastAPI(
    title="智能問答 API",
    description="基於 Elasticsearch 和 Graph RAG 的智能問答系統 API",
    version="1.0.0"
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制為特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 RAG 系統實例
rag_system = None

# 請求/響應模型
class QueryRequest(BaseModel):
    question: str
    include_sources: bool = True
    max_sources: int = 3

class SourceInfo(BaseModel):
    source: str
    file_path: str
    score: float
    content: str
    page: Optional[str] = None
    type: str = "user_document"

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo] = []
    metadata: Dict[str, Any] = {}
    timestamp: str

class SystemStatus(BaseModel):
    status: str
    elasticsearch_connected: bool
    total_documents: int
    system_info: Dict[str, Any]
    timestamp: str

class FileInfo(BaseModel):
    name: str
    chunk_count: int
    total_size_bytes: float
    size_mb: float
    file_type: str
    source: str

class KnowledgeBaseInfo(BaseModel):
    files: List[FileInfo]
    total_files: int
    total_chunks: int
    total_size_mb: float

# 啟動事件
@app.on_event("startup")
async def startup_event():
    """啟動時初始化 RAG 系統"""
    global rag_system
    try:
        print("🚀 正在初始化智能問答 API...")
        rag_system = ElasticsearchRAGSystem()
        
        if rag_system._initialize_elasticsearch():
            print("✅ Elasticsearch RAG 系統初始化成功")
        else:
            print("❌ Elasticsearch RAG 系統初始化失敗")
            
    except Exception as e:
        print(f"❌ RAG 系統初始化錯誤: {str(e)}")
        print(traceback.format_exc())

# API 端點
@app.get("/", summary="API 根端點")
async def root():
    """API 根端點，返回基本信息"""
    return {
        "message": "智能問答 API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/query",
            "status": "/api/status", 
            "knowledge_base": "/api/knowledge-base",
            "docs": "/docs"
        }
    }

@app.get("/api/status", response_model=SystemStatus, summary="獲取系統狀態")
async def get_system_status():
    """獲取系統狀態信息"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系統未初始化")
        
        # 獲取文檔統計
        stats = rag_system.get_document_statistics()
        
        # 檢查 Elasticsearch 連接
        es_connected = rag_system._initialize_elasticsearch()
        
        return SystemStatus(
            status="healthy" if es_connected else "degraded",
            elasticsearch_connected=es_connected,
            total_documents=stats.get('total_documents', 0),
            system_info={
                "total_nodes": stats.get('total_nodes', 0),
                "index_size_mb": stats.get('index_size_mb', 0),
                "backend": "Elasticsearch"
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取系統狀態失敗: {str(e)}")

@app.get("/api/knowledge-base", response_model=KnowledgeBaseInfo, summary="獲取知識庫信息")
async def get_knowledge_base_info():
    """獲取知識庫中的文件信息"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系統未初始化")
        
        files = rag_system.get_indexed_files()
        
        # 轉換為 API 模型
        file_infos = []
        total_chunks = 0
        total_size_mb = 0.0
        
        for file in files:
            file_info = FileInfo(
                name=file['name'],
                chunk_count=file['chunk_count'],
                total_size_bytes=file['total_size_bytes'],
                size_mb=file['size_mb'],
                file_type=file['file_type'],
                source=file['source']
            )
            file_infos.append(file_info)
            total_chunks += file['chunk_count']
            total_size_mb += file['size_mb']
        
        return KnowledgeBaseInfo(
            files=file_infos,
            total_files=len(file_infos),
            total_chunks=total_chunks,
            total_size_mb=round(total_size_mb, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取知識庫信息失敗: {str(e)}")

@app.post("/api/query", response_model=QueryResponse, summary="智能問答查詢")
async def query_knowledge_base(request: QueryRequest):
    """執行智能問答查詢"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系統未初始化")
        
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="問題不能為空")
        
        # 執行查詢
        if request.include_sources and hasattr(rag_system, 'query_with_sources'):
            # 使用帶來源的查詢
            result = rag_system.query_with_sources(request.question)
            answer = result['answer']
            sources = result['sources']
            metadata = result['metadata']
        else:
            # 使用普通查詢
            answer = rag_system.query(request.question)
            sources = []
            metadata = {"include_sources": False}
        
        # 處理來源信息
        source_infos = []
        if sources:
            for source in sources[:request.max_sources]:
                source_info = SourceInfo(
                    source=source['source'],
                    file_path=source['file_path'],
                    score=source['score'],
                    content=source['content'],
                    page=source.get('page', ''),
                    type=source['type']
                )
                source_infos.append(source_info)
        
        return QueryResponse(
            answer=answer,
            sources=source_infos,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 查詢錯誤: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@app.get("/api/health", summary="健康檢查")
async def health_check():
    """簡單的健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "智能問答 API"
    }

# 錯誤處理
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "端點未找到",
        "message": f"請求的路徑 {request.url.path} 不存在",
        "available_endpoints": [
            "/",
            "/api/status", 
            "/api/query",
            "/api/knowledge-base",
            "/api/health",
            "/docs"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 啟動智能問答 FastAPI 服務...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=False,
        access_log=True
    )