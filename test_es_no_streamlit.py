#!/usr/bin/env python3
"""
測試 Elasticsearch RAG 系統 - 不使用 Streamlit
"""

import sys
import os
sys.path.append('/app')

from custom_elasticsearch_store import CustomElasticsearchStore
from elasticsearch import Elasticsearch
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.retrievers import VectorIndexRetriever  
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from datetime import datetime

def test_full_system():
    """測試完整的 ElasticsearchRAG 系統功能"""
    print("🔧 初始化 Elasticsearch 客戶端...")
    
    # 1. 設置 ES 客戶端
    es = Elasticsearch(['http://elasticsearch:9200'], request_timeout=30)
    if not es.ping():
        print("❌ Elasticsearch 連接失敗")
        return False
    print("✅ Elasticsearch 連接成功")
    
    # 2. 設置嵌入模型
    print("🔧 載入嵌入模型...")
    embed_model = HuggingFaceEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
    Settings.embed_model = embed_model
    print("✅ 嵌入模型載入完成")
    
    # 3. 創建索引映射
    print("🔧 創建 Elasticsearch 索引...")
    index_name = "full_test_es"
    
    # 簡單的索引映射
    index_mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "content": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                },
                "metadata": {"type": "object"}
            }
        }
    }
    
    try:
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
            
        response = es.indices.create(index=index_name, body=index_mapping)
        print("✅ Elasticsearch 索引創建成功")
    except Exception as e:
        print(f"❌ 索引創建失敗: {e}")
        return False
    
    # 4. 創建自定義向量存儲
    print("🔧 創建自定義向量存儲...")
    vector_store = CustomElasticsearchStore(
        es_client=es,
        index_name=index_name,
        text_field='content',
        vector_field='embedding'
    )
    print("✅ 自定義向量存儲創建完成")
    
    # 5. 創建存儲上下文
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # 6. 準備測試文檔
    documents = [
        Document(
            text="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            metadata={"source": "ml_doc", "category": "technology", "timestamp": datetime.now().isoformat()}
        ),
        Document(
            text="Natural language processing helps computers understand human language.",
            metadata={"source": "nlp_doc", "category": "ai", "timestamp": datetime.now().isoformat()}
        ),
        Document(
            text="Deep learning uses neural networks with multiple layers to process data.",
            metadata={"source": "dl_doc", "category": "deep_learning", "timestamp": datetime.now().isoformat()}
        )
    ]
    
    print(f"🔧 準備索引 {len(documents)} 個文檔...")
    
    # 7. 創建索引
    try:
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model
        )
        print("✅ VectorStoreIndex 創建成功")
    except Exception as e:
        print(f"❌ 索引創建失敗: {e}")
        return False
    
    # 8. 驗證文檔是否已索引
    try:
        count_response = es.count(index=index_name)
        doc_count = count_response['count']
        print(f"✅ 已索引 {doc_count} 個文檔")
        
        if doc_count == 0:
            print("❌ 沒有文檔被索引")
            return False
            
    except Exception as e:
        print(f"❌ 文檔計數失敗: {e}")
        return False
    
    # 9. 創建查詢引擎
    print("🔧 創建查詢引擎...")
    try:
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=5
        )
        
        postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)
        
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=[postprocessor]
        )
        print("✅ 查詢引擎創建完成")
    except Exception as e:
        print(f"❌ 查詢引擎創建失敗: {e}")
        return False
    
    # 10. 測試查詢
    print("🔧 測試查詢...")
    test_queries = [
        "What is machine learning?",
        "Tell me about neural networks",
        "How does NLP work?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        try:
            print(f"\n查詢 {i}: {query}")
            response = query_engine.query(query)
            print(f"回答: {str(response)[:200]}...")
            
        except Exception as e:
            print(f"❌ 查詢失敗: {e}")
            return False
    
    print("\n🎉 所有測試通過！Elasticsearch RAG 系統工作正常。")
    return True

if __name__ == "__main__":
    print("🧪 開始完整 Elasticsearch RAG 系統測試")
    print("=" * 70)
    
    success = test_full_system()
    
    print("=" * 70)
    if success:
        print("✅ 測試成功！系統已準備就緒。")
    else:
        print("❌ 測試失敗！")
        
    sys.exit(0 if success else 1)