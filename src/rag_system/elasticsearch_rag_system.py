import os
import json
from typing import List, Dict, Any, Optional
import streamlit as st
from datetime import datetime
import traceback

# LlamaIndex 核心
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# 對話記錄管理
from src.storage.conversation_history import ConversationHistoryManager

# Elasticsearch integration
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    st.warning("⚠️ Elasticsearch dependencies not installed. Install with: pip install elasticsearch")

# 繼承增強版系統
from .enhanced_rag_system import EnhancedRAGSystem
from config.config import (
    GROQ_API_KEY, EMBEDDING_MODEL, LLM_MODEL, 
    ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_SCHEME,
    ELASTICSEARCH_INDEX_NAME, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD,
    ELASTICSEARCH_TIMEOUT, ELASTICSEARCH_MAX_RETRIES, ELASTICSEARCH_VERIFY_CERTS,
    ELASTICSEARCH_SHARDS, ELASTICSEARCH_REPLICAS, ELASTICSEARCH_VECTOR_DIMENSION,
    ELASTICSEARCH_SIMILARITY
)

class ElasticsearchRAGSystem(EnhancedRAGSystem):
    """Elasticsearch RAG 系統 - 高效能、可擴展的向量檢索"""
    
    def __init__(self, elasticsearch_config: Optional[Dict] = None):
        """初始化 Elasticsearch RAG 系統"""
        # 首先設置 elasticsearch_config，避免在父類初始化時引用錯誤
        self.elasticsearch_config = elasticsearch_config or self._get_default_config()
        self.elasticsearch_client = None
        self.elasticsearch_store = None
        
        # 使用配置文件中的索引名稱
        from config.config import ELASTICSEARCH_INDEX_NAME
        self.index_name = ELASTICSEARCH_INDEX_NAME
        
        # 記憶體使用監控
        self.memory_stats = {
            'documents_processed': 0,
            'vectors_stored': 0,
            'peak_memory_mb': 0
        }
        
        # 模型實例
        self.embedding_model = None
        self.llm_model = None
        
        # 初始化對話記錄管理器
        self.conversation_manager = ConversationHistoryManager(elasticsearch_config)
        
        # 調用父類初始化，但禁用其 Elasticsearch 自動初始化
        super().__init__(use_elasticsearch=False, use_chroma=False)  # 先設置為 False
        
        # 然後手動設置標誌並初始化 Elasticsearch 
        self.use_elasticsearch = True
        if self._initialize_elasticsearch():
            # 如果初始化成功，嘗試載入現有索引
            self.load_existing_index()
    
    def _initialize_elasticsearch(self):
        """初始化 Elasticsearch 連接和向量存儲"""
        try:
            if self._setup_elasticsearch_client():
                if self._create_elasticsearch_index():
                    if self._setup_elasticsearch_store():
                        st.success("✅ Elasticsearch RAG 系統初始化完成")
                        # 確保 use_elasticsearch 標誌正確設置
                        self.use_elasticsearch = True
                        return True
                    else:
                        st.error("❌ Elasticsearch 向量存儲設置失敗")
                        self.use_elasticsearch = False
                else:
                    st.error("❌ Elasticsearch 索引創建失敗")
                    self.use_elasticsearch = False
            else:
                st.error("❌ Elasticsearch 客戶端連接失敗")
                self.use_elasticsearch = False
            return False
        except Exception as e:
            st.error(f"❌ Elasticsearch 初始化失敗: {str(e)}")
            self.use_elasticsearch = False
            return False
    
    def _ensure_models_initialized(self):
        """確保模型已初始化並存儲為實例屬性"""
        if not self.models_initialized or self.embedding_model is None:
            super()._ensure_models_initialized()
            
            # 從 Settings 獲取模型並存儲為實例屬性
            from llama_index.core import Settings
            self.embedding_model = Settings.embed_model
            self.llm_model = Settings.llm
            
            st.info("✅ Elasticsearch RAG 系統模型初始化完成")
    
    def _get_default_config(self) -> Dict:
        """獲取預設 Elasticsearch 配置"""
        return {
            'host': ELASTICSEARCH_HOST or 'localhost',
            'port': ELASTICSEARCH_PORT or 9200,
            'scheme': ELASTICSEARCH_SCHEME or 'http',
            'username': ELASTICSEARCH_USERNAME,
            'password': ELASTICSEARCH_PASSWORD,
            'timeout': ELASTICSEARCH_TIMEOUT or 30,
            'max_retries': ELASTICSEARCH_MAX_RETRIES or 3,
            'verify_certs': ELASTICSEARCH_VERIFY_CERTS,
            'index_name': ELASTICSEARCH_INDEX_NAME or 'rag_intelligent_assistant',
            'shards': ELASTICSEARCH_SHARDS or 1,
            'replicas': ELASTICSEARCH_REPLICAS or 0,
            'dimension': ELASTICSEARCH_VECTOR_DIMENSION or 1024,
            'similarity': ELASTICSEARCH_SIMILARITY or 'cosine',
            'text_field': 'content',
            'vector_field': 'embedding',
            'metadata_fields': ['source', 'page', 'chunk_id', 'timestamp', 'file_type', 'file_size']
        }
    
    def _setup_elasticsearch_client(self) -> bool:
        """設置 Elasticsearch 客戶端（統一使用同步客戶端）"""
        if not ELASTICSEARCH_AVAILABLE:
            st.error("❌ Elasticsearch 依賴未安裝")
            return False
            
        try:
            config = self.elasticsearch_config
            
            # 統一使用同步客戶端 - LlamaIndex ElasticsearchStore 需要同步客戶端
            from elasticsearch import Elasticsearch
            
            # 建立連接配置 - 使用同步客戶端
            es_config = {
                'hosts': [{
                    'host': config['host'],
                    'port': config['port'],
                    'scheme': config['scheme']
                }],
                'request_timeout': config['timeout'],
                'max_retries': 3,
                'retry_on_timeout': True
            }
            
            # 添加驗證信息（如果配置了）
            if config.get('username') and config.get('password'):
                es_config['basic_auth'] = (config['username'], config['password'])
            
            # 創建同步客戶端（ElasticsearchStore 要求）
            sync_client = Elasticsearch(**es_config)
            
            # 測試連接
            if sync_client.ping():
                st.success(f"✅ 成功連接到 Elasticsearch: {config['host']}:{config['port']}")
                
                # 顯示集群信息
                try:
                    cluster_info = sync_client.info()
                    st.info(f"📊 ES 集群版本: {cluster_info.get('version', {}).get('number', 'unknown')}")
                except:
                    pass
                
                # 統一使用同步客戶端
                self.elasticsearch_client = sync_client
                self.sync_elasticsearch_client = sync_client
                
                print(f"✅ ES客戶端初始化完成，類型: {type(self.elasticsearch_client)}")
                
                return True
            else:
                st.error("❌ 無法連接到 Elasticsearch")
                return False
                
        except Exception as e:
            st.error(f"❌ Elasticsearch 客戶端設置失敗: {str(e)}")
            return False
    
    def _create_elasticsearch_index(self) -> bool:
        """創建 Elasticsearch 索引"""
        try:
            config = self.elasticsearch_config
            
            # 驗證/對齊嵌入維度
            try:
                # 使用 EnhancedRAGSystem 的維度檢測
                actual_dim = self._get_embed_dim()
            except Exception:
                actual_dim = None
            expected_dim = config.get('dimension')
            
            if actual_dim is not None and expected_dim and int(actual_dim) != int(expected_dim):
                st.warning(f"⚠️ 檢測到模型維度 {actual_dim} 與配置維度 {expected_dim} 不一致，將以模型維度為準。")
                config['dimension'] = int(actual_dim)
            
            # 最終維度驗證
            if not self._validate_embedding_dimension(config['dimension']):
                st.error("❌ 嵌入維度驗證失敗，停止建立索引。")
                return False
            
            # 索引映射設定 (使用中文分析器)
            index_mapping = {
                "settings": {
                    "number_of_shards": config['shards'],
                    "number_of_replicas": config['replicas'],
                    "analysis": {
                        "analyzer": {
                            "chinese_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "cjk_width", "cjk_bigram"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        config['text_field']: {
                            "type": "text",
                            "analyzer": "chinese_analyzer",
                            "search_analyzer": "chinese_analyzer"
                        },
                        config['vector_field']: {
                            "type": "dense_vector",
                            "dims": config['dimension'],
                            "index": True,
                            "similarity": config['similarity']
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "keyword"},
                                "page": {"type": "integer"},
                                "chunk_id": {"type": "keyword"},
                                "timestamp": {"type": "date"},
                                "file_type": {"type": "keyword"},
                                "file_size": {"type": "integer"}
                            }
                        }
                    }
                }
            }
            
            # 檢查索引是否存在（使用同步客戶端）
            sync_client = getattr(self, 'sync_elasticsearch_client', None)
            if not sync_client:
                # 如果沒有同步客戶端，創建一個
                from elasticsearch import Elasticsearch
                sync_client = Elasticsearch(**{
                    'hosts': [{'host': config['host'], 'port': config['port'], 'scheme': config['scheme']}],
                    'request_timeout': config['timeout'],
                })
                self.sync_elasticsearch_client = sync_client
            
            if sync_client.indices.exists(index=self.index_name):
                st.info(f"📚 索引 '{self.index_name}' 已存在")
                return True
            
            # 創建索引（使用同步客戶端）
            try:
                st.info(f"🔧 正在创建索引: {self.index_name}")
                response = sync_client.indices.create(
                    index=self.index_name,
                    body=index_mapping,
                    ignore=400  # 忽略已存在的錯誤
                )
                
                if response.get('acknowledged', False):
                    st.success(f"✅ 成功创建索引: {self.index_name}")
                    # 驗證索引创建
                    if sync_client.indices.exists(index=self.index_name):
                        st.info("📋 索引创建验证通过")
                    return True
                else:
                    st.error(f"❌ 索引創建失敗: {response}")
                    return False
                    
            except Exception as create_error:
                # 如果是 HeadApiResponse async 錯誤，嘗試同步方式
                error_msg = str(create_error)
                if "HeadApiResponse" in error_msg or "await" in error_msg:
                    st.warning(f"⚠️ 檢測到async兼容性問題，嘗試同步方式創建索引...")
                    try:
                        # 使用同步 Elasticsearch 客戶端重新初始化
                        from elasticsearch import Elasticsearch
                        sync_client = Elasticsearch(
                            [{'host': self.elasticsearch_config['host'], 'port': self.elasticsearch_config['port']}],
                            timeout=30,
                            request_timeout=30
                        )
                        
                        # 測試連接
                        if sync_client.ping():
                            # 使用同步客戶端創建索引
                            response = sync_client.indices.create(
                                index=self.index_name,
                                body=index_mapping,
                                ignore=400
                            )
                            # 更新客戶端為同步版本
                            self.elasticsearch_client = sync_client
                            st.success(f"✅ 使用同步客戶端成功創建索引: {self.index_name}")
                            return True
                        else:
                            st.error("❌ 同步客戶端無法連接到 Elasticsearch")
                            return False
                    except Exception as sync_error:
                        st.error(f"❌ 同步創建索引也失敗: {str(sync_error)}")
                        return False
                else:
                    st.error(f"❌ 創建索引失敗: {error_msg}")
                    return False
        except Exception as e:
            st.error(f"❌ 創建索引時發生錯誤: {str(e)}")
            return False
                
    def query(self, query_str: str, **kwargs) -> str:
        """執行查詢並返回結果字符串"""
        if not self.query_engine:
            return "❌ 查詢引擎尚未設置。請先上傳並索引文檔。"
        
        try:
            print(f"🔍 開始執行查詢: {query_str}")
            print(f"🔧 查詢引擎類型: {type(self.query_engine)}")
            
            response = self.query_engine.query(query_str)
            
            print(f"✅ 查詢完成，響應類型: {type(response)}")
            return str(response)
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            print(f"❌ 查詢錯誤詳情:")
            print(f"   錯誤類型: {error_type}")
            print(f"   錯誤消息: {error_msg}")
            
            # 檢查是否為 ObjectApiResponse 錯誤
            if "ObjectApiResponse" in error_msg or "await" in error_msg:
                print("🚨 檢測到ObjectApiResponse錯誤！")
                print(f"   查詢引擎: {type(self.query_engine)}")
                if hasattr(self.query_engine, '_retriever'):
                    print(f"   檢索器: {type(self.query_engine._retriever)}")
                
            import traceback
            print(f"🔍 完整錯誤堆疊:")
            print(traceback.format_exc())
            
            st.error(f"查詢時發生錯誤: {error_msg}")
            st.write(traceback.format_exc())
            return f"查詢失敗: {error_msg}"
    
    def query_with_sources(self, query_str: str, save_to_history: bool = True, session_id: str = None, user_id: str = None, **kwargs) -> Dict[str, Any]:
        """執行查詢並返回帶有來源信息的完整結果"""
        if not self.query_engine:
            return {
                "answer": "❌ 查詢引擎尚未設置。請先上傳並索引文檔。",
                "sources": [],
                "metadata": {}
            }
        
        start_time = datetime.now()
        
        try:
            print(f"🔍 開始執行帶來源的查詢: {query_str}")
            print(f"🔧 查詢引擎類型: {type(self.query_engine)}")
            
            response = self.query_engine.query(query_str)
            
            print(f"✅ 查詢完成，響應類型: {type(response)}")
            
            # 提取答案
            answer = str(response)
            
            # 提取來源信息
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                print(f"📚 找到 {len(response.source_nodes)} 個來源節點")
                for i, node in enumerate(response.source_nodes):
                    source_info = {
                        "content": node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text,
                        "source": node.node.metadata.get("source", "未知來源"),
                        "file_path": node.node.metadata.get("file_path", ""),
                        "score": float(node.score) if hasattr(node, 'score') else 0.0,
                        "page": node.node.metadata.get("page", ""),
                        "type": node.node.metadata.get("type", "user_document")
                    }
                    sources.append(source_info)
                    print(f"  [{i+1}] 來源: {source_info['source']}, 評分: {source_info['score']}")
            else:
                print("❌ 響應中沒有找到來源節點")
            
            # 計算響應時間
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            metadata = {
                "query": query_str,
                "total_sources": len(sources),
                "response_time_ms": response_time_ms,
                "model": "Groq LLama 3.3",
                "backend": "Elasticsearch"
            }
            
            result = {
                "answer": answer,
                "sources": sources,
                "metadata": metadata
            }
            
            # 保存到對話記錄
            if save_to_history and self.conversation_manager:
                try:
                    conversation_id = self.conversation_manager.save_conversation(
                        question=query_str,
                        answer=answer,
                        sources=sources,
                        metadata=metadata,
                        session_id=session_id,
                        user_id=user_id
                    )
                    if conversation_id:
                        result["conversation_id"] = conversation_id
                        print(f"💾 對話記錄已保存: {conversation_id}")
                except Exception as save_error:
                    print(f"⚠️ 保存對話記錄失敗: {str(save_error)}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 帶來源查詢失敗: {error_msg}")
            import traceback
            print(f"🔍 完整錯誤堆疊: {traceback.format_exc()}")
            
            return {
                "answer": f"查詢失敗: {error_msg}",
                "sources": [],
                "metadata": {"error": error_msg}
            }
                
    def _setup_elasticsearch_store(self) -> bool:
        """設置 Elasticsearch 向量存儲"""
        try:
            # 使用統一的同步客戶端
            if not hasattr(self, 'elasticsearch_client') or not self.elasticsearch_client:
                st.error("❌ Elasticsearch 客戶端未初始化")
                return False
            
            print(f"🔧 設置ElasticsearchStore，客戶端類型: {type(self.elasticsearch_client)}")
            
            # 使用自定義同步 Elasticsearch Store 避免 async 問題
            from ..storage.custom_elasticsearch_store import CustomElasticsearchStore
            self.elasticsearch_store = CustomElasticsearchStore(
                es_client=self.elasticsearch_client,
                index_name=self.index_name,
                vector_field=self.elasticsearch_config['vector_field'],
                text_field=self.elasticsearch_config['text_field'],
                metadata_field='metadata'
            )
            
            st.success("✅ Elasticsearch 向量存儲設置完成 (使用同步客戶端)")
            return True
                
        except Exception as e:
            st.error(f"❌ Elasticsearch 向量存儲設置失敗: {str(e)}")
            import traceback
            st.error(f"詳細錯誤: {traceback.format_exc()}")
            return False
    
    def load_existing_index(self) -> bool:
        """載入現有的 Elasticsearch 索引"""
        try:
            # 設置 Elasticsearch 客戶端
            if not self._setup_elasticsearch_client():
                st.error("❌ 無法連接到 Elasticsearch")
                return False
            
            # 檢查索引是否存在（使用同步客戶端）
            sync_client = getattr(self, 'sync_elasticsearch_client', None)
            if sync_client and sync_client.indices.exists(index=self.index_name):
                # 獲取索引統計資訊
                stats = sync_client.indices.stats(index=self.index_name)
                doc_count = stats['indices'][self.index_name]['total']['docs']['count']
                
                if doc_count > 0:
                    # 驗證索引維度與嵌入模型
                    try:
                        mapping = sync_client.indices.get_mapping(index=self.index_name)
                        props = mapping[self.index_name]['mappings']['properties']
                        vec_field = self.elasticsearch_config['vector_field']
                        index_dims = props.get(vec_field, {}).get('dims')
                    except Exception:
                        index_dims = None

                    model_dim = None
                    try:
                        model_dim = self._get_embed_dim()
                    except Exception:
                        pass

                    if index_dims is not None and model_dim is not None and int(index_dims) != int(model_dim):
                        st.error(f"❌ 嵌入維度不一致：索引為 {index_dims}，模型為 {model_dim}。請對齊後重試。")
                        return False

                    # 設置向量存儲
                    if self._setup_elasticsearch_store():
                        # 確保模型初始化
                        self._ensure_models_initialized()
                        
                        # 重新創建索引對象
                        storage_context = StorageContext.from_defaults(vector_store=self.elasticsearch_store)
                        self.index = VectorStoreIndex.from_vector_store(
                            vector_store=self.elasticsearch_store,
                            storage_context=storage_context,
                            embed_model=self.embedding_model
                        )
                        
                        # 設置查詢引擎
                        self.setup_query_engine()
                        return True
                    else:
                        st.error("❌ Elasticsearch 向量存儲設置失敗")
                        return False
                else:
                    st.info(f"📚 索引 '{self.index_name}' 存在但為空")
                    return False
            else:
                st.info("💡 沒有發現現有的 Elasticsearch 索引，請上傳文檔來建立新索引")
                return False
                
        except Exception as e:
            st.error(f"❌ 載入 Elasticsearch 索引失敗: {str(e)}")
            return False
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """獲取 Elasticsearch RAG 系統的統計資訊"""
        try:
            stats = {
                "system_type": "elasticsearch",
                "base_statistics": self.memory_stats.copy(),
                "elasticsearch_stats": {}
            }
            
            # 使用同步客戶端進行統計查詢
            sync_client = getattr(self, 'sync_elasticsearch_client', None)
            if sync_client and self.index_name:
                try:
                    # 先刷新索引確保最新數據
                    sync_client.indices.refresh(index=self.index_name)
                    
                    # 獲取索引統計
                    index_stats = sync_client.indices.stats(index=self.index_name)
                    total_stats = index_stats['indices'][self.index_name]['total']
                    
                    stats["elasticsearch_stats"] = {
                        "index_name": self.index_name,
                        "document_count": total_stats['docs']['count'],
                        "index_size_bytes": total_stats['store']['size_in_bytes'],
                        "index_size_mb": round(total_stats['store']['size_in_bytes'] / 1024 / 1024, 2)
                    }
                    
                    # 更新基礎統計
                    stats["base_statistics"]["total_documents"] = total_stats['docs']['count']
                    stats["base_statistics"]["total_nodes"] = total_stats['docs']['count']
                    
                    # 記錄詳細統計日誌
                    print(f"📊 ES統計更新: 索引={self.index_name}, 文檔數={total_stats['docs']['count']}")
                    
                except Exception as e:
                    st.warning(f"無法獲取 Elasticsearch 統計: {e}")
                    # 如果索引不存在，統計為0
                    if "index_not_found" in str(e).lower():
                        stats["elasticsearch_stats"] = {
                            "index_name": self.index_name,
                            "document_count": 0,
                            "index_size_bytes": 0,
                            "index_size_mb": 0
                        }
                    
            return stats
            
        except Exception as e:
            st.error(f"統計資訊獲取失敗: {e}")
            return {
                "system_type": "elasticsearch", 
                "base_statistics": self.memory_stats.copy(),
                "elasticsearch_stats": {}
            }
    
    def get_elasticsearch_statistics(self) -> Dict[str, Any]:
        """獲取詳細的 Elasticsearch 統計資訊"""
        return self.get_enhanced_statistics()
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """覆寫父類方法，使用 Elasticsearch 專用統計"""
        try:
            # 使用 Elasticsearch 專用統計方法
            enhanced_stats = self.get_enhanced_statistics()
            
            # 轉換為標準格式以保持兼容性
            es_stats = enhanced_stats.get("elasticsearch_stats", {})
            base_stats = enhanced_stats.get("base_statistics", {})
            
            return {
                "total_documents": es_stats.get("document_count", 0),
                "total_nodes": es_stats.get("document_count", 0),
                "document_details": [],
                "total_pages": 0,
                "index_size_bytes": es_stats.get("index_size_bytes", 0),
                "index_size_mb": es_stats.get("index_size_mb", 0)
            }
        except Exception as e:
            st.error(f"獲取文檔統計時發生錯誤: {str(e)}")
            return {
                "total_documents": 0,
                "total_nodes": 0,
                "document_details": [],
                "total_pages": 0
            }
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """獲取已索引的文件列表 (Elasticsearch 版本)"""
        try:
            return self.get_indexed_files_from_es()
        except Exception as e:
            st.error(f"獲取文件列表時發生錯誤: {str(e)}")
            return []
    
    def delete_documents_by_source(self, source_filename: str) -> bool:
        """根據來源文件名刪除文檔"""
        sync_client = getattr(self, 'sync_elasticsearch_client', None)
        if not sync_client:
            st.error("❌ Elasticsearch 同步客戶端未初始化")
            return False
        
        try:
            # 構建查詢以查找指定來源的文檔
            query = {
                "query": {
                    "term": {
                        "metadata.source.keyword": source_filename
                    }
                }
            }
            
            # 刷除匹配的文檔
            response = sync_client.delete_by_query(
                index=self.index_name,
                body=query
            )
            
            deleted_count = response.get('deleted', 0)
            if deleted_count > 0:
                st.success(f"✅ 從 Elasticsearch 中刪除了 {deleted_count} 個文檔塊（來源：{source_filename}）")
                return True
            else:
                st.info(f"📝 在 Elasticsearch 中沒有找到來源為 '{source_filename}' 的文檔")
                return False
                
        except Exception as e:
            st.error(f"❌ 從 Elasticsearch 刪除文檔失敗: {str(e)}")
            return False
    
    def get_indexed_files_from_es(self) -> List[Dict[str, Any]]:
        """從 ES 索引中獲取已索引的文件列表"""
        # 使用 Elasticsearch 客戶端進行查詢
        es_client = getattr(self, 'elasticsearch_client', None)
        if not es_client:
            return []
        
        try:
            # 聚合查詢獲取不同的文件來源
            query = {
                "size": 0,
                "aggs": {
                    "unique_sources": {
                        "terms": {
                            "field": "metadata.source",
                            "size": 1000
                        },
                        "aggs": {
                            "total_size": {
                                "sum": {
                                    "field": "metadata.file_size"
                                }
                            },
                            "file_type": {
                                "terms": {
                                    "field": "metadata.file_type",
                                    "size": 1
                                }
                            },
                            "latest_timestamp": {
                                "max": {
                                    "field": "metadata.timestamp"
                                }
                            }
                        }
                    }
                }
            }
            
            response = es_client.search(
                index=self.index_name,
                body=query
            )
            
            files = []
            buckets = response.get('aggregations', {}).get('unique_sources', {}).get('buckets', [])
            
            for bucket in buckets:
                source_file = bucket['key']
                chunk_count = bucket['doc_count']  # 直接從 terms 聚合取得文檔數
                total_size = bucket.get('total_size', {}).get('value', 0)
                file_type_buckets = bucket.get('file_type', {}).get('buckets', [])
                file_type = file_type_buckets[0]['key'] if file_type_buckets else 'unknown'
                timestamp = bucket.get('latest_timestamp', {}).get('value_as_string', '')
                
                files.append({
                    'name': source_file,
                    'chunk_count': chunk_count,
                    'node_count': chunk_count,  # 添加 node_count 字段兼容性
                    'total_size_bytes': total_size,
                    'size': total_size,  # 為了兼容性保留 size 字段
                    'size_mb': round(total_size / (1024 * 1024), 1) if total_size > 0 else 0,
                    'file_type': file_type,
                    'timestamp': timestamp,
                    'source': 'elasticsearch'
                })
            
            return files
            
        except Exception as e:
            st.warning(f"從 ES 獲取文件列表失敗: {str(e)}")
            return []
    
    def get_knowledge_base_file_stats(self) -> Dict[str, Any]:
        """獲取知識庫文件統計（從ES索引）"""
        files = self.get_indexed_files_from_es()
        
        total_files = len(files)
        total_chunks = sum(f['chunk_count'] for f in files)
        total_size_mb = sum(f['size_mb'] for f in files)
        
        # 按文件類型分類
        pdf_files = [f for f in files if f['file_type'] == 'pdf']
        image_files = [f for f in files if f['file_type'] in ['png', 'jpg', 'jpeg', 'webp', 'bmp']]
        doc_files = [f for f in files if f['file_type'] in ['txt', 'docx', 'md']]
        
        return {
            'total_files': total_files,
            'total_chunks': total_chunks,
            'total_size_mb': round(total_size_mb, 2),
            'pdf_count': len(pdf_files),
            'image_count': len(image_files),
            'document_count': len(doc_files),
            'files': files
        }
    
    def get_conversation_history(self, session_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取對話記錄"""
        if self.conversation_manager:
            return self.conversation_manager.get_conversation_history(
                session_id=session_id, 
                limit=limit
            )
        return []
    
    def search_conversation_history(self, query_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索對話記錄"""
        if self.conversation_manager:
            return self.conversation_manager.search_conversations(query_text, limit)
        return []
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """獲取對話統計信息"""
        if self.conversation_manager:
            return self.conversation_manager.get_conversation_statistics()
        return {}
    
    def update_conversation_feedback(self, conversation_id: str, rating: int = None, feedback: str = None) -> bool:
        """更新對話反饋"""
        if self.conversation_manager:
            return self.conversation_manager.update_conversation_feedback(
                conversation_id, rating, feedback
            )
        return False

    def refresh_index(self):
        """刪除文檔後刷新索引"""
        try:
            # 使用同步客戶端進行索引刷新
            sync_client = getattr(self, 'sync_elasticsearch_client', None)
            if sync_client:
                print("🔄 正在使用同步客戶端刷新ES索引...")
                sync_client.indices.refresh(index=self.index_name)
                st.info("🔄 Elasticsearch 索引已刷新")
                print("✅ ES索引刷新完成")
            else:
                st.warning("⚠️ 同步ES客戶端不可用，無法刷新索引")
        except Exception as e:
            st.warning(f"索引刷新警告: {str(e)}")
            print(f"❌ 索引刷新失敗: {str(e)}")

    def __del__(self):
        """析構函數：清理資源"""
        try:
            if hasattr(self, 'elasticsearch_client') and self.elasticsearch_client:
                self.elasticsearch_client.close()
        except:
            pass
    
    def setup_query_engine(self):
        """設置查詢引擎 - 支援 ES 混合檢索 (向量 + 關鍵字)"""
        if self.index:
            # 使用自定義的混合檢索器
            if self.use_elasticsearch and self.elasticsearch_store:
                # 創建混合檢索器 (向量 + 關鍵字)
                retriever = self._create_hybrid_retriever()
                
                from llama_index.core.query_engine import RetrieverQueryEngine
                self.query_engine = RetrieverQueryEngine.from_args(
                    retriever=retriever,
                    response_mode="compact"
                )
                st.success("✅ 使用 ES 混合檢索引擎 (向量搜尋 + 關鍵字搜尋)")
            else:
                # 回退到標準查詢引擎
                self.query_engine = self.index.as_query_engine(
                    similarity_top_k=3,
                    response_mode="compact"
                )
                st.info("✅ 使用標準向量檢索引擎")
    
    def _create_hybrid_retriever(self):
        """創建 ES 混合檢索器 (向量相似度 + BM25 關鍵字)"""
        from llama_index.core.retrievers import BaseRetriever
        from llama_index.core.schema import QueryBundle, NodeWithScore
        from typing import List
        
        class ESHybridRetriever(BaseRetriever):
            def __init__(self, es_client, index_name, embedding_model, top_k=5):
                self.es_client = es_client
                self.index_name = index_name
                self.embedding_model = embedding_model
                self.top_k = top_k
                print(f"🔧 ESHybridRetriever初始化: ES客戶端類型={type(es_client)}")
                print(f"🔧 索引名稱: {index_name}, top_k: {top_k}")
                super().__init__()
            
            def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
                """混合檢索：結合向量搜尋和關鍵字搜尋"""
                query_text = query_bundle.query_str
                print(f"🔍 開始ES混合檢索，查詢: {query_text}")
                print(f"🔧 ES客戶端類型: {type(self.es_client)}")
                
                try:
                    # 1. 獲取查詢的 embedding 向量
                    print("📊 正在獲取查詢向量...")
                    query_embedding = self.embedding_model._get_query_embedding(query_text)
                    print(f"✅ 查詢向量維度: {len(query_embedding) if query_embedding else 'None'}")
                    
                    # 2. ES 混合查詢 (向量 + 關鍵字) - 使用 Elasticsearch 8.x 語法
                    hybrid_query = {
                        "size": self.top_k,
                        "knn": {
                            "field": "embedding",
                            "query_vector": query_embedding,
                            "k": self.top_k,
                            "num_candidates": self.top_k * 2
                        },
                        "query": {
                            "bool": {
                                "should": [
                                    # BM25 關鍵字搜尋 (詞彙搜尋)
                                    {
                                        "match": {
                                            "content": {
                                                "query": query_text,
                                                "boost": 1.2  # 稍微提升關鍵字權重
                                            }
                                        }
                                    },
                                    # 短語匹配
                                    {
                                        "match_phrase": {
                                            "content": {
                                                "query": query_text,
                                                "boost": 1.5
                                            }
                                        }
                                    }
                                ],
                                "minimum_should_match": 1
                            }
                        },
                        "_source": ["content", "metadata"]
                    }
                    
                    # 3. 執行查詢
                    print(f"🔍 執行ES搜尋，索引: {self.index_name}")
                    print(f"🔧 查詢結構: {hybrid_query}")
                    
                    try:
                        response = self.es_client.search(
                            index=self.index_name,
                            body=hybrid_query
                        )
                        print(f"✅ ES查詢成功，響應類型: {type(response)}")
                        
                        # 檢查 response 是否為 awaitable
                        if hasattr(response, '__await__'):
                            print("❌ 錯誤：收到awaitable response，但在同步環境中")
                            raise Exception("同步客戶端返回了awaitable response")
                            
                    except Exception as search_error:
                        print(f"❌ ES搜尋失敗: {str(search_error)}")
                        print(f"🔧 搜尋錯誤類型: {type(search_error)}")
                        raise search_error
                    
                    # 4. 轉換為 NodeWithScore
                    nodes = []
                    hits = response.get('hits', {}).get('hits', [])
                    print(f"📊 找到 {len(hits)} 個匹配結果")
                    
                    for i, hit in enumerate(hits):
                        from llama_index.core.schema import TextNode
                        
                        # 創建文本節點
                        node = TextNode(
                            text=hit['_source']['content'],
                            metadata=hit['_source'].get('metadata', {}),
                            id_=hit['_id']
                        )
                        
                        # ES 評分 (結合向量和關鍵字)
                        score = hit['_score']
                        
                        # 創建評分節點
                        node_with_score = NodeWithScore(
                            node=node,
                            score=score
                        )
                        nodes.append(node_with_score)
                    
                    st.info(f"🔍 ES 混合檢索找到 {len(nodes)} 個相關文檔")
                    return nodes
                    
                except Exception as e:
                    print(f"❌ ES混合檢索失敗，錯誤詳情: {str(e)}")
                    print(f"🔧 錯誤類型: {type(e)}")
                    import traceback
                    print(f"🔍 完整錯誤堆疊: {traceback.format_exc()}")
                    st.error(f"❌ ES 混合檢索失敗: {str(e)}")
                    
                    # 檢查是否為async/await錯誤
                    if "ObjectApiResponse" in str(e) or "await" in str(e) or "coroutine" in str(e):
                        print("🚨 檢測到async/sync客戶端錯誤，ES客戶端可能仍為異步")
                        print(f"🔧 當前ES客戶端類型: {type(self.es_client)}")
                    
                    # 回退到基本向量檢索
                    return self._fallback_vector_search(query_bundle)
            
            def _fallback_vector_search(self, query_bundle):
                """回退到純向量搜尋"""
                try:
                    query_embedding = self.embedding_model._get_query_embedding(query_bundle.query_str)
                    
                    vector_query = {
                        "size": self.top_k,
                        "knn": {
                            "field": "embedding",
                            "query_vector": query_embedding,
                            "k": self.top_k,
                            "num_candidates": self.top_k * 2
                        },
                        "_source": ["content", "metadata"]
                    }
                    
                    response = self.es_client.search(
                        index=self.index_name,
                        body=vector_query
                    )
                    
                    nodes = []
                    for hit in response['hits']['hits']:
                        from llama_index.core.schema import TextNode
                        
                        node = TextNode(
                            text=hit['_source']['content'],
                            metadata=hit['_source'].get('metadata', {}),
                            id_=hit['_id']
                        )
                        
                        node_with_score = NodeWithScore(
                            node=node,
                            score=hit['_score']
                        )
                        nodes.append(node_with_score)
                    
                    st.warning("⚠️ 回退到純向量搜尋")
                    return nodes
                    
                except Exception as e:
                    st.error(f"❌ 向量搜尋也失敗: {str(e)}")
                    return []
        
        # 創建並返回混合檢索器 - 使用統一同步客戶端
        if not hasattr(self, 'elasticsearch_client') or not self.elasticsearch_client:
            st.error("❌ ES客戶端未初始化，無法創建查詢引擎")
            return None
            
        print(f"🔧 創建ESHybridRetriever，使用客戶端類型: {type(self.elasticsearch_client)}")
            
        return ESHybridRetriever(
            es_client=self.elasticsearch_client,  # 統一使用同步客戶端
            index_name=self.index_name,
            embedding_model=self.embedding_model,
            top_k=10  # Change the top_k value from 5 to 10
        )
    
    def _recreate_sync_elasticsearch_client(self) -> bool:
        """完全重新創建同步ES客戶端，解決async/await問題"""
        try:
            print("🔧 開始重新創建同步ES客戶端...")
            
            # 強制使用最基礎的同步配置
            from elasticsearch import Elasticsearch
            
            config = self.elasticsearch_config
            basic_config = {
                'hosts': [f"{config['scheme']}://{config['host']}:{config['port']}"],
                'request_timeout': 60,
                'max_retries': 1,
                'retry_on_timeout': False
            }
            
            if config.get('username') and config.get('password'):
                basic_config['basic_auth'] = (config['username'], config['password'])
            
            # 創建新的同步客戶端
            new_sync_client = Elasticsearch(**basic_config)
            
            # 測試連接
            if new_sync_client.ping():
                print("✅ 新同步客戶端連接成功")
                # 更新同步客戶端引用（不要覆蓋異步客戶端）
                self.sync_elasticsearch_client = new_sync_client
                
                # 重新創建向量存儲 - 使用同步客戶端
                self.elasticsearch_store = ElasticsearchStore(
                    es_client=self.sync_elasticsearch_client,
                    index_name=self.index_name,
                    vector_field=self.elasticsearch_config['vector_field'],
                    text_field=self.elasticsearch_config['text_field'],
                    metadata_field='metadata',
                    embedding_dim=self.elasticsearch_config.get('dimension', 1024)
                )
                print("✅ 向量存儲重新創建成功（使用同步客戶端）")
                return True
            else:
                print("❌ 新同步客戶端連接失敗")
                return False
                
        except Exception as e:
            print(f"❌ 重新創建同步客戶端失敗: {str(e)}")
            return False
    
    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """覆寫父類方法，強制使用 Elasticsearch"""
        if not documents:
            st.warning("⚠️ 沒有文檔需要索引")
            return None
        
        with st.spinner("正在使用 Elasticsearch 建立索引..."):
            try:
                # 確保 ES 連接和模型已初始化
                if not self.elasticsearch_client:
                    st.error("❌ Elasticsearch 客戶端未初始化，嘗試重新初始化...")
                    if not self._setup_elasticsearch_client():
                        return None
                
                if not self.elasticsearch_store:
                    st.error("❌ Elasticsearch 向量存儲未設置，嘗試重新設置...")
                    if not self._create_elasticsearch_index():
                        return None
                    if not self._setup_elasticsearch_store():
                        return None
                    
                self._ensure_models_initialized()
                
                # 建立 storage context
                storage_context = StorageContext.from_defaults(
                    vector_store=self.elasticsearch_store
                )
                
                st.info(f"📊 準備向量化 {len(documents)} 個文檔到 {self.index_name}")
                
                # 檢查文檔內容
                for i, doc in enumerate(documents[:3]):
                    content_preview = doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
                    print(f"📄 文檔 {i+1}: {len(doc.text)} 字符")
                    print(f"   內容預覽: {content_preview}")
                    if hasattr(doc, 'metadata') and doc.metadata:
                        print(f"   元數據: {doc.metadata}")
                
                # 創建索引 - 加入詳細日誌
                print(f"🔧 開始創建VectorStoreIndex，使用ES存儲: {type(self.elasticsearch_store)}")
                print(f"🔧 ES客戶端類型: {type(self.elasticsearch_client)}")
                print(f"🔧 嵌入模型類型: {type(self.embedding_model)}")
                
                try:
                    index = VectorStoreIndex.from_documents(
                        documents, 
                        storage_context=storage_context,
                        embed_model=self.embedding_model
                    )
                    print("✅ VectorStoreIndex.from_documents 執行成功")
                except Exception as index_error:
                    print(f"❌ VectorStoreIndex.from_documents 失敗: {str(index_error)}")
                    print(f"❌ 錯誤類型: {type(index_error)}")
                    import traceback
                    print(f"❌ 完整錯誤堆疊: {traceback.format_exc()}")
                    
                    # 如果是 HeadApiResponse 錯誤，嘗試替代方案
                    if "HeadApiResponse" in str(index_error) or "await" in str(index_error):
                        print("🔄 檢測到HeadApiResponse錯誤，嘗試重新初始化ES客戶端...")
                        
                        # 完全重新創建 ES 客戶端和存儲
                        if self._recreate_sync_elasticsearch_client():
                            print("🔄 重新創建storage_context...")
                            storage_context = StorageContext.from_defaults(
                                vector_store=self.elasticsearch_store
                            )
                            
                            print("🔄 重新嘗試創建索引...")
                            index = VectorStoreIndex.from_documents(
                                documents, 
                                storage_context=storage_context,
                                embed_model=self.embedding_model
                            )
                            print("✅ 使用重新創建的客戶端成功創建索引")
                        else:
                            raise index_error
                    else:
                        raise index_error
                
                # 強制刷新並驗證（使用同步客戶端）
                sync_client = getattr(self, 'sync_elasticsearch_client', None)
                if sync_client:
                    sync_client.indices.refresh(index=self.index_name)
                    stats = sync_client.indices.stats(index=self.index_name)
                    doc_count = stats['indices'][self.index_name]['total']['docs']['count']
                else:
                    doc_count = 0
                
                print(f"✅ ES索引驗證: {doc_count} 個文檔已成功索引到 {self.index_name}")
                st.success(f"✅ 成功索引 {doc_count} 個文檔到 Elasticsearch")
                
                # 更新統計
                self.memory_stats['documents_processed'] = len(documents)
                self.memory_stats['vectors_stored'] = doc_count
                
                return index
                
            except Exception as e:
                st.error(f"❌ Elasticsearch 索引建立失敗: {str(e)}")
                print(f"❌ 詳細錯誤: {traceback.format_exc()}")
                return None