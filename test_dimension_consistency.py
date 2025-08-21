#!/usr/bin/env python3
"""
維度一致性測試
確認索引和查詢時使用相同的維度
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_dimension_consistency():
    """測試維度一致性"""
    
    print("🔍 維度一致性測試")
    print("=" * 40)
    
    # 1. 檢查配置文件中的維度
    try:
        from config.config import ELASTICSEARCH_VECTOR_DIMENSION
        config_dimension = ELASTICSEARCH_VECTOR_DIMENSION
        print(f"📋 配置文件維度: {config_dimension}")
    except ImportError as e:
        print(f"❌ 無法導入配置: {e}")
        return False
    
    # 2. 檢查 embedding_fix.py 中的維度使用
    try:
        from src.utils.embedding_fix import SafeJinaEmbedding
        
        # 使用默認配置創建 embedding 模型
        api_key = os.getenv("JINA_API_KEY")
        embedding_model_default = SafeJinaEmbedding(api_key=api_key)
        
        print(f"📊 Embedding 模型默認維度: {embedding_model_default.embed_dim}")
        
        # 使用顯式配置創建 embedding 模型
        embedding_model_explicit = SafeJinaEmbedding(
            api_key=api_key,
            dimensions=config_dimension
        )
        
        print(f"📊 Embedding 模型顯式維度: {embedding_model_explicit.embed_dim}")
        
    except Exception as e:
        print(f"❌ Embedding 模型測試失敗: {e}")
        return False
    
    # 3. 檢查 Elasticsearch RAG 系統的配置
    try:
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        
        # 創建 RAG 系統實例但不初始化 ES 連接（避免錯誤）
        class TestElasticsearchRAGSystem(ElasticsearchRAGSystem):
            def _initialize_elasticsearch(self):
                return False  # 跳過 ES 初始化
        
        rag_system = TestElasticsearchRAGSystem()
        rag_config = rag_system.elasticsearch_config
        
        print(f"📊 RAG 系統配置維度: {rag_config.get('dimension')}")
        
    except Exception as e:
        print(f"❌ RAG 系統測試失敗: {e}")
        return False
    
    # 4. 測試實際的 embedding 生成維度
    try:
        test_text = "測試維度一致性"
        
        # 使用默認配置生成 embedding
        embedding_default = embedding_model_default.get_text_embedding(test_text)
        actual_dim_default = len(embedding_default)
        
        # 使用顯式配置生成 embedding
        embedding_explicit = embedding_model_explicit.get_text_embedding(test_text)
        actual_dim_explicit = len(embedding_explicit)
        
        print(f"🧪 實際生成維度 (默認): {actual_dim_default}")
        print(f"🧪 實際生成維度 (顯式): {actual_dim_explicit}")
        
    except Exception as e:
        print(f"❌ Embedding 生成測試失敗: {e}")
        return False
    
    # 5. 檢查 Elasticsearch Mapping
    try:
        import requests
        response = requests.get("http://localhost:9200/rag_intelligent_assistant/_mapping", timeout=5)
        
        if response.status_code == 200:
            mapping_data = response.json()
            es_dimension = mapping_data['rag_intelligent_assistant']['mappings']['properties']['embedding']['dims']
            print(f"📊 Elasticsearch Mapping 維度: {es_dimension}")
        else:
            print(f"⚠️ 無法獲取 ES Mapping，狀態碼: {response.status_code}")
            es_dimension = None
            
    except Exception as e:
        print(f"⚠️ 無法檢查 ES Mapping: {e}")
        es_dimension = None
    
    # 6. 一致性驗證
    print(f"\n🔍 一致性檢查:")
    print("-" * 30)
    
    dimensions = {
        "配置文件": config_dimension,
        "Embedding默認": embedding_model_default.embed_dim,
        "Embedding顯式": embedding_model_explicit.embed_dim,
        "RAG系統配置": rag_config.get('dimension'),
        "實際生成(默認)": actual_dim_default,
        "實際生成(顯式)": actual_dim_explicit,
        "ES Mapping": es_dimension
    }
    
    # 顯示所有維度
    reference_dimension = config_dimension
    all_consistent = True
    
    for name, dim in dimensions.items():
        if dim is not None:
            status = "✅" if dim == reference_dimension else "❌"
            if dim != reference_dimension:
                all_consistent = False
            print(f"{name}: {dim} {status}")
        else:
            print(f"{name}: 無法檢測 ⚠️")
    
    # 7. 最終結果
    print(f"\n🎯 一致性測試結果:")
    if all_consistent:
        print(f"✅ 所有維度配置一致: {reference_dimension}")
        print(f"✅ 索引和查詢將使用相同維度")
        return True
    else:
        print(f"❌ 檢測到維度不一致問題")
        print(f"⚠️ 這可能導致查詢錯誤")
        
        # 提供修復建議
        print(f"\n💡 修復建議:")
        print(f"   1. 確保所有配置都使用 ELASTICSEARCH_VECTOR_DIMENSION")
        print(f"   2. 重啟服務以載入新配置")
        print(f"   3. 重新創建 Elasticsearch 索引")
        
        return False

def main():
    """主函數"""
    success = test_dimension_consistency()
    
    if success:
        print(f"\n🎉 維度一致性測試通過！")
        return 0
    else:
        print(f"\n💥 維度一致性測試失敗！")
        return 1

if __name__ == "__main__":
    sys.exit(main())