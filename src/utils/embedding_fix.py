#!/usr/bin/env python3
"""
修補檔案：防止 LlamaIndex 使用 OpenAI 預設 embedding
確保總是使用我們的自定義 Jina embedding 或後備方案
"""

import os
from typing import List
from llama_index.core.embeddings import BaseEmbedding

# 條件性導入 streamlit，API環境下使用 mock 實現
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    # Mock streamlit 接口
    class MockStreamlit:
        @staticmethod
        def error(message): print(f"ERROR: {message}")
        @staticmethod
        def success(message): print(f"SUCCESS: {message}")
        @staticmethod
        def warning(message): print(f"WARNING: {message}")
        @staticmethod
        def info(message): print(f"INFO: {message}")
    st = MockStreamlit()
from llama_index.core import Settings
import requests
from config.config import ELASTICSEARCH_VECTOR_DIMENSION
# from dotenv import load_dotenv

# load_dotenv()

class SafeJinaEmbedding(BaseEmbedding):
    """安全的 Jina Embedding，包含完整的後備方案"""
    
    def __init__(self, api_key: str = None, model: str = "jina-embeddings-v3", task: str = "text-matching", embed_batch_size: int = 10, dimensions: int = ELASTICSEARCH_VECTOR_DIMENSION):
        super().__init__(embed_batch_size=embed_batch_size)
        
        # 設置屬性 - 避免與 Pydantic 衝突
        object.__setattr__(self, '_api_key', api_key)
        object.__setattr__(self, '_model', model)
        object.__setattr__(self, '_task', task)
        object.__setattr__(self, '_dimensions', dimensions)
        object.__setattr__(self, '_url', 'https://api.jina.ai/v1/embeddings')
        object.__setattr__(self, '_embed_dim', dimensions)  # 使用指定的維度
        
        # 檢查是否有有效的 API key
        object.__setattr__(self, '_use_api', api_key and api_key.strip() and api_key != "dummy")
        
        if not self._use_api:
            st.warning("⚠️ 使用本地後備 embedding（功能有限）")
            st.info("💡 設定 JINA_API_KEY 以獲得更好的效果")
    
    @property
    def api_key(self):
        return object.__getattribute__(self, '_api_key')
    
    @property
    def model(self):
        return object.__getattribute__(self, '_model')
    
    @property
    def task(self):
        return object.__getattribute__(self, '_task')
    
    @property
    def url(self):
        return object.__getattribute__(self, '_url')
    
    @property
    def embed_dim(self):
        return object.__getattribute__(self, '_embed_dim')
    
    @property
    def use_api(self):
        return object.__getattribute__(self, '_use_api')
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """獲取單個文本的嵌入向量"""
        return self._get_text_embeddings([text])[0]
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """獲取多個文本的嵌入向量"""
        if self.use_api:
            return self._get_api_embeddings(texts)
        else:
            return self._get_fallback_embeddings(texts)
    
    def _get_api_embeddings(self, texts: List[str]) -> List[List[float]]:
        """使用 Jina API 獲取嵌入"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            "model": self.model,
            "task": self.task,
            "dimensions": self._dimensions,
            "truncate": True,
            "input": texts
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            embeddings = []
            for item in result.get('data', []):
                embedding = item.get('embedding', [])
                if len(embedding) != self.embed_dim:
                    st.warning(f"⚠️ 意外的嵌入維度: {len(embedding)}, 預期: {self.embed_dim}")
                embeddings.append(embedding)
            
            return embeddings
        except Exception as e:
            st.error(f"❌ Jina API 調用失敗: {str(e)}")
            st.warning("🔄 回退到本地 embedding")
            return self._get_fallback_embeddings(texts)
    
    def _get_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """本地後備嵌入方案"""
        embeddings = []
        for text in texts:
            embedding = self._simple_text_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _simple_text_embedding(self, text: str) -> List[float]:
        """簡單的文本特徵向量（後備方案）"""
        import hashlib
        import math
        
        # 確保文本不為空
        if not text.strip():
            text = "empty"
        
        # 基於文本內容生成一致的特徵向量
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # 生成固定維度的向量
        embedding = []
        for i in range(self.embed_dim // 8):  # 每8個值為一組
            hex_start = (i * 2) % 64  # 循環使用 hash
            hex_val = int(text_hash[hex_start:hex_start+2], 16)
            
            # 生成8個相關的特徵值
            for j in range(8):
                value = (hex_val + j * 31) % 256  # 使用質數避免週期性
                normalized = (value / 255.0) * 2 - 1  # 歸一化到 [-1, 1]
                embedding.append(normalized)
        
        # 確保維度正確
        while len(embedding) < self.embed_dim:
            embedding.append(0.0)
        
        return embedding[:self.embed_dim]
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """獲取查詢嵌入向量"""
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """異步獲取查詢嵌入向量"""
        return self._get_query_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """異步獲取文本嵌入"""
        return self._get_text_embedding(text)

def setup_safe_embedding(jina_api_key: str = None):
    """設置安全的嵌入模型 - 完全本地化，不使用任何API"""
    
    # 強制使用本地後備模型，忽略API金鑰
    print("🔄 使用本地後備嵌入模型（已停用API調用）")
    
    embedding_model = SafeJinaEmbedding(
        api_key=None,  # 強制使用本地模型
        model="jina-embeddings-v3",
        task="text-matching", 
        dimensions=ELASTICSEARCH_VECTOR_DIMENSION # 匹配 Elasticsearch 索引維度
    )
    
    # 設置為全域預設
    Settings.embed_model = embedding_model
    
    # 條件性顯示技術訊息
    try:
        from config.config import SHOW_TECHNICAL_MESSAGES, DEBUG_MODE
        show_tech = (DEBUG_MODE or SHOW_TECHNICAL_MESSAGES or 
                    st.session_state.get('show_tech_messages', False))
        if show_tech:
            st.success("✅ 使用本地嵌入模型（已停用API調用）")
        else:
            print("[TECH] ✅ 使用本地嵌入模型（已停用API調用）")
    except Exception:
        print("[TECH] ✅ 使用本地嵌入模型（已停用API調用）")
    return embedding_model

def prevent_openai_fallback():
    """防止 LlamaIndex 回退到 OpenAI"""
    # 設置一個假的 OpenAI API key 來避免檢查失敗
    # 這樣 LlamaIndex 不會報錯，但我們會用自己的嵌入模型覆蓋它
    os.environ['OPENAI_API_KEY'] = 'sk-fake-key-to-avoid-llamaindex-validation-error'
    
    # 同時移除其他可能的 OpenAI 配置
    openai_config_keys = ['OPENAI_API_BASE', 'OPENAI_ORGANIZATION']
    for key in openai_config_keys:
        if key in os.environ:
            del os.environ[key]
    
    # 在調試模式下記錄，避免在用戶界面顯示技術信息
    import logging
    logging.getLogger(__name__).info("已防止 OpenAI 預設回退")

if __name__ == "__main__":
    # 測試嵌入模型
    print("測試安全嵌入模型...")
    
    embedding = setup_safe_embedding()
    test_text = "這是一個測試文本"
    
    try:
        result = embedding._get_text_embedding(test_text)
        print(f"✅ 嵌入成功，維度: {len(result)}")
        print(f"前5個值: {result[:5]}")
    except Exception as e:
        print(f"❌ 嵌入失敗: {e}")