#!/usr/bin/env python3
"""
簡單修正：防止 LlamaIndex 回退到 OpenAI
"""

import os
from llama_index.core import Settings

def prevent_openai_fallback():
    """防止 LlamaIndex 回退到 OpenAI"""
    # 設置空的 OpenAI API key 來防止自動使用
    os.environ['OPENAI_API_KEY'] = ''
    
    print("🛡️ 已防止 OpenAI 預設回退")

def setup_local_embedding():
    """設置本地嵌入模型"""
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        
        # 使用 HuggingFace 的本地嵌入模型
        embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        Settings.embed_model = embed_model
        print("✅ 使用本地 HuggingFace 嵌入模型")
        return embed_model
        
    except ImportError:
        print("❌ HuggingFace 嵌入模型不可用")
        return None

if __name__ == "__main__":
    prevent_openai_fallback()
    embed_model = setup_local_embedding()
    
    if embed_model:
        # 測試嵌入
        test_text = "這是一個測試"
        try:
            result = embed_model._get_text_embedding(test_text)
            print(f"✅ 嵌入測試成功，維度: {len(result)}")
        except Exception as e:
            print(f"❌ 嵌入測試失敗: {e}")
    else:
        print("❌ 無法設置嵌入模型")