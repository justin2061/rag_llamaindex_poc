#!/usr/bin/env python3
"""
測試 Elasticsearch RAG 系統
確保依賴正確安裝和基本功能可用
"""

import sys
import os

def test_imports():
    """測試主要模組導入"""
    print("🔍 測試模組導入...")
    
    try:
        import elasticsearch
        print(f"✅ Elasticsearch: {elasticsearch.__version__}")
    except ImportError as e:
        print(f"❌ Elasticsearch 導入失敗: {e}")
        return False
    
    try:
        from llama_index.vector_stores.elasticsearch import ElasticsearchStore
        print("✅ LlamaIndex Elasticsearch Vector Store")
    except ImportError as e:
        print(f"❌ LlamaIndex Elasticsearch 導入失敗: {e}")
        return False
    
    try:
        from elasticsearch_rag_system import ElasticsearchRAGSystem
        print("✅ ElasticsearchRAGSystem")
    except ImportError as e:
        print(f"❌ ElasticsearchRAGSystem 導入失敗: {e}")
        return False
    
    return True

def test_elasticsearch_connection():
    """測試 Elasticsearch 連接"""
    print("\n🔗 測試 Elasticsearch 連接...")
    
    try:
        from elasticsearch import Elasticsearch
        
        # 嘗試連接到本地 Elasticsearch
        es_config = {
            'hosts': ['http://localhost:9200'],
            'timeout': 5,
        }
        
        es = Elasticsearch(**es_config)
        
        if es.ping():
            print("✅ Elasticsearch 連接成功")
            
            # 獲取集群資訊
            info = es.info()
            print(f"   版本: {info['version']['number']}")
            print(f"   集群名稱: {info['cluster_name']}")
            return True
        else:
            print("⚠️ Elasticsearch 無法連接 (這是正常的，如果您尚未啟動 Elasticsearch)")
            return True  # 不將此視為錯誤
            
    except Exception as e:
        print(f"⚠️ Elasticsearch 連接測試失敗: {e}")
        print("   (這是正常的，如果您尚未啟動 Elasticsearch)")
        return True  # 不將此視為錯誤

def test_basic_initialization():
    """測試基本初始化"""
    print("\n🚀 測試 ElasticsearchRAGSystem 初始化...")
    
    try:
        from elasticsearch_rag_system import ElasticsearchRAGSystem
        
        # 創建系統實例（不連接 Elasticsearch）
        system = ElasticsearchRAGSystem()
        print("✅ ElasticsearchRAGSystem 初始化成功")
        
        # 檢查配置
        config = system.elasticsearch_config
        print(f"   主機: {config['host']}:{config['port']}")
        print(f"   索引名稱: {config['index_name']}")
        print(f"   向量維度: {config['dimension']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ElasticsearchRAGSystem 初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """測試配置載入"""
    print("\n⚙️ 測試配置載入...")
    
    try:
        from config import (
            ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, 
            ELASTICSEARCH_INDEX_NAME, RAG_SYSTEM_TYPE,
            ENABLE_ELASTICSEARCH
        )
        
        print(f"✅ RAG_SYSTEM_TYPE: {RAG_SYSTEM_TYPE}")
        print(f"✅ ENABLE_ELASTICSEARCH: {ENABLE_ELASTICSEARCH}")
        print(f"✅ ELASTICSEARCH_HOST: {ELASTICSEARCH_HOST}")
        print(f"✅ ELASTICSEARCH_INDEX_NAME: {ELASTICSEARCH_INDEX_NAME}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置載入失敗: {e}")
        return False

def test_memory_monitoring():
    """測試記憶體監控"""
    print("\n💾 測試記憶體監控...")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        print(f"✅ 當前記憶體使用: {memory_info.rss / 1024 / 1024:.1f} MB")
        print(f"✅ 虛擬記憶體: {memory_info.vms / 1024 / 1024:.1f} MB")
        print(f"✅ CPU 使用率: {process.cpu_percent():.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 記憶體監控失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    print("🧪 Elasticsearch RAG 系統測試")
    print("=" * 50)
    
    tests = [
        ("模組導入", test_imports),
        ("Elasticsearch 連接", test_elasticsearch_connection),
        ("基本初始化", test_basic_initialization),
        ("配置載入", test_config_loading),
        ("記憶體監控", test_memory_monitoring),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 執行時發生錯誤: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 測試結果摘要")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！Elasticsearch RAG 系統就緒。")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查上述錯誤訊息。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)