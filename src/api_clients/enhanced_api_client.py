"""
Enhanced API Client
用於Streamlit應用串接Enhanced RAG API V2.0的客戶端
"""

import requests
import logging
import streamlit as st
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAPIClient:
    """Enhanced RAG API V2.0 客戶端"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8003",
                 api_key: str = "demo-api-key-123"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.jwt_token = None
        self.token_expires_at = None
        
        # 初始化會話
        self.session = requests.Session()
        
        logger.info(f"🔧 EnhancedAPIClient 初始化")
        logger.info(f"   - API Base URL: {self.base_url}")
        
        # 自動獲取Token
        self._ensure_authenticated()
    
    def _ensure_authenticated(self):
        """確保已認證"""
        if (not self.jwt_token or 
            not self.token_expires_at or 
            datetime.now() >= self.token_expires_at - timedelta(minutes=5)):
            
            self._get_jwt_token()
    
    def _get_jwt_token(self):
        """獲取JWT Token"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/token",
                json={"api_key": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data["access_token"]
                expires_in = data.get("expires_in", 86400)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # 設置默認認證頭
                self.session.headers.update({
                    "Authorization": f"Bearer {self.jwt_token}"
                })
                
                logger.info("✅ JWT Token 獲取成功")
            else:
                raise Exception(f"Token獲取失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ JWT Token 獲取失敗: {e}")
            st.error(f"認證失敗: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"健康檢查失敗: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 健康檢查失敗: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def chat_query(self, 
                   question: str,
                   conversation_context: Optional[Dict] = None,
                   include_sources: bool = True,
                   max_sources: int = 3) -> Dict[str, Any]:
        """智能問答"""
        self._ensure_authenticated()
        
        try:
            payload = {
                "question": question,
                "include_sources": include_sources,
                "max_sources": max_sources,
                "user_id": st.session_state.get('user_id', 'streamlit_user'),
                "session_id": st.session_state.get('session_id', 'streamlit_session')
            }
            
            if conversation_context:
                payload["conversation_context"] = conversation_context
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 聊天查詢成功: {question[:50]}...")
                logger.info(f"   - 響應時間: {result.get('response_time_ms', 0)}ms")
                logger.info(f"   - 來源數量: {len(result.get('sources', []))}")
                
                # 記錄優化功能使用
                optimization_used = result.get('metadata', {}).get('optimization_used', [])
                if optimization_used:
                    logger.info(f"   - 使用優化: {', '.join(optimization_used)}")
                
                return result
            else:
                raise Exception(f"聊天查詢失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ 聊天查詢失敗: {e}")
            return {
                "answer": f"抱歉，查詢過程中發生錯誤: {str(e)}",
                "sources": [],
                "error": str(e),
                "conversation_id": None,
                "metadata": {},
                "context": {"conversation_id": None, "messages": [], "max_history": 10},
                "response_time_ms": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def upload_file(self, uploaded_file) -> Dict[str, Any]:
        """上傳文件"""
        self._ensure_authenticated()
        
        try:
            # 準備文件數據
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream"
                )
            }
            
            # 上傳請求（不設置Content-Type，讓requests自動設置）
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            
            response = requests.post(
                f"{self.base_url}/upload",
                files=files,
                headers=headers,
                timeout=120  # 文件上傳可能需要更長時間
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 文件上傳成功: {uploaded_file.name}")
                logger.info(f"   - 處理時間: {result.get('processing_time_ms', 0)}ms")
                logger.info(f"   - 創建chunks: {result.get('chunks_created', 0)}")
                return result
            else:
                raise Exception(f"文件上傳失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ 文件上傳失敗: {e}")
            return {
                "file_id": None,
                "filename": uploaded_file.name,
                "size_bytes": uploaded_file.size,
                "status": "failed",
                "chunks_created": 0,
                "processing_time_ms": 0,
                "error": str(e)
            }
    
    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """獲取知識庫狀態"""
        self._ensure_authenticated()
        
        try:
            response = self.session.get(
                f"{self.base_url}/knowledge-base",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"獲取知識庫狀態失敗: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 獲取知識庫狀態失敗: {e}")
            return {
                "total_files": 0,
                "total_chunks": 0,
                "total_size_mb": 0,
                "files": [],
                "error": str(e)
            }
    
    def delete_file_from_knowledge_base(self, file_id: str) -> bool:
        """從知識庫刪除文件"""
        self._ensure_authenticated()
        
        try:
            response = self.session.delete(
                f"{self.base_url}/knowledge-base/files/{file_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 文件刪除成功: {file_id}")
                return True
            else:
                logger.error(f"❌ 文件刪除失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 文件刪除失敗: {e}")
            return False
    
    def get_conversations(self, 
                         page: int = 1, 
                         page_size: int = 20,
                         user_id: Optional[str] = None,
                         session_id: Optional[str] = None) -> Dict[str, Any]:
        """獲取對話記錄"""
        self._ensure_authenticated()
        
        try:
            params = {"page": page, "page_size": page_size}
            if user_id:
                params["user_id"] = user_id
            if session_id:
                params["session_id"] = session_id
            
            response = self.session.get(
                f"{self.base_url}/conversations",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"獲取對話記錄失敗: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 獲取對話記錄失敗: {e}")
            return {
                "conversations": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "error": str(e)
            }
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """獲取對話統計"""
        self._ensure_authenticated()
        
        try:
            response = self.session.get(
                f"{self.base_url}/conversations/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"獲取對話統計失敗: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 獲取對話統計失敗: {e}")
            return {"error": str(e)}
    
    def batch_upload_files(self, uploaded_files: List) -> List[Dict[str, Any]]:
        """批量上傳文件"""
        results = []
        
        total_files = len(uploaded_files)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"正在處理文件 {i+1}/{total_files}: {uploaded_file.name}")
                
                result = self.upload_file(uploaded_file)
                results.append(result)
                
                progress = (i + 1) / total_files
                progress_bar.progress(progress)
                
            except Exception as e:
                logger.error(f"❌ 批量上傳文件失敗 {uploaded_file.name}: {e}")
                results.append({
                    "filename": uploaded_file.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    def clear_knowledge_base(self) -> bool:
        """清空知識庫（通過刪除所有文件實現）"""
        try:
            # 獲取所有文件
            kb_status = self.get_knowledge_base_status()
            files = kb_status.get("files", [])
            
            if not files:
                logger.info("✅ 知識庫已經是空的")
                return True
            
            # 逐個刪除文件
            success_count = 0
            for file_info in files:
                file_id = file_info.get("id")
                if file_id and self.delete_file_from_knowledge_base(file_id):
                    success_count += 1
            
            if success_count == len(files):
                logger.info(f"✅ 知識庫清空成功，刪除了 {success_count} 個文件")
                return True
            else:
                logger.warning(f"⚠️ 部分文件刪除失敗，成功刪除 {success_count}/{len(files)} 個文件")
                return success_count > 0
                
        except Exception as e:
            logger.error(f"❌ 清空知識庫失敗: {e}")
            return False
    
    def test_connection(self) -> bool:
        """測試API連接"""
        try:
            health = self.health_check()
            return health.get("status") == "healthy"
        except:
            return False