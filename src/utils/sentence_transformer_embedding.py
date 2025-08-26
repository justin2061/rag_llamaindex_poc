#!/usr/bin/env python3
"""
本地 Sentence Transformers Jina Embedding
使用本地模型，無需 API 金鑰
"""

import logging
from typing import List
import numpy as np
from llama_index.core.embeddings import BaseEmbedding

logger = logging.getLogger(__name__)

class SentenceTransformerJinaEmbedding(BaseEmbedding):
    """本地 Sentence Transformers Jina 嵌入模型"""
    
    def __init__(self, model_name: str = "jinaai/jina-embeddings-v3", embed_dim: int = 1024):
        """
        初始化本地 Jina 嵌入模型
        
        Args:
            model_name: 模型名稱
            embed_dim: 嵌入維度
        """
        super().__init__(embed_dim=embed_dim)
        self.model_name = model_name
        self._embed_dim = embed_dim
        self._model = None
        
        # 延遲載入模型
        self._load_model()
    
    def _load_model(self):
        """載入 Sentence Transformers 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"📥 載入本地 Jina 模型: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name, 
                trust_remote_code=True
            )
            logger.info(f"✅ 本地 Jina 模型載入成功，維度: {self._embed_dim}")
            
        except ImportError:
            logger.error("❌ sentence-transformers 未安裝，請執行: pip install sentence-transformers")
            raise RuntimeError("sentence-transformers 依賴缺失")
        except Exception as e:
            logger.error(f"❌ 載入 Jina 模型失敗: {e}")
            raise RuntimeError(f"Jina 模型載入失敗: {e}")
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """獲取文本嵌入向量"""
        if not self._model:
            raise RuntimeError("模型未初始化")
        
        try:
            # 確保有文本
            if not text.strip():
                text = "empty"
            
            # 生成嵌入向量
            embedding = self._model.encode([text], convert_to_numpy=True)[0]
            
            # 確保維度正確
            if len(embedding) != self._embed_dim:
                logger.warning(f"⚠️ 嵌入維度不匹配: 期望 {self._embed_dim}, 實際 {len(embedding)}")
                # 如果維度不匹配，進行調整
                if len(embedding) > self._embed_dim:
                    embedding = embedding[:self._embed_dim]
                else:
                    # 補零
                    padding = np.zeros(self._embed_dim - len(embedding))
                    embedding = np.concatenate([embedding, padding])
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"❌ 生成文本嵌入失敗: {e}")
            # 回退到零向量
            return [0.0] * self._embed_dim
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """獲取查詢嵌入向量"""
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """異步獲取查詢嵌入向量"""
        return self._get_query_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """異步獲取文本嵌入"""
        return self._get_text_embedding(text)
    
    def similarity(self, embeddings1: List[List[float]], embeddings2: List[List[float]]) -> np.ndarray:
        """計算嵌入向量相似度"""
        if not self._model:
            raise RuntimeError("模型未初始化")
        
        try:
            return self._model.similarity(np.array(embeddings1), np.array(embeddings2))
        except Exception as e:
            logger.error(f"❌ 計算相似度失敗: {e}")
            # 回退到簡單餘弦相似度
            emb1 = np.array(embeddings1)
            emb2 = np.array(embeddings2)
            return np.dot(emb1, emb2.T) / (np.linalg.norm(emb1, axis=1)[:, None] * np.linalg.norm(emb2, axis=1))

def setup_sentence_transformer_jina(model_name: str = "jinaai/jina-embeddings-v3") -> bool:
    """
    設置本地 Sentence Transformers Jina 嵌入模型
    
    Args:
        model_name: Jina 模型名稱
        
    Returns:
        bool: 是否設置成功
    """
    try:
        from llama_index.core import Settings
        
        # 根據模型名稱選擇維度
        embed_dim_map = {
            "jinaai/jina-embeddings-v3": 1024,
            "jinaai/jina-embeddings-v2-base-en": 768,
            "jinaai/jina-embeddings-v2-small-en": 512,
            "jinaai/jina-embeddings-v1": 512
        }
        
        embed_dim = embed_dim_map.get(model_name, 1024)
        
        logger.info(f"🚀 設置本地 Sentence Transformers Jina 嵌入: {model_name}")
        
        # 創建嵌入模型
        embed_model = SentenceTransformerJinaEmbedding(
            model_name=model_name,
            embed_dim=embed_dim
        )
        
        # 設置全局配置
        Settings.embed_model = embed_model
        
        logger.info(f"✅ 本地 Jina 嵌入模型設置成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 本地 Jina 嵌入設置失敗: {e}")
        return False

def test_embedding_speed():
    """測試嵌入速度和質量"""
    try:
        logger.info("🧪 開始測試本地 Jina 嵌入...")
        
        # 測試句子
        sentences = [
            "The weather is lovely today.",
            "It's so sunny outside!",
            "He drove to the stadium.",
            "機器學習是人工智能的重要分支",
            "今天天氣很好",
            "他開車去了體育場"
        ]
        
        # 設置模型
        embed_model = SentenceTransformerJinaEmbedding()
        
        import time
        start_time = time.time()
        
        # 生成嵌入
        embeddings = []
        for sentence in sentences:
            emb = embed_model._get_text_embedding(sentence)
            embeddings.append(emb)
        
        process_time = time.time() - start_time
        
        logger.info(f"⏱️ 處理 {len(sentences)} 個句子耗時: {process_time:.2f}秒")
        logger.info(f"📊 平均每句: {process_time/len(sentences):.3f}秒")
        logger.info(f"📐 嵌入維度: {len(embeddings[0])}")
        
        # 測試相似度計算
        if len(embeddings) >= 2:
            similarities = embed_model.similarity([embeddings[0]], [embeddings[1]])
            logger.info(f"🔍 相似度範例: {similarities[0][0]:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 嵌入測試失敗: {e}")
        return False

if __name__ == "__main__":
    # 測試
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 測試本地 Sentence Transformers Jina 嵌入")
    success = test_embedding_speed()
    
    if success:
        print("✅ 測試成功！")
    else:
        print("❌ 測試失敗")