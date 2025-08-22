"""
對話記錄管理 - Elasticsearch 存儲
負責處理智能問答的對話記錄存儲和檢索
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st
import traceback

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

class ConversationHistoryManager:
    """對話記錄管理器"""
    
    def __init__(self, elasticsearch_config: Optional[Dict] = None):
        self.elasticsearch_config = self._normalize_config(elasticsearch_config or self._get_default_config())
        self.index_name = "rag_conversation_history"
        self.elasticsearch_client = None
        self._initialize_client()
    
    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """將配置標準化為 Elasticsearch 客戶端所需的格式"""
        # 如果配置已經是正確格式（有 hosts 字段），直接返回
        if 'hosts' in config:
            return config
        
        # 否則從單獨的 host, port 參數構建 hosts 格式
        if 'host' in config and 'port' in config:
            normalized = {
                'hosts': [{
                    'host': config['host'],
                    'port': config['port'],
                    'scheme': config.get('scheme', 'http')
                }],
                'request_timeout': config.get('timeout', 30),
                'max_retries': config.get('max_retries', 3),
                'retry_on_timeout': True
            }
            
            # 添加認證信息（如果有）
            if config.get('username') and config.get('password'):
                normalized['basic_auth'] = (config['username'], config['password'])
                
            return normalized
        
        # 如果都沒有，返回默認配置
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認的 Elasticsearch 配置"""
        return {
            'hosts': [os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')],
            'timeout': 30,
            'max_retries': 3,
            'retry_on_timeout': True
        }
    
    def _initialize_client(self) -> bool:
        """初始化 Elasticsearch 客戶端"""
        if not ELASTICSEARCH_AVAILABLE:
            st.error("❌ Elasticsearch 模組未安裝")
            return False
        
        try:
            self.elasticsearch_client = Elasticsearch(**self.elasticsearch_config)
            
            # 測試連接
            if self.elasticsearch_client.ping():
                print(f"✅ 對話記錄 ES 客戶端連接成功")
                self._ensure_index_exists()
                return True
            else:
                st.error("❌ 無法連接到 Elasticsearch 服務")
                return False
                
        except Exception as e:
            st.error(f"❌ Elasticsearch 客戶端初始化失敗: {str(e)}")
            traceback.print_exc()
            return False
    
    def _ensure_index_exists(self):
        """確保對話記錄索引存在"""
        try:
            if not self.elasticsearch_client.indices.exists(index=self.index_name):
                # 創建索引映射
                mapping = {
                    "mappings": {
                        "properties": {
                            "conversation_id": {"type": "keyword"},
                            "session_id": {"type": "keyword"},
                            "user_id": {"type": "keyword"},
                            "question": {"type": "text", "analyzer": "standard"},
                            "answer": {"type": "text", "analyzer": "standard"},
                            "sources": {
                                "type": "nested",
                                "properties": {
                                    "source": {"type": "keyword"},
                                    "file_path": {"type": "keyword"},
                                    "score": {"type": "float"},
                                    "content": {"type": "text"},
                                    "page": {"type": "keyword"},
                                    "type": {"type": "keyword"}
                                }
                            },
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "text"},
                                    "total_sources": {"type": "integer"},
                                    "response_time_ms": {"type": "integer"},
                                    "model": {"type": "keyword"},
                                    "backend": {"type": "keyword"}
                                }
                            },
                            "timestamp": {"type": "date"},
                            "created_at": {"type": "date"},
                            "rating": {"type": "integer"},  # 用戶評分 1-5
                            "feedback": {"type": "text"},   # 用戶反饋
                            "tags": {"type": "keyword"}     # 標籤
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "standard": {
                                    "type": "standard"
                                }
                            }
                        }
                    }
                }
                
                self.elasticsearch_client.indices.create(
                    index=self.index_name,
                    body=mapping
                )
                print(f"✅ 創建對話記錄索引: {self.index_name}")
            
        except Exception as e:
            st.error(f"❌ 創建對話記錄索引失敗: {str(e)}")
    
    def save_conversation(self, 
                         question: str, 
                         answer: str, 
                         sources: List[Dict[str, Any]] = None,
                         metadata: Dict[str, Any] = None,
                         session_id: str = None,
                         user_id: str = None) -> str:
        """保存對話記錄"""
        if not self.elasticsearch_client:
            return None
        
        try:
            conversation_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            conversation_record = {
                "conversation_id": conversation_id,
                "session_id": session_id or "default",
                "user_id": user_id or "anonymous",
                "question": question,
                "answer": answer,
                "sources": sources or [],
                "metadata": metadata or {},
                "timestamp": timestamp.isoformat(),
                "created_at": timestamp.isoformat(),
                "rating": None,
                "feedback": None,
                "tags": []
            }
            
            # 保存到 Elasticsearch
            response = self.elasticsearch_client.index(
                index=self.index_name,
                id=conversation_id,
                body=conversation_record
            )
            
            print(f"✅ 對話記錄已保存: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            st.error(f"❌ 保存對話記錄失敗: {str(e)}")
            return None
    
    def get_conversation_history(self, 
                               session_id: str = None,
                               user_id: str = None,
                               limit: int = 50,
                               start_date: datetime = None,
                               end_date: datetime = None) -> List[Dict[str, Any]]:
        """獲取對話記錄"""
        if not self.elasticsearch_client:
            return []
        
        try:
            # 構建查詢
            query = {"bool": {"must": []}}
            
            if session_id:
                query["bool"]["must"].append({"term": {"session_id": session_id}})
            
            if user_id:
                query["bool"]["must"].append({"term": {"user_id": user_id}})
            
            if start_date or end_date:
                date_range = {}
                if start_date:
                    date_range["gte"] = start_date.isoformat()
                if end_date:
                    date_range["lte"] = end_date.isoformat()
                query["bool"]["must"].append({"range": {"timestamp": date_range}})
            
            # 如果沒有條件，獲取所有記錄
            if not query["bool"]["must"]:
                query = {"match_all": {}}
            
            search_body = {
                "query": query,
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": limit
            }
            
            response = self.elasticsearch_client.search(
                index=self.index_name,
                body=search_body
            )
            
            conversations = []
            for hit in response.get('hits', {}).get('hits', []):
                conversation = hit['_source']
                conversation['id'] = hit['_id']
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            st.error(f"❌ 獲取對話記錄失敗: {str(e)}")
            return []
    
    def update_conversation_feedback(self, 
                                   conversation_id: str, 
                                   rating: int = None, 
                                   feedback: str = None,
                                   tags: List[str] = None) -> bool:
        """更新對話反饋"""
        if not self.elasticsearch_client:
            return False
        
        try:
            update_doc = {}
            
            if rating is not None:
                update_doc["rating"] = rating
            
            if feedback is not None:
                update_doc["feedback"] = feedback
            
            if tags is not None:
                update_doc["tags"] = tags
            
            if update_doc:
                response = self.elasticsearch_client.update(
                    index=self.index_name,
                    id=conversation_id,
                    body={"doc": update_doc}
                )
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ 更新對話反饋失敗: {str(e)}")
            return False
    
    def search_conversations(self, 
                           query_text: str, 
                           limit: int = 20) -> List[Dict[str, Any]]:
        """搜索對話記錄"""
        if not self.elasticsearch_client:
            return []
        
        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["question^2", "answer", "sources.content"],
                        "type": "best_fields"
                    }
                },
                "highlight": {
                    "fields": {
                        "question": {},
                        "answer": {},
                        "sources.content": {}
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": limit
            }
            
            response = self.elasticsearch_client.search(
                index=self.index_name,
                body=search_body
            )
            
            conversations = []
            for hit in response.get('hits', {}).get('hits', []):
                conversation = hit['_source']
                conversation['id'] = hit['_id']
                conversation['highlight'] = hit.get('highlight', {})
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            st.error(f"❌ 搜索對話記錄失敗: {str(e)}")
            return []
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """獲取對話統計信息"""
        if not self.elasticsearch_client:
            return {}
        
        try:
            # 總對話數
            total_response = self.elasticsearch_client.count(index=self.index_name)
            total_conversations = total_response.get('count', 0)
            
            # 聚合統計
            agg_body = {
                "size": 0,
                "aggs": {
                    "conversations_by_date": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "day",
                            "order": {"_key": "desc"}
                        }
                    },
                    "avg_rating": {
                        "avg": {
                            "field": "rating"
                        }
                    },
                    "popular_tags": {
                        "terms": {
                            "field": "tags",
                            "size": 10
                        }
                    },
                    "sessions_count": {
                        "cardinality": {
                            "field": "session_id"
                        }
                    }
                }
            }
            
            response = self.elasticsearch_client.search(
                index=self.index_name,
                body=agg_body
            )
            
            aggs = response.get('aggregations', {})
            
            return {
                'total_conversations': total_conversations,
                'unique_sessions': aggs.get('sessions_count', {}).get('value', 0),
                'average_rating': round(aggs.get('avg_rating', {}).get('value', 0) or 0, 2),
                'conversations_by_date': aggs.get('conversations_by_date', {}).get('buckets', []),
                'popular_tags': aggs.get('popular_tags', {}).get('buckets', [])
            }
            
        except Exception as e:
            st.error(f"❌ 獲取對話統計失敗: {str(e)}")
            return {}
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """刪除對話記錄"""
        if not self.elasticsearch_client:
            return False
        
        try:
            response = self.elasticsearch_client.delete(
                index=self.index_name,
                id=conversation_id
            )
            return True
            
        except Exception as e:
            st.error(f"❌ 刪除對話記錄失敗: {str(e)}")
            return False
    
    def clear_all_conversations(self, confirm: bool = False) -> bool:
        """清空所有對話記錄"""
        if not self.elasticsearch_client or not confirm:
            return False
        
        try:
            response = self.elasticsearch_client.delete_by_query(
                index=self.index_name,
                body={"query": {"match_all": {}}}
            )
            
            deleted_count = response.get('deleted', 0)
            st.success(f"✅ 已刪除 {deleted_count} 條對話記錄")
            return True
            
        except Exception as e:
            st.error(f"❌ 清空對話記錄失敗: {str(e)}")
            return False