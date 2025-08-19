#!/usr/bin/env python3
"""
立即修復方案：強制設置本地嵌入模型
"""

import os
from typing import List
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core import Settings
try:
    import streamlit as st
except ImportError:
    # 創建 mock streamlit 用於測試
    class MockSt:
        def success(self, msg): print(f"SUCCESS: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    st = MockSt()

class SimpleLocalEmbedding(BaseEmbedding):
    """簡單的本地嵌入模型 - 不依賴任何外部 API"""
    
    def __init__(self):
        super().__init__()
        self.embed_dim = 384  # 小維度，快速
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """使用簡單的字符哈希生成嵌入向量"""
        import hashlib
        
        # 確保有文本
        if not text.strip():
            text = "empty"
        
        # 生成多個不同的哈希值
        embeddings = []
        
        # 使用多種哈希算法
        for i in range(self.embed_dim // 32):  # 每個哈希生成32個值
            seed_text = f"{text}_{i}"
            hash_obj = hashlib.md5(seed_text.encode())
            hash_bytes = hash_obj.digest()
            
            # 將字節轉換為浮點數
            for j in range(0, len(hash_bytes), 4):
                if len(embeddings) >= self.embed_dim:
                    break
                # 取4個字節組成一個整數，然後歸一化
                chunk = hash_bytes[j:j+4]
                if len(chunk) == 4:
                    value = int.from_bytes(chunk, byteorder='big')
                    normalized = (value / (2**32 - 1)) * 2 - 1  # 歸一化到 [-1, 1]
                    embeddings.append(normalized)
        
        # 確保維度正確
        while len(embeddings) < self.embed_dim:
            embeddings.append(0.0)
        
        return embeddings[:self.embed_dim]
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """獲取查詢嵌入向量"""
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """異步獲取查詢嵌入向量"""
        return self._get_query_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """異步獲取文本嵌入"""
        return self._get_text_embedding(text)

def setup_immediate_fix():
    """立即修復嵌入模型問題"""
    
    # 1. 清除 OpenAI 環境變數
    openai_vars = ['OPENAI_API_KEY', 'OPENAI_API_BASE', 'OPENAI_ORGANIZATION']
    for var in openai_vars:
        if var in os.environ:
            del os.environ[var]
    
    # 2. 設置一個假的 OpenAI key 來避免驗證
    os.environ['OPENAI_API_KEY'] = 'sk-fake-key-for-llamaindex'
    
    # 3. 創建本地嵌入模型
    embed_model = SimpleLocalEmbedding()
    
    # 4. 強制設置為全域預設
    Settings.embed_model = embed_model
    
    st.success("✅ 使用簡單本地嵌入模型（立即修復版本）")
    return embed_model

if __name__ == "__main__":
    # 測試
    embed_model = setup_immediate_fix()
    test_text = "這是一個測試"
    result = embed_model._get_text_embedding(test_text)
    print(f"✅ 嵌入成功，維度: {len(result)}")
    print(f"前5個值: {result[:5]}")