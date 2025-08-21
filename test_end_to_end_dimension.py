#!/usr/bin/env python3
"""
端到端維度一致性測試
模擬完整的索引-查詢流程
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_end_to_end_dimension():
    """端到端維度測試"""
    
    print("🔄 端到端維度一致性測試")
    print("=" * 50)
    
    try:
        # 1. 初始化系統
        print("📋 1. 初始化 RAG 系統...")
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        from llama_index.core import Document
        
        rag_system = ElasticsearchRAGSystem()
        
        if not rag_system.use_elasticsearch:
            print("❌ Elasticsearch 未正確初始化")
            return False
        
        config_dimension = rag_system.elasticsearch_config.get('dimension')
        print(f"   RAG 系統配置維度: {config_dimension}")
        
        # 2. 檢查 embedding 模型維度
        print("📊 2. 檢查 embedding 模型...")
        rag_system._ensure_models_initialized()
        
        if not rag_system.embedding_model:
            print("❌ Embedding 模型未初始化")
            return False
            
        model_dimension = rag_system.embedding_model.embed_dim
        print(f"   Embedding 模型維度: {model_dimension}")
        
        # 3. 測試文檔索引
        print("🔗 3. 測試文檔索引...")
        test_docs = [
            Document(text="這是第一個測試文檔，用於驗證維度一致性。", 
                    metadata={"source": "test_doc_1", "type": "dimension_test"}),
            Document(text="這是第二個測試文檔，包含不同的內容進行測試。", 
                    metadata={"source": "test_doc_2", "type": "dimension_test"})
        ]
        
        # 創建索引
        index = rag_system.create_index(test_docs)
        
        if index is None:
            print("❌ 索引創建失敗")
            return False
        
        print(f"   ✅ 成功索引 {len(test_docs)} 個文檔")
        
        # 4. 測試查詢
        print("🔍 4. 測試查詢...")
        
        # 使用 RAG 系統的查詢方法
        test_query = "測試文檔內容"
        print(f"   查詢: {test_query}")
        
        try:
            # 直接使用 query 方法而不是 create_query_engine
            response = rag_system.query(test_query)
            print(f"   ✅ 查詢成功，回應: {str(response)[:100]}...")
            
            # 檢查是否有結果
            if hasattr(response, 'source_nodes') and response.source_nodes:
                print(f"   ✅ 找到 {len(response.source_nodes)} 個相關文檔")
            else:
                print("   ⚠️ 未找到相關文檔，但查詢執行成功")
                
        except Exception as query_error:
            print(f"❌ 查詢執行失敗: {query_error}")
            
            # 檢查是否是維度相關錯誤
            error_msg = str(query_error).lower()
            if 'dimension' in error_msg or 'dims' in error_msg:
                print("❌ 檢測到維度相關錯誤！")
                return False
            else:
                print("⚠️ 非維度相關錯誤，但查詢仍失敗")
                return False
        
        # 5. 驗證向量維度
        print("🧪 5. 驗證向量維度...")
        
        # 生成測試向量
        test_embedding = rag_system.embedding_model.get_text_embedding(test_query)
        actual_query_dimension = len(test_embedding)
        
        print(f"   查詢向量維度: {actual_query_dimension}")
        
        # 6. 最終一致性檢查
        print(f"\n🔍 最終一致性檢查:")
        print("-" * 30)
        
        dimensions = {
            "配置維度": config_dimension,
            "模型維度": model_dimension, 
            "實際查詢維度": actual_query_dimension
        }
        
        all_consistent = True
        reference_dim = config_dimension
        
        for name, dim in dimensions.items():
            status = "✅" if dim == reference_dim else "❌"
            if dim != reference_dim:
                all_consistent = False
            print(f"   {name}: {dim} {status}")
        
        if all_consistent:
            print(f"\n✅ 端到端測試通過！")
            print(f"   - 所有維度一致: {reference_dim}")
            print(f"   - 索引創建成功")
            print(f"   - 查詢執行成功")
            print(f"   - 無維度相關錯誤")
            return True
        else:
            print(f"\n❌ 端到端測試失敗！")
            print(f"   - 維度不一致")
            return False
            
    except Exception as e:
        print(f"❌ 端到端測試異常: {str(e)}")
        import traceback
        print(f"   詳細錯誤: {traceback.format_exc()}")
        return False

def main():
    """主函數"""
    success = test_end_to_end_dimension()
    
    if success:
        print(f"\n🎉 端到端維度一致性測試成功！")
        return 0
    else:
        print(f"\n💥 端到端維度一致性測試失敗！")
        return 1

if __name__ == "__main__":
    sys.exit(main())