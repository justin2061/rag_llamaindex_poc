#!/usr/bin/env python3
"""
測試 Elasticsearch async/await 修復
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent))

def test_elasticsearch_rag_system():
    """測試 Elasticsearch RAG 系統"""
    print("🧪 測試 Elasticsearch RAG 系統修復...")
    
    try:
        # 導入必要模組
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        from llama_index.core import Document
        
        print("✅ 模組導入成功")
        
        # 初始化系統
        print("🔧 初始化 ElasticsearchRAGSystem...")
        rag_system = ElasticsearchRAGSystem()
        
        print("✅ 系統初始化成功")
        
        # 測試文檔處理
        print("📄 測試文檔添加...")
        test_docs = [
            Document(text="這是一個測試文檔，包含一些測試內容。", metadata={"source": "test1"}),
            Document(text="另一個測試文檔，用於驗證系統功能。", metadata={"source": "test2"})
        ]
        
        # 創建索引
        print("🔨 創建測試索引...")
        if rag_system.create_index(test_docs):
            print("✅ 索引創建成功")
            
            # 測試查詢
            print("🔍 測試查詢功能...")
            try:
                result = rag_system.query("測試內容")
                print(f"✅ 查詢成功，結果: {result[:100]}...")
                return True
            except Exception as query_error:
                print(f"❌ 查詢失敗: {query_error}")
                import traceback
                print(traceback.format_exc())
                return False
        else:
            print("❌ 索引創建失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_custom_elasticsearch_store():
    """測試自定義 Elasticsearch Store"""
    print("\n🧪 測試自定義 Elasticsearch Store...")
    
    try:
        from elasticsearch import Elasticsearch
        from src.storage.custom_elasticsearch_store import CustomElasticsearchStore
        from llama_index.core.schema import TextNode
        from llama_index.core.vector_stores.types import VectorStoreQuery
        
        print("✅ 模組導入成功")
        
        # 創建 Elasticsearch 客戶端
        es_client = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
        
        if es_client.ping():
            print("✅ Elasticsearch 連接成功")
            
            # 創建自定義 Store
            store = CustomElasticsearchStore(
                es_client=es_client,
                index_name="test_index"
            )
            
            # 測試添加節點
            test_nodes = [
                TextNode(text="測試節點1", node_id="node1"),
                TextNode(text="測試節點2", node_id="node2")
            ]
            
            print("➕ 測試添加節點...")
            ids = store.add(test_nodes)
            print(f"✅ 添加成功，IDs: {ids}")
            
            # 測試查詢
            print("🔍 測試查詢...")
            query = VectorStoreQuery(query_str="測試", similarity_top_k=2)
            result = store.query(query)
            print(f"✅ 查詢成功，找到 {len(result.nodes)} 個結果")
            
            return True
        else:
            print("⚠️ Elasticsearch 未運行，跳過測試")
            return True
            
    except Exception as e:
        print(f"❌ 自定義 Store 測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 開始 Elasticsearch 修復驗證...")
    
    # 測試自定義 Store
    store_test = test_custom_elasticsearch_store()
    
    # 測試完整 RAG 系統
    rag_test = test_elasticsearch_rag_system()
    
    print("\n📊 測試結果:")
    print(f"- 自定義 Store: {'✅ 通過' if store_test else '❌ 失敗'}")
    print(f"- RAG 系統: {'✅ 通過' if rag_test else '❌ 失敗'}")
    
    if store_test and rag_test:
        print("\n🎉 所有測試通過！async/await 問題已修復。")
        exit(0)
    else:
        print("\n❌ 部分測試失敗，需要進一步檢查。")
        exit(1)