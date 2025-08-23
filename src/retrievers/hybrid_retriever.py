"""
Hybrid Retriever System
混合檢索系統，結合向量搜索、關鍵字搜索和語義搜索
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from elasticsearch import Elasticsearch
import numpy as np
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.retrievers import BaseRetriever
from llama_index.core import Settings

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索結果"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]
    search_type: str  # vector, keyword, semantic, structural
    
@dataclass 
class HybridSearchConfig:
    """混合搜索配置"""
    vector_weight: float = 0.6
    keyword_weight: float = 0.3
    semantic_weight: float = 0.1
    structural_weight: float = 0.0
    top_k: int = 10
    rerank_top_k: int = 20

class QueryRewriter:
    """查詢改寫器"""
    
    def __init__(self, llm_model=None):
        self.llm_model = llm_model or Settings.llm
    
    def rewrite_query(self, original_query: str, conversation_history: List[str] = None) -> List[str]:
        """
        查詢改寫，生成多個變體查詢
        """
        rewritten_queries = [original_query]
        
        try:
            # 1. 同義詞擴展
            synonym_query = self._expand_synonyms(original_query)
            if synonym_query != original_query:
                rewritten_queries.append(synonym_query)
            
            # 2. 實體提取查詢
            entity_query = self._extract_key_entities(original_query)
            if entity_query:
                rewritten_queries.append(entity_query)
            
            # 3. 上下文相關查詢（如果有對話歷史）
            if conversation_history:
                context_query = self._generate_contextual_query(original_query, conversation_history)
                if context_query:
                    rewritten_queries.append(context_query)
            
            # 4. 語義相關問題
            related_queries = self._generate_related_queries(original_query)
            rewritten_queries.extend(related_queries)
            
            logger.info(f"🔄 查詢改寫完成，原始查詢: {original_query}")
            logger.info(f"   生成 {len(rewritten_queries)} 個變體查詢")
            
        except Exception as e:
            logger.warning(f"⚠️ 查詢改寫失敗: {e}")
        
        return list(set(rewritten_queries))  # 去重
    
    def _expand_synonyms(self, query: str) -> str:
        """同義詞擴展"""
        synonym_map = {
            "機器學習": ["ML", "machine learning", "人工智慧學習"],
            "人工智能": ["AI", "artificial intelligence", "人工智慧"],
            "深度學習": ["DL", "deep learning", "神經網路學習"],
            "演算法": ["algorithm", "算法", "運算法"],
            "資料": ["數據", "data", "數據資料"],
            "模型": ["model", "模型系統", "演算模型"]
        }
        
        expanded_query = query
        for term, synonyms in synonym_map.items():
            if term in query:
                expanded_query += " " + " ".join(synonyms[:2])  # 只取前2個同義詞
        
        return expanded_query
    
    def _extract_key_entities(self, query: str) -> str:
        """提取關鍵實體"""
        # 簡化版實體提取，實際應用中可用NER模型
        entities = []
        
        # 檢測技術術語
        tech_terms = ["機器學習", "深度學習", "人工智能", "演算法", "模型", "訓練", "預測"]
        for term in tech_terms:
            if term in query:
                entities.append(term)
        
        # 檢測數字和時間
        import re
        numbers = re.findall(r'\d+', query)
        entities.extend(numbers)
        
        return " ".join(entities) if entities else ""
    
    def _generate_contextual_query(self, query: str, history: List[str]) -> str:
        """基於對話歷史生成上下文查詢"""
        if not history:
            return ""
        
        # 簡化版：將最近的對話內容加入查詢
        recent_context = " ".join(history[-2:])  # 取最近2輪對話
        return f"{query} {recent_context}"
    
    def _generate_related_queries(self, query: str) -> List[str]:
        """生成相關查詢"""
        related = []
        
        # 基於查詢內容生成相關問題
        if "什麼是" in query or "是什麼" in query:
            # 如果問的是定義，可能還想知道應用
            topic = query.replace("什麼是", "").replace("是什麼", "").strip()
            related.append(f"{topic}的應用")
            related.append(f"如何使用{topic}")
        
        if "如何" in query or "怎麼" in query:
            # 如果問的是方法，可能還想知道原理
            topic = query.replace("如何", "").replace("怎麼", "").strip()
            related.append(f"{topic}的原理")
            related.append(f"{topic}的優缺點")
        
        return related[:2]  # 限制數量

class HybridRetriever(BaseRetriever):
    """混合檢索器"""
    
    def __init__(
        self, 
        elasticsearch_client: Elasticsearch,
        index_name: str,
        config: HybridSearchConfig = None,
        embedding_model = None
    ):
        super().__init__()
        self.es_client = elasticsearch_client
        self.index_name = index_name
        self.config = config or HybridSearchConfig()
        self.embedding_model = embedding_model or Settings.embed_model
        self.query_rewriter = QueryRewriter()
        
        logger.info(f"🔧 HybridRetriever 初始化完成")
        logger.info(f"   - 索引名稱: {index_name}")
        logger.info(f"   - 向量權重: {self.config.vector_weight}")
        logger.info(f"   - 關鍵字權重: {self.config.keyword_weight}")
        logger.info(f"   - 語義權重: {self.config.semantic_weight}")
    
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """執行混合檢索"""
        query = query_bundle.query_str
        
        logger.info(f"🔍 開始混合檢索: {query}")
        
        # 1. 查詢改寫
        rewritten_queries = self.query_rewriter.rewrite_query(query)
        
        # 2. 多種檢索策略
        all_results = []
        
        for search_query in rewritten_queries:
            # 向量搜索
            vector_results = self._vector_search(search_query)
            all_results.extend([(r, "vector") for r in vector_results])
            
            # 關鍵字搜索 
            keyword_results = self._keyword_search(search_query)
            all_results.extend([(r, "keyword") for r in keyword_results])
            
            # 語義搜索
            semantic_results = self._semantic_search(search_query)
            all_results.extend([(r, "semantic") for r in semantic_results])
            
            # 結構化搜索
            structural_results = self._structural_search(search_query)
            all_results.extend([(r, "structural") for r in structural_results])
        
        # 3. 結果融合和重排序
        fused_results = self._fusion_ranking(all_results, query)
        
        # 4. 轉換為NodeWithScore格式
        nodes_with_scores = self._convert_to_nodes(fused_results)
        
        logger.info(f"✅ 混合檢索完成，返回 {len(nodes_with_scores)} 個結果")
        return nodes_with_scores[:self.config.top_k]
    
    def _vector_search(self, query: str) -> List[SearchResult]:
        """向量相似度搜索"""
        try:
            # 生成查詢向量
            query_embedding = self.embedding_model.get_text_embedding(query)
            
            search_body = {
                "knn": {
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": self.config.rerank_top_k,
                    "num_candidates": self.config.rerank_top_k * 2
                }
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=search_body,
                size=self.config.rerank_top_k
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = SearchResult(
                    content=hit['_source']['content'],
                    score=hit['_score'],
                    source=hit['_source'].get('metadata', {}).get('source', 'unknown'),
                    metadata=hit['_source'].get('metadata', {}),
                    search_type="vector"
                )
                results.append(result)
            
            logger.info(f"🎯 向量搜索找到 {len(results)} 個結果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 向量搜索失敗: {e}")
            return []
    
    def _keyword_search(self, query: str) -> List[SearchResult]:
        """BM25關鍵字搜索"""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "boost": 2.0
                                    }
                                }
                            },
                            {
                                "match": {
                                    "bm25_content": {
                                        "query": query,
                                        "boost": 1.5
                                    }
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": query,
                                        "boost": 3.0
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=search_body,
                size=self.config.rerank_top_k
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = SearchResult(
                    content=hit['_source']['content'],
                    score=hit['_score'],
                    source=hit['_source'].get('metadata', {}).get('source', 'unknown'),
                    metadata=hit['_source'].get('metadata', {}),
                    search_type="keyword"
                )
                results.append(result)
            
            logger.info(f"🔑 關鍵字搜索找到 {len(results)} 個結果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 關鍵字搜索失敗: {e}")
            return []
    
    def _semantic_search(self, query: str) -> List[SearchResult]:
        """語義搜索（基於內容語義）"""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content.ngram": {
                                        "query": query,
                                        "boost": 1.5
                                    }
                                }
                            },
                            {
                                "terms": {
                                    "metadata.semantic_info.keywords": query.split(),
                                    "boost": 2.0
                                }
                            },
                            {
                                "terms": {
                                    "metadata.semantic_info.entities": query.split(),
                                    "boost": 2.5
                                }
                            }
                        ]
                    }
                }
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=search_body,
                size=self.config.rerank_top_k
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = SearchResult(
                    content=hit['_source']['content'],
                    score=hit['_score'],
                    source=hit['_source'].get('metadata', {}).get('source', 'unknown'),
                    metadata=hit['_source'].get('metadata', {}),
                    search_type="semantic"
                )
                results.append(result)
            
            logger.info(f"🧠 語義搜索找到 {len(results)} 個結果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 語義搜索失敗: {e}")
            return []
    
    def _structural_search(self, query: str) -> List[SearchResult]:
        """結構化搜索（基於文檔結構）"""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            # 在標題中搜索
                            {
                                "match": {
                                    "title": {
                                        "query": query,
                                        "boost": 3.0
                                    }
                                }
                            },
                            # 在章節中搜索
                            {
                                "match": {
                                    "metadata.document_structure.chapter": {
                                        "query": query,
                                        "boost": 2.5
                                    }
                                }
                            },
                            # 在節中搜索
                            {
                                "match": {
                                    "metadata.document_structure.section": {
                                        "query": query,
                                        "boost": 2.0
                                    }
                                }
                            },
                            # 按內容類型過濾
                            {
                                "bool": {
                                    "must": [
                                        {"match": {"content": query}},
                                        {"term": {"metadata.document_structure.content_type": "title"}}
                                    ],
                                    "boost": 2.0
                                }
                            }
                        ]
                    }
                }
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=search_body,
                size=self.config.rerank_top_k
            )
            
            results = []
            for hit in response['hits']['hits']:
                result = SearchResult(
                    content=hit['_source']['content'],
                    score=hit['_score'],
                    source=hit['_source'].get('metadata', {}).get('source', 'unknown'),
                    metadata=hit['_source'].get('metadata', {}),
                    search_type="structural"
                )
                results.append(result)
            
            logger.info(f"🏗️ 結構化搜索找到 {len(results)} 個結果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 結構化搜索失敗: {e}")
            return []
    
    def _fusion_ranking(self, results: List[Tuple[SearchResult, str]], query: str) -> List[SearchResult]:
        """融合排序"""
        
        if not results:
            return []
        
        # 按內容去重
        seen_content = set()
        unique_results = []
        for result, search_type in results:
            content_hash = hash(result.content[:100])  # 使用前100字符做去重
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                result.search_type = search_type  # 更新搜索類型
                unique_results.append(result)
        
        # 計算融合分數
        for result in unique_results:
            fusion_score = self._calculate_fusion_score(result, query)
            result.score = fusion_score
        
        # 按融合分數排序
        ranked_results = sorted(unique_results, key=lambda x: x.score, reverse=True)
        
        logger.info(f"🔀 融合排序完成，去重後剩餘 {len(ranked_results)} 個結果")
        return ranked_results
    
    def _calculate_fusion_score(self, result: SearchResult, query: str) -> float:
        """計算融合分數"""
        base_score = result.score
        
        # 根據搜索類型加權
        weight = {
            "vector": self.config.vector_weight,
            "keyword": self.config.keyword_weight,
            "semantic": self.config.semantic_weight,
            "structural": self.config.structural_weight
        }.get(result.search_type, 0.1)
        
        # 額外的信號
        bonus = 0.0
        
        # 內容長度獎勵（適中長度更好）
        content_length = len(result.content)
        if 200 <= content_length <= 1500:
            bonus += 0.1
        
        # 結構化內容獎勵
        if result.metadata.get('document_structure', {}).get('content_type') == 'title':
            bonus += 0.2
        
        # 查詢詞完全匹配獎勵
        if query.lower() in result.content.lower():
            bonus += 0.15
        
        final_score = base_score * weight + bonus
        return final_score
    
    def _convert_to_nodes(self, results: List[SearchResult]) -> List[NodeWithScore]:
        """轉換為NodeWithScore格式"""
        from llama_index.core.schema import TextNode
        
        nodes_with_scores = []
        for result in results:
            node = TextNode(
                text=result.content,
                metadata={
                    **result.metadata,
                    "search_type": result.search_type,
                    "fusion_score": result.score
                }
            )
            
            node_with_score = NodeWithScore(
                node=node,
                score=result.score
            )
            nodes_with_scores.append(node_with_score)
        
        return nodes_with_scores