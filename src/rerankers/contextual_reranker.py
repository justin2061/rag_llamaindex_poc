"""
Contextual Reranker System
上下文感知重排序系統，基於對話歷史和語義相關性重新排序檢索結果
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from llama_index.core.schema import NodeWithScore
from llama_index.core import Settings

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RerankingContext:
    """重排序上下文"""
    query: str
    conversation_history: List[Dict[str, str]]
    user_preferences: Dict[str, Any]
    domain_context: str
    search_intent: str  # informational, navigational, transactional

@dataclass
class RerankingFeatures:
    """重排序特徵"""
    semantic_similarity: float
    keyword_overlap: float
    context_relevance: float
    freshness_score: float
    authority_score: float
    user_preference_score: float
    diversity_penalty: float
    final_score: float

class SemanticAnalyzer:
    """語義分析器"""
    
    def __init__(self):
        self.llm_model = Settings.llm
    
    def compute_semantic_similarity(self, query: str, content: str) -> float:
        """計算語義相似度"""
        try:
            # 簡化版語義相似度計算
            # 實際應用中可使用更複雜的模型
            
            # 1. 關鍵詞重疊度
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            
            if not query_words:
                return 0.0
            
            overlap = len(query_words.intersection(content_words))
            keyword_sim = overlap / len(query_words)
            
            # 2. 語義概念匹配
            semantic_sim = self._compute_concept_similarity(query, content)
            
            # 3. 加權平均
            final_sim = 0.6 * keyword_sim + 0.4 * semantic_sim
            
            return min(final_sim, 1.0)
            
        except Exception as e:
            logger.warning(f"⚠️ 語義相似度計算失敗: {e}")
            return 0.0
    
    def _compute_concept_similarity(self, query: str, content: str) -> float:
        """計算概念相似度"""
        # 定義概念同義詞組
        concept_groups = {
            "learning": ["學習", "訓練", "教育", "培訓", "進修"],
            "artificial_intelligence": ["人工智能", "AI", "機器學習", "深度學習", "智能系統"],
            "algorithm": ["演算法", "算法", "方法", "技術", "策略"],
            "data": ["數據", "資料", "信息", "資訊", "數據集"],
            "model": ["模型", "框架", "系統", "架構", "結構"]
        }
        
        query_concepts = self._extract_concepts(query, concept_groups)
        content_concepts = self._extract_concepts(content, concept_groups)
        
        if not query_concepts:
            return 0.0
        
        # 計算概念重疊
        overlap = len(query_concepts.intersection(content_concepts))
        return overlap / len(query_concepts)
    
    def _extract_concepts(self, text: str, concept_groups: Dict[str, List[str]]) -> set:
        """提取文本中的概念"""
        concepts = set()
        text_lower = text.lower()
        
        for concept, keywords in concept_groups.items():
            if any(keyword in text_lower for keyword in keywords):
                concepts.add(concept)
        
        return concepts
    
    def analyze_search_intent(self, query: str) -> str:
        """分析搜索意圖"""
        query_lower = query.lower()
        
        # 信息型查詢
        if any(word in query_lower for word in ["什麼", "如何", "為什麼", "怎麼", "介紹"]):
            return "informational"
        
        # 導航型查詢
        if any(word in query_lower for word in ["找", "搜索", "位置", "在哪"]):
            return "navigational"
        
        # 事務型查詢
        if any(word in query_lower for word in ["下載", "購買", "註冊", "申請"]):
            return "transactional"
        
        return "informational"  # 預設為信息型

class ContextualReranker:
    """上下文感知重排序器"""
    
    def __init__(self, enable_contextual_reranking: bool = True):
        self.enable_contextual_reranking = enable_contextual_reranking
        self.semantic_analyzer = SemanticAnalyzer()
        
        # 特徵權重配置
        self.feature_weights = {
            "semantic_similarity": 0.35,
            "keyword_overlap": 0.20,
            "context_relevance": 0.25,
            "freshness_score": 0.05,
            "authority_score": 0.10,
            "user_preference_score": 0.05
        }
        
        logger.info(f"🎯 ContextualReranker 初始化完成")
        logger.info(f"   - 啟用上下文重排序: {enable_contextual_reranking}")
    
    def rerank_results(
        self, 
        results: List[NodeWithScore],
        reranking_context: RerankingContext
    ) -> List[NodeWithScore]:
        """重新排序檢索結果"""
        
        if not self.enable_contextual_reranking or not results:
            return results
        
        logger.info(f"🔄 開始重排序，候選結果: {len(results)}")
        
        # 1. 提取重排序特徵
        features_list = []
        for result in results:
            features = self._extract_reranking_features(result, reranking_context)
            features_list.append(features)
        
        # 2. 多樣性處理
        features_list = self._apply_diversity_penalty(features_list, results)
        
        # 3. 計算最終分數
        for i, features in enumerate(features_list):
            final_score = self._compute_final_score(features)
            features.final_score = final_score
            
            # 更新NodeWithScore的分數
            results[i].score = final_score
        
        # 4. 按最終分數排序
        reranked_results = sorted(
            zip(results, features_list), 
            key=lambda x: x[1].final_score, 
            reverse=True
        )
        
        final_results = [result for result, _ in reranked_results]
        
        logger.info(f"✅ 重排序完成，返回 {len(final_results)} 個結果")
        return final_results
    
    def _extract_reranking_features(
        self, 
        result: NodeWithScore, 
        context: RerankingContext
    ) -> RerankingFeatures:
        """提取重排序特徵"""
        
        content = result.node.text
        metadata = result.node.metadata
        
        # 1. 語義相似度
        semantic_sim = self.semantic_analyzer.compute_semantic_similarity(
            context.query, content
        )
        
        # 2. 關鍵詞重疊度
        keyword_overlap = self._compute_keyword_overlap(context.query, content)
        
        # 3. 上下文相關性
        context_relevance = self._compute_context_relevance(
            content, context.conversation_history
        )
        
        # 4. 時新性分數
        freshness_score = self._compute_freshness_score(metadata)
        
        # 5. 權威性分數
        authority_score = self._compute_authority_score(metadata)
        
        # 6. 用戶偏好分數
        user_preference_score = self._compute_user_preference_score(
            content, metadata, context.user_preferences
        )
        
        return RerankingFeatures(
            semantic_similarity=semantic_sim,
            keyword_overlap=keyword_overlap,
            context_relevance=context_relevance,
            freshness_score=freshness_score,
            authority_score=authority_score,
            user_preference_score=user_preference_score,
            diversity_penalty=0.0,  # 稍後計算
            final_score=0.0        # 稍後計算
        )
    
    def _compute_keyword_overlap(self, query: str, content: str) -> float:
        """計算關鍵詞重疊度"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(content_words))
        return overlap / len(query_words)
    
    def _compute_context_relevance(
        self, 
        content: str, 
        conversation_history: List[Dict[str, str]]
    ) -> float:
        """計算上下文相關性"""
        
        if not conversation_history:
            return 0.0
        
        # 獲取最近的對話內容
        recent_messages = conversation_history[-3:]  # 最近3輪對話
        context_text = " ".join([
            msg.get("content", "") 
            for msg in recent_messages 
            if msg.get("role") == "user"
        ])
        
        if not context_text.strip():
            return 0.0
        
        # 計算內容與對話歷史的相似度
        return self.semantic_analyzer.compute_semantic_similarity(
            context_text, content
        )
    
    def _compute_freshness_score(self, metadata: Dict[str, Any]) -> float:
        """計算時新性分數"""
        try:
            # 檢查處理時間
            processed_at = metadata.get("processing_info", {}).get("processed_at")
            if processed_at:
                from datetime import datetime
                processed_time = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                days_ago = (datetime.now() - processed_time.replace(tzinfo=None)).days
                
                # 越新的內容分數越高
                if days_ago <= 1:
                    return 1.0
                elif days_ago <= 7:
                    return 0.8
                elif days_ago <= 30:
                    return 0.6
                else:
                    return 0.4
            
            return 0.5  # 預設分數
            
        except Exception as e:
            logger.debug(f"時新性計算失敗: {e}")
            return 0.5
    
    def _compute_authority_score(self, metadata: Dict[str, Any]) -> float:
        """計算權威性分數"""
        
        score = 0.5  # 基礎分數
        
        # 根據來源類型調整權威性
        source = metadata.get("source", "").lower()
        
        if any(domain in source for domain in [".edu", ".gov", ".org"]):
            score += 0.3  # 教育、政府、組織網站
        elif any(domain in source for domain in [".pdf", "paper", "journal"]):
            score += 0.2  # 學術文件
        elif "wiki" in source:
            score += 0.1  # 維基百科
        
        # 根據文檔結構調整
        doc_structure = metadata.get("document_structure", {})
        if doc_structure.get("content_type") == "title":
            score += 0.1  # 標題內容通常更重要
        
        return min(score, 1.0)
    
    def _compute_user_preference_score(
        self, 
        content: str, 
        metadata: Dict[str, Any], 
        user_preferences: Dict[str, Any]
    ) -> float:
        """計算用戶偏好分數"""
        
        if not user_preferences:
            return 0.5
        
        score = 0.5
        
        # 偏好的內容類型
        preferred_types = user_preferences.get("content_types", [])
        content_type = metadata.get("document_structure", {}).get("content_type", "")
        if content_type in preferred_types:
            score += 0.2
        
        # 偏好的主題
        preferred_topics = user_preferences.get("topics", [])
        for topic in preferred_topics:
            if topic.lower() in content.lower():
                score += 0.1
                break
        
        # 偏好的文檔長度
        preferred_length = user_preferences.get("preferred_length", "medium")
        content_length = len(content)
        
        if preferred_length == "short" and content_length < 500:
            score += 0.1
        elif preferred_length == "medium" and 500 <= content_length <= 1500:
            score += 0.1
        elif preferred_length == "long" and content_length > 1500:
            score += 0.1
        
        return min(score, 1.0)
    
    def _apply_diversity_penalty(
        self, 
        features_list: List[RerankingFeatures], 
        results: List[NodeWithScore]
    ) -> List[RerankingFeatures]:
        """應用多樣性懲罰"""
        
        # 簡化版多樣性檢測：檢查內容相似度
        for i, features_i in enumerate(features_list):
            penalty = 0.0
            content_i = results[i].node.text
            
            for j, features_j in enumerate(features_list[:i]):  # 只檢查前面的結果
                content_j = results[j].node.text
                
                # 計算內容相似度
                similarity = self._compute_content_similarity(content_i, content_j)
                
                if similarity > 0.8:  # 高相似度
                    penalty += 0.2
                elif similarity > 0.6:  # 中等相似度
                    penalty += 0.1
            
            features_i.diversity_penalty = min(penalty, 0.5)  # 限制最大懲罰
        
        return features_list
    
    def _compute_content_similarity(self, content1: str, content2: str) -> float:
        """計算內容相似度"""
        # 簡化版：基於共同詞彙比例
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _compute_final_score(self, features: RerankingFeatures) -> float:
        """計算最終分數"""
        
        score = (
            self.feature_weights["semantic_similarity"] * features.semantic_similarity +
            self.feature_weights["keyword_overlap"] * features.keyword_overlap +
            self.feature_weights["context_relevance"] * features.context_relevance +
            self.feature_weights["freshness_score"] * features.freshness_score +
            self.feature_weights["authority_score"] * features.authority_score +
            self.feature_weights["user_preference_score"] * features.user_preference_score
        )
        
        # 應用多樣性懲罰
        score = max(0.0, score - features.diversity_penalty)
        
        return score
    
    def get_reranking_explanation(
        self, 
        result: NodeWithScore, 
        features: RerankingFeatures
    ) -> Dict[str, Any]:
        """獲取重排序解釋"""
        
        return {
            "final_score": features.final_score,
            "feature_breakdown": {
                "semantic_similarity": {
                    "value": features.semantic_similarity,
                    "weight": self.feature_weights["semantic_similarity"],
                    "contribution": features.semantic_similarity * self.feature_weights["semantic_similarity"]
                },
                "keyword_overlap": {
                    "value": features.keyword_overlap,
                    "weight": self.feature_weights["keyword_overlap"],
                    "contribution": features.keyword_overlap * self.feature_weights["keyword_overlap"]
                },
                "context_relevance": {
                    "value": features.context_relevance,
                    "weight": self.feature_weights["context_relevance"],
                    "contribution": features.context_relevance * self.feature_weights["context_relevance"]
                },
                "freshness_score": {
                    "value": features.freshness_score,
                    "weight": self.feature_weights["freshness_score"],
                    "contribution": features.freshness_score * self.feature_weights["freshness_score"]
                },
                "authority_score": {
                    "value": features.authority_score,
                    "weight": self.feature_weights["authority_score"],
                    "contribution": features.authority_score * self.feature_weights["authority_score"]
                },
                "user_preference_score": {
                    "value": features.user_preference_score,
                    "weight": self.feature_weights["user_preference_score"],
                    "contribution": features.user_preference_score * self.feature_weights["user_preference_score"]
                }
            },
            "diversity_penalty": features.diversity_penalty,
            "content_preview": result.node.text[:200] + "..." if len(result.node.text) > 200 else result.node.text
        }
    
    def update_feature_weights(self, new_weights: Dict[str, float]):
        """更新特徵權重"""
        
        # 確保權重總和為1
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            normalized_weights = {k: v/total_weight for k, v in new_weights.items()}
            self.feature_weights.update(normalized_weights)
            logger.info(f"🔧 特徵權重已更新: {self.feature_weights}")
        else:
            logger.warning("⚠️ 權重總和為0，保持原有權重")
    
    def analyze_reranking_performance(
        self, 
        original_results: List[NodeWithScore],
        reranked_results: List[NodeWithScore],
        ground_truth_relevance: List[float] = None
    ) -> Dict[str, Any]:
        """分析重排序性能"""
        
        analysis = {
            "original_count": len(original_results),
            "reranked_count": len(reranked_results),
            "score_changes": [],
            "rank_changes": []
        }
        
        # 分析分數變化
        for i, (orig, reranked) in enumerate(zip(original_results, reranked_results)):
            score_change = reranked.score - orig.score
            analysis["score_changes"].append({
                "index": i,
                "original_score": orig.score,
                "reranked_score": reranked.score,
                "score_change": score_change
            })
        
        # 計算統計指標
        score_changes = [item["score_change"] for item in analysis["score_changes"]]
        analysis["statistics"] = {
            "mean_score_change": np.mean(score_changes) if score_changes else 0,
            "std_score_change": np.std(score_changes) if score_changes else 0,
            "improved_results": sum(1 for change in score_changes if change > 0),
            "degraded_results": sum(1 for change in score_changes if change < 0)
        }
        
        return analysis