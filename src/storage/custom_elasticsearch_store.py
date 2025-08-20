"""
自定義 Elasticsearch 向量存儲實現
避免 LlamaIndex Elasticsearch 整合中的 async/await 問題
"""

from typing import List, Dict, Any, Optional, Union
from llama_index.core.vector_stores.types import (
    VectorStore,
    VectorStoreQuery,
    VectorStoreQueryResult,
)
from llama_index.core.schema import BaseNode, TextNode
from elasticsearch import Elasticsearch
import json
import numpy as np
from datetime import datetime

class CustomElasticsearchStore(VectorStore):
    """自定義 Elasticsearch 向量存儲實現"""
    
    def __init__(
        self,
        es_client: Elasticsearch,
        index_name: str = "vector_index",
        text_field: str = "content",
        vector_field: str = "embedding",
        metadata_field: str = "metadata"
    ):
        """初始化自定義 Elasticsearch 向量存儲"""
        super().__init__()
        self.es_client = es_client
        self.index_name = index_name
        self.text_field = text_field
        self.vector_field = vector_field
        self.metadata_field = metadata_field
        
    @property
    def stores_text(self) -> bool:
        return True
    
    def add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """添加節點到 Elasticsearch"""
        ids = []
        
        for node in nodes:
            # 生成唯一 ID
            node_id = node.node_id if hasattr(node, 'node_id') and node.node_id else f"node_{datetime.now().timestamp()}"
            
            # 準備文檔
            doc = {
                self.text_field: node.text if hasattr(node, 'text') else str(node),
                self.metadata_field: node.metadata if hasattr(node, 'metadata') else {}
            }
            
            # 添加嵌入向量（如果有）
            if hasattr(node, 'embedding') and node.embedding is not None:
                doc[self.vector_field] = node.embedding
            
            # 索引文檔
            try:
                response = self.es_client.index(
                    index=self.index_name,
                    id=node_id,
                    body=doc,
                    refresh=True  # 立即刷新以便搜索
                )
                ids.append(node_id)
            except Exception as e:
                print(f"❌ 文檔索引失敗: {e}")
                
        return ids
    
    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """刪除文檔"""
        try:
            self.es_client.delete(
                index=self.index_name,
                id=ref_doc_id,
                refresh=True
            )
        except Exception as e:
            print(f"❌ 文檔刪除失敗: {e}")
    
    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """執行向量搜索查詢"""
        
        if query.query_embedding is None:
            # 如果沒有查詢嵌入，進行文本搜索
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query.query_str if query.query_str else "",
                        "fields": [self.text_field],
                        "type": "best_fields"
                    }
                },
                "size": query.similarity_top_k or 10
            }
        else:
            # 向量相似性搜索 - Elasticsearch 8.x KNN 語法
            search_body = {
                "knn": {
                    "field": self.vector_field,
                    "query_vector": query.query_embedding,
                    "k": query.similarity_top_k or 10,
                    "num_candidates": (query.similarity_top_k or 10) * 2
                },
                "_source": [self.text_field, self.metadata_field],
                "size": query.similarity_top_k or 10
            }
        
        # 執行搜索
        try:
            response = self.es_client.search(
                index=self.index_name,
                body=search_body
            )
            
            # 處理結果
            nodes = []
            similarities = []
            ids = []
            
            hits = response.get('hits', {}).get('hits', [])
            
            for hit in hits:
                # 創建節點
                node = TextNode(
                    text=hit['_source'].get(self.text_field, ''),
                    metadata=hit['_source'].get(self.metadata_field, {}),
                    node_id=hit['_id']
                )
                nodes.append(node)
                ids.append(hit['_id'])
                
                # 計算相似性分數
                score = hit.get('_score', 0.0)
                similarities.append(score)
            
            return VectorStoreQueryResult(
                nodes=nodes,
                similarities=similarities,
                ids=ids
            )
            
        except Exception as e:
            print(f"❌ 搜索查詢失敗: {e}")
            return VectorStoreQueryResult(nodes=[], similarities=[], ids=[])
    
    def get_nodes(self, node_ids: Optional[List[str]] = None, **kwargs: Any) -> List[BaseNode]:
        """獲取節點"""
        if not node_ids:
            return []
        
        nodes = []
        for node_id in node_ids:
            try:
                response = self.es_client.get(
                    index=self.index_name,
                    id=node_id
                )
                
                source = response['_source']
                node = TextNode(
                    text=source.get(self.text_field, ''),
                    metadata=source.get(self.metadata_field, {}),
                    node_id=node_id
                )
                nodes.append(node)
                
            except Exception as e:
                print(f"❌ 獲取節點失敗 {node_id}: {e}")
                
        return nodes
    
    def clear(self) -> None:
        """清空索引"""
        try:
            self.es_client.delete_by_query(
                index=self.index_name,
                body={"query": {"match_all": {}}},
                refresh=True
            )
        except Exception as e:
            print(f"❌ 清空索引失敗: {e}")
    
    def persist(self, persist_path: str, **kwargs: Any) -> None:
        """持久化（Elasticsearch 已經自動持久化）"""
        pass