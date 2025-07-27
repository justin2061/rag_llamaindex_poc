import os
import shutil
from typing import Optional, List, Dict, Any
import streamlit as st
import chromadb
from chromadb.config import Settings as ChromaSettings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore

from config import INDEX_DIR

class ChromaVectorStoreManager:
    def __init__(self, persist_path: str = None):
        self.persist_path = persist_path or os.path.join("data", "chroma_db")
        self.collection_name = "documents"
        self.client = None
        self.collection = None
        self.vector_store = None
        
        # 確保目錄存在
        os.makedirs(self.persist_path, exist_ok=True)
        
    def initialize_client(self) -> bool:
        """初始化 ChromaDB 客戶端"""
        try:
            # 確保目錄清潔
            if os.path.exists(self.persist_path):
                # 檢查是否有損壞的檔案
                sqlite_file = os.path.join(self.persist_path, "chroma.sqlite3")
                if os.path.exists(sqlite_file):
                    try:
                        # 嘗試測試資料庫檔案
                        import sqlite3
                        conn = sqlite3.connect(sqlite_file)
                        conn.execute("SELECT 1").fetchone()
                        conn.close()
                    except Exception as db_e:
                        st.warning(f"檢測到損壞的 ChromaDB 檔案，正在清理: {str(db_e)}")
                        import shutil
                        shutil.rmtree(self.persist_path)
                        os.makedirs(self.persist_path, exist_ok=True)
            
            # 創建持久化客戶端
            self.client = chromadb.PersistentClient(
                path=self.persist_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            # 獲取或創建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Multi-modal document collection"}
            )
            
            # 創建向量儲存
            self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
            
            st.info(f"✅ ChromaDB 初始化成功: {self.persist_path}")
            return True
            
        except Exception as e:
            st.error(f"初始化 ChromaDB 時發生錯誤: {str(e)}")
            st.error(f"錯誤詳情: {type(e).__name__}")
            # 清理失敗的初始化
            self.client = None
            self.collection = None
            self.vector_store = None
            return False
    
    def get_storage_context(self) -> Optional[StorageContext]:
        """獲取儲存上下文"""
        if not self.vector_store:
            if not self.initialize_client():
                return None
        
        try:
            # 創建儲存上下文
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store,
                docstore=SimpleDocumentStore(),
                index_store=SimpleIndexStore()
            )
            
            return storage_context
            
        except Exception as e:
            st.error(f"創建儲存上下文時發生錯誤: {str(e)}")
            return None
    
    def migrate_from_simple_vector_store(self, old_index_dir: str = INDEX_DIR) -> bool:
        """從 SimpleVectorStore 遷移數據到 ChromaDB"""
        try:
            # 檢查是否有舊的索引數據
            if not os.path.exists(old_index_dir) or not os.listdir(old_index_dir):
                st.info("沒有找到舊的索引數據，跳過遷移")
                return True
            
            st.info("正在遷移舊的向量數據到 ChromaDB...")
            
            # 載入舊的索引
            from llama_index.core import load_index_from_storage
            old_storage_context = StorageContext.from_defaults(persist_dir=old_index_dir)
            old_index = load_index_from_storage(old_storage_context)
            
            # 獲取新的儲存上下文
            new_storage_context = self.get_storage_context()
            if not new_storage_context:
                return False
            
            # 重建索引到新的向量儲存
            documents = []
            for node_id, node in old_index.docstore.docs.items():
                documents.append(node)
            
            if documents:
                # 使用新的儲存上下文創建索引
                new_index = VectorStoreIndex.from_documents(
                    documents, 
                    storage_context=new_storage_context
                )
                
                # 持久化新索引
                new_index.storage_context.persist(persist_dir=old_index_dir)
                
                st.success(f"✅ 成功遷移 {len(documents)} 個文檔到 ChromaDB")
                return True
            else:
                st.warning("沒有找到可遷移的文檔")
                return True
                
        except Exception as e:
            st.error(f"數據遷移失敗: {str(e)}")
            return False
    
    def has_data(self) -> bool:
        """檢查 ChromaDB 是否有資料"""
        if not self.collection:
            if not self.initialize_client():
                return False
        
        try:
            count = self.collection.count()
            return count > 0
        except Exception as e:
            st.warning(f"檢查 ChromaDB 資料時發生錯誤: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """獲取集合統計資訊"""
        if not self.collection:
            return {}
        
        try:
            count = self.collection.count()
            
            # 獲取元數據統計
            metadata_stats = {}
            if count > 0:
                # 獲取所有文檔的元數據
                results = self.collection.get(include=['metadatas'])
                metadatas = results.get('metadatas', [])
                
                # 統計資料來源類型
                source_types = {}
                for metadata in metadatas:
                    if metadata:
                        doc_type = metadata.get('type', 'unknown')
                        source_types[doc_type] = source_types.get(doc_type, 0) + 1
                
                metadata_stats = source_types
            
            return {
                'total_documents': count,
                'source_types': metadata_stats,
                'collection_name': self.collection_name,
                'persist_path': self.persist_path
            }
            
        except Exception as e:
            st.error(f"獲取統計資訊時發生錯誤: {str(e)}")
            return {}
    
    def query_with_filters(self, query_vector: List[float], n_results: int = 5, 
                          source_types: List[str] = None) -> Dict[str, Any]:
        """帶過濾條件的查詢"""
        if not self.collection:
            return {}
        
        try:
            where_clause = {}
            if source_types:
                where_clause = {"type": {"$in": source_types}}
            
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            return results
            
        except Exception as e:
            st.error(f"過濾查詢時發生錯誤: {str(e)}")
            return {}
    
    def clear_collection(self) -> bool:
        """清空集合"""
        try:
            if self.collection:
                # 刪除所有文檔
                all_ids = self.collection.get()['ids']
                if all_ids:
                    self.collection.delete(ids=all_ids)
                st.success("✅ 集合已清空")
                return True
            return False
            
        except Exception as e:
            st.error(f"清空集合時發生錯誤: {str(e)}")
            return False
    
    def reset_database(self) -> bool:
        """重置資料庫"""
        try:
            if self.client:
                self.client.reset()
                st.success("✅ ChromaDB 資料庫已重置")
                return True
            return False
            
        except Exception as e:
            st.error(f"重置資料庫時發生錯誤: {str(e)}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """備份資料庫"""
        try:
            if os.path.exists(self.persist_path):
                shutil.copytree(self.persist_path, backup_path, dirs_exist_ok=True)
                st.success(f"✅ 資料庫已備份到: {backup_path}")
                return True
            return False
            
        except Exception as e:
            st.error(f"備份資料庫時發生錯誤: {str(e)}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """還原資料庫"""
        try:
            if os.path.exists(backup_path):
                # 停止當前客戶端
                if self.client:
                    del self.client
                
                # 移除現有資料庫
                if os.path.exists(self.persist_path):
                    shutil.rmtree(self.persist_path)
                
                # 還原備份
                shutil.copytree(backup_path, self.persist_path)
                
                # 重新初始化
                self.initialize_client()
                
                st.success(f"✅ 資料庫已從備份還原: {backup_path}")
                return True
            return False
            
        except Exception as e:
            st.error(f"還原資料庫時發生錯誤: {str(e)}")
            return False
