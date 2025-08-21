#!/usr/bin/env python3
"""
測試 Jina API 連接和不同維度支持
"""

import os
import sys
import requests
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_jina_api_dimensions():
    """測試 Jina API 不同維度支持"""
    
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        print("❌ 未找到 JINA_API_KEY")
        return
    
    print(f"🔑 使用 API Key: {api_key[:20]}...")
    
    url = 'https://api.jina.ai/v1/embeddings'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    test_text = "這是一個測試文本"
    test_dimensions = [128, 256, 384, 512, 768, 1024]
    
    for dim in test_dimensions:
        print(f"\n🔧 測試維度: {dim}")
        
        data = {
            "model": "jina-embeddings-v3",
            "task": "text-matching",
            "dimensions": dim,
            "truncate": True,
            "input": [test_text]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            print(f"HTTP 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0:
                    embedding = result['data'][0]['embedding']
                    actual_dim = len(embedding)
                    print(f"✅ 成功 - 請求維度: {dim}, 實際維度: {actual_dim}")
                    
                    # 檢查維度一致性
                    if actual_dim == dim:
                        print(f"✅ 維度匹配")
                    else:
                        print(f"⚠️ 維度不匹配")
                else:
                    print(f"❌ 響應格式錯誤: {result}")
            else:
                print(f"❌ API 錯誤: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"錯誤詳情: {error_detail}")
                except:
                    print(f"錯誤內容: {response.text}")
                    
        except Exception as e:
            print(f"❌ 請求失敗: {str(e)}")

def test_current_embedding_setup():
    """測試當前 embedding 設置"""
    print("\n🔬 測試當前 embedding 設置")
    
    try:
        from src.utils.embedding_fix import SafeJinaEmbedding
        from config.config import ELASTICSEARCH_VECTOR_DIMENSION
        
        print(f"📊 配置維度: {ELASTICSEARCH_VECTOR_DIMENSION}")
        
        # 創建 embedding 實例
        api_key = os.getenv("JINA_API_KEY")
        embedding_model = SafeJinaEmbedding(
            api_key=api_key,
            model="jina-embeddings-v3",
            dimensions=ELASTICSEARCH_VECTOR_DIMENSION
        )
        
        print(f"🔧 Embedding 實例:")
        print(f"   - API Key 可用: {embedding_model.use_api}")
        print(f"   - 預期維度: {embedding_model.embed_dim}")
        print(f"   - 模型: {embedding_model.model}")
        
        # 測試生成 embedding
        test_text = "測試文本"
        embedding = embedding_model.get_text_embedding(test_text)
        actual_dim = len(embedding)
        
        print(f"✅ 生成 embedding 成功")
        print(f"   - 實際維度: {actual_dim}")
        print(f"   - 維度匹配: {'✅' if actual_dim == ELASTICSEARCH_VECTOR_DIMENSION else '❌'}")
        
        if actual_dim != ELASTICSEARCH_VECTOR_DIMENSION:
            print(f"⚠️ 維度不匹配可能的原因:")
            print(f"   - API 連接失敗，使用了本地後備")
            print(f"   - API key 無效")
            print(f"   - 網絡連接問題")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"錯誤堆疊: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🚀 開始 Jina API 維度測試")
    test_jina_api_dimensions()
    test_current_embedding_setup()