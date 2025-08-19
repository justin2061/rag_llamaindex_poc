import os
import json
from typing import List, Dict, Any, Optional
import streamlit as st
from datetime import datetime

# LlamaIndex 核心
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# Elasticsearch integration
try:
    from elasticsearch import Elasticsearch
    from llama_index.vector_stores.elasticsearch import ElasticsearchStore
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    st.warning("⚠️ Elasticsearch dependencies not installed. Install with: pip install elasticsearch llama-index-vector-stores-elasticsearch")

# 繼承增強版系統
from enhanced_rag_system import EnhancedRAGSystem
from config import (
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
        super().__init__(use_elasticsearch=False, use_chroma=False)  # ES RAG系統自己管理Elasticsearch
        
        self.elasticsearch_config = elasticsearch_config or self._get_default_config()
        self.elasticsearch_client = None
        self.elasticsearch_store = None
        self.index_name = self.elasticsearch_config.get('index_name', 'rag_documents')
        
        # 記憶體使用監控
        self.memory_stats = {
            'documents_processed': 0,
            'vectors_stored': 0,
            'peak_memory_mb': 0
        }
        
        # 模型實例
        self.embedding_model = None
        self.llm_model = None
    
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
        """設置 Elasticsearch 客戶端"""
        if not ELASTICSEARCH_AVAILABLE:
            st.error("❌ Elasticsearch 依賴未安裝")
            return False
        
        try:
            config = self.elasticsearch_config
            
            # 連接配置
            es_config = {
                'hosts': [f"{config['scheme']}://{config['host']}:{config['port']}"],
                'timeout': config['timeout'],
                'max_retries': config['max_retries'],
                'retry_on_timeout': True,
                'verify_certs': config['verify_certs']
            }
            
            # 認證配置
            if config.get('username') and config.get('password'):
                es_config['basic_auth'] = (config['username'], config['password'])
            
            self.elasticsearch_client = Elasticsearch(**es_config)
            
            # 測試連接
            if self.elasticsearch_client.ping():
                st.success(f"✅ 成功連接到 Elasticsearch: {config['host']}:{config['port']}")
                return True
            else:
                st.error(f"❌ 無法連接到 Elasticsearch: {config['host']}:{config['port']}")
                return False
                
        except Exception as e:
            st.error(f"❌ Elasticsearch 連接失敗: {str(e)}")
            return False
    
    def _create_elasticsearch_index(self) -> bool:
        """創建 Elasticsearch 索引"""
        try:
            config = self.elasticsearch_config
            
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
            
            # 檢查索引是否存在
            if self.elasticsearch_client.indices.exists(index=self.index_name):
                st.info(f"📚 索引 '{self.index_name}' 已存在")
                return True
            
            # 創建索引 - 修復 async/await 兼容性問題
            try:
                response = self.elasticsearch_client.indices.create(
                    index=self.index_name,
                    body=index_mapping,
                    ignore=400  # 忽略已存在的錯誤
                )
                
                if response.get('acknowledged', False):
                    st.success(f"✅ 成功創建索引: {self.index_name}")
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
            st.error(f"❌ 創建索引過程出現異常: {str(e)}")
            return False
    
    def _setup_elasticsearch_store(self) -> bool:
        """設置 Elasticsearch 向量存儲"""
        try:
            # 確保使用正確的同步客戶端
            if not hasattr(self, 'elasticsearch_client') or not self.elasticsearch_client:
                st.error("❌ Elasticsearch 客戶端未初始化")
                return False
            
            self.elasticsearch_store = ElasticsearchStore(
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
    
    def create_index(self, documents: List[Document]):
        """創建 Elasticsearch 索引"""
        with st.spinner("正在建立 Elasticsearch 索引..."):
            try:
                # 1. 確保所有基礎設定都已就緒
                if not all([
                    self._setup_elasticsearch_client(),
                    self._create_elasticsearch_index(),
                    self._setup_elasticsearch_store()
                ]):
                    st.error("❌ Elasticsearch 基礎設定失敗，無法建立索引。")
                    return None

                # 2. 確保模型已初始化
                self._ensure_models_initialized()

                # 3. 確保所有文件都有唯一的 ID 和時間戳
                import uuid
                for doc in documents:
                    if not hasattr(doc, 'id_') or not doc.id_:
                        doc.id_ = str(uuid.uuid4())
                    if 'timestamp' not in doc.metadata:
                        doc.metadata['timestamp'] = datetime.now().isoformat()

                # 4. 建立存儲上下文
                storage_context = StorageContext.from_defaults(vector_store=self.elasticsearch_store)

                # 5. 使用 LlamaIndex 的標準方法建立索引
                try:
                    self.index = VectorStoreIndex.from_documents(
                        documents,
                        storage_context=storage_context,
                        embed_model=self.embedding_model,
                        show_progress=True
                    )

                    if self.index:
                        st.success(f"✅ Elasticsearch 索引建立完成！處理了 {len(documents)} 個文檔。")
                        
                        # 驗證文檔是否真的被插入
                        try:
                            stats = self.elasticsearch_client.indices.stats(index=self.index_name)
                            doc_count = stats['indices'][self.index_name]['total']['docs']['count']
                            st.info(f"📊 Elasticsearch 實際文檔數: {doc_count}")
                            
                            if doc_count == 0:
                                st.warning("⚠️ 索引創建成功但文檔數為0，可能存在插入問題")
                        except Exception as stat_e:
                            st.warning(f"無法獲取索引統計: {stat_e}")
                        
                        return self.index
                    else:
                        st.error("❌ 索引對象為 None")
                        return None
                        
                except Exception as index_e:
                    st.error(f"❌ 索引創建過程失敗: {str(index_e)}")
                    import traceback
                    st.error(f"索引創建詳細錯誤: {traceback.format_exc()}")
                    return None

            except Exception as e:
                st.error(f"❌ Elasticsearch 索引建立失敗: {str(e)}")
                import traceback
                st.error(f"詳細錯誤: {traceback.format_exc()}")
                return None
    
    def setup_query_engine(self):
        """設置 Elasticsearch 查詢引擎"""
        if self.index is None:
            st.warning("請先建立索引")
            return
        
        try:
            # 創建檢索器
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=10,  # 增加檢索數量
                vector_store_query_mode="default"
            )
            
            # 創建後處理器
            postprocessor = SimilarityPostprocessor(
                similarity_cutoff=0.7  # 相似度過濾
            )
            
            # 創建查詢引擎
            self.query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever,
                node_postprocessors=[postprocessor],
                response_mode="compact",  # 緊湊模式節省記憶體
                streaming=False
            )
            
            st.success("✅ Elasticsearch 查詢引擎設置完成")
            
        except Exception as e:
            st.error(f"❌ 查詢引擎設置失敗: {str(e)}")
    
    def get_elasticsearch_statistics(self) -> Dict[str, Any]:
        """獲取 Elasticsearch 統計資訊"""
        stats = super().get_enhanced_statistics()
        
        if self.elasticsearch_client:
            try:
                # 索引統計
                index_stats = self.elasticsearch_client.indices.stats(
                    index=self.index_name
                )
                
                # 集群健康狀態
                cluster_health = self.elasticsearch_client.cluster.health()
                
                # 搜索統計
                search_stats = index_stats.get('indices', {}).get(self.index_name, {})
                
                elasticsearch_stats = {
                    'cluster_status': cluster_health.get('status', 'unknown'),
                    'total_documents': search_stats.get('total', {}).get('docs', {}).get('count', 0),
                    'index_size_bytes': search_stats.get('total', {}).get('store', {}).get('size_in_bytes', 0),
                    'search_queries': search_stats.get('total', {}).get('search', {}).get('query_total', 0),
                    'memory_stats': self.memory_stats,
                    'index_name': self.index_name,
                    'elasticsearch_config': self.elasticsearch_config
                }
                
                stats['elasticsearch_stats'] = elasticsearch_stats
                
            except Exception as e:
                st.warning(f"無法獲取 Elasticsearch 統計: {str(e)}")
        
        return stats
    
    def search_documents(self, query: str, size: int = 10) -> List[Dict]:
        """直接搜索 Elasticsearch 文檔"""
        if not self.elasticsearch_client:
            return []
        
        try:
            # 混合搜索：向量搜索 + 文本搜索
            search_query = {
                "size": size,
                "query": {
                    "bool": {
                        "should": [
                            # 文本搜索
                            {
                                "match": {
                                    self.elasticsearch_config['text_field']: {
                                        "query": query,
                                        "analyzer": "chinese_analyzer",
                                        "boost": 1.0
                                    }
                                }
                            },
                            # 短語搜索
                            {
                                "match_phrase": {
                                    self.elasticsearch_config['text_field']: {
                                        "query": query,
                                        "boost": 1.5
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "highlight": {
                    "fields": {
                        self.elasticsearch_config['text_field']: {}
                    }
                },
                "_source": ["*"]
            }
            
            response = self.elasticsearch_client.search(
                index=self.index_name,
                body=search_query
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'score': hit['_score'],
                    'content': hit['_source'].get(self.elasticsearch_config['text_field'], ''),
                    'metadata': hit['_source'].get('metadata', {}),
                    'highlights': hit.get('highlight', {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            st.error(f"搜索失敗: {str(e)}")
            return []
    
    def cleanup_memory(self):
        """清理記憶體"""
        try:
            import gc
            import psutil
            import os
            
            # 獲取當前記憶體使用量
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # 清理操作
            gc.collect()
            
            # 記錄峰值記憶體
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            self.memory_stats['peak_memory_mb'] = max(
                self.memory_stats['peak_memory_mb'], 
                memory_before
            )
            
            st.info(f"🧹 記憶體清理：{memory_before:.1f}MB → {memory_after:.1f}MB")
            
        except Exception as e:
            st.warning(f"記憶體清理失敗: {str(e)}")
    
    def load_existing_index(self) -> bool:
        """載入現有的 Elasticsearch 索引"""
        try:
            # 設置 Elasticsearch 客戶端
            if not self._setup_elasticsearch_client():
                st.error("❌ 無法連接到 Elasticsearch")
                return False
            
            # 檢查索引是否存在
            if self.elasticsearch_client.indices.exists(index=self.index_name):
                # 獲取索引統計資訊
                stats = self.elasticsearch_client.indices.stats(index=self.index_name)
                doc_count = stats['indices'][self.index_name]['total']['docs']['count']
                
                if doc_count > 0:
                    st.success(f"✅ 發現現有的 Elasticsearch 索引：{self.index_name} ({doc_count} 文檔)")
                    
                    # 設置向量存儲
                    if self._setup_elasticsearch_store():
                        # 重新創建索引對象
                        from llama_index.core import VectorStoreIndex
                        from llama_index.core.storage.storage_context import StorageContext
                        
                        self._ensure_models_initialized()
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
            
            if self.elasticsearch_client and self.index_name:
                try:
                    # 獲取索引統計
                    index_stats = self.elasticsearch_client.indices.stats(index=self.index_name)
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
                    
                except Exception as e:
                    st.warning(f"無法獲取 Elasticsearch 統計: {e}")
                    
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
    
    def delete_documents_by_source(self, source_filename: str) -> bool:
        """根據來源文件名刪除文檔"""
        if not self.elasticsearch_client:
            st.error("❌ Elasticsearch 客戶端未初始化")
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
            
            # 刪除匹配的文檔
            response = self.elasticsearch_client.delete_by_query(
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
    
    def refresh_index_after_deletion(self):
        """刪除文檔後刷新索引"""
        try:
            if self.elasticsearch_client:
                self.elasticsearch_client.indices.refresh(index=self.index_name)
                st.info("🔄 Elasticsearch 索引已刷新")
        except Exception as e:
            st.warning(f"索引刷新警告: {str(e)}")

    def __del__(self):
        """析構函數：清理資源"""
        try:
            if hasattr(self, 'elasticsearch_client') and self.elasticsearch_client:
                self.elasticsearch_client.close()
        except:
            pass