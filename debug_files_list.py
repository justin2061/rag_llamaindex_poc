#!/usr/bin/env python3
"""
調試文件列表獲取問題
"""

import sys
from pathlib import Path
import traceback

# 添加項目根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent))

def debug_files_list():
    """調試文件列表獲取"""
    print("🔍 開始調試文件列表獲取問題...")
    
    try:
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        from src.utils.embedding_fix import prevent_openai_fallback
        
        print("✅ 模組導入成功")
        
        # 防止 OpenAI 回退
        prevent_openai_fallback()
        
        # 初始化系統
        print("🔧 初始化 ElasticsearchRAGSystem...")
        rag_system = ElasticsearchRAGSystem()
        
        print(f"✅ 系統初始化成功")
        print(f"📊 系統類型: {type(rag_system)}")
        print(f"🔧 是否使用 Elasticsearch: {getattr(rag_system, 'use_elasticsearch', False)}")
        print(f"🔧 Elasticsearch Store: {type(getattr(rag_system, 'elasticsearch_store', None))}")
        print(f"🔧 Elasticsearch Client: {type(getattr(rag_system, 'elasticsearch_client', None))}")
        
        # 測試連接
        if hasattr(rag_system, 'elasticsearch_client') and rag_system.elasticsearch_client:
            try:
                ping_result = rag_system.elasticsearch_client.ping()
                print(f"📶 Elasticsearch 連接狀態: {ping_result}")
                
                if ping_result:
                    # 檢查索引
                    index_name = getattr(rag_system.elasticsearch_store, 'index_name', 'rag_intelligent_assistant')
                    print(f"📋 使用的索引名稱: {index_name}")
                    
                    # 直接查詢 Elasticsearch
                    response = rag_system.elasticsearch_client.search(
                        index=index_name,
                        body={
                            "query": {"match_all": {}},
                            "size": 5,
                            "_source": ["metadata"]
                        }
                    )
                    
                    print(f"📊 Elasticsearch 查詢結果:")
                    print(f"   總文檔數: {response['hits']['total']['value']}")
                    
                    for i, hit in enumerate(response['hits']['hits']):
                        metadata = hit['_source'].get('metadata', {})
                        print(f"   文檔 {i+1}:")
                        print(f"     ID: {hit['_id']}")
                        print(f"     Source: {metadata.get('source', 'N/A')}")
                        print(f"     File Size: {metadata.get('file_size', 'N/A')}")
                        print(f"     Type: {metadata.get('type', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Elasticsearch 連接測試失敗: {e}")
        
        # 測試 get_indexed_files 方法
        print("\n🧪 測試 get_indexed_files 方法...")
        
        try:
            # 檢查方法是否存在
            if hasattr(rag_system, 'get_indexed_files'):
                print("✅ get_indexed_files 方法存在")
                
                files = rag_system.get_indexed_files()
                
                print(f"📋 獲取到的文件列表:")
                print(f"   文件數量: {len(files)}")
                
                for i, file_info in enumerate(files):
                    print(f"   文件 {i+1}:")
                    print(f"     Name: {file_info.get('name', 'N/A')}")
                    print(f"     ID: {file_info.get('id', 'N/A')}")
                    print(f"     Size: {file_info.get('size', 'N/A')}")
                    print(f"     Type: {file_info.get('type', 'N/A')}")
                    print(f"     Node Count: {file_info.get('node_count', 'N/A')}")
            else:
                print("❌ get_indexed_files 方法不存在")
                
                # 列出所有可用的方法
                methods = [method for method in dir(rag_system) if not method.startswith('_')]
                print(f"🔧 可用的方法: {methods}")
        
        except Exception as e:
            print(f"❌ get_indexed_files 方法調用失敗: {e}")
            print(f"📜 詳細錯誤:")
            print(traceback.format_exc())
        
        # 測試 _get_elasticsearch_files 方法
        print("\n🧪 測試 _get_elasticsearch_files 方法...")
        
        try:
            if hasattr(rag_system, '_get_elasticsearch_files'):
                print("✅ _get_elasticsearch_files 方法存在")
                
                files = rag_system._get_elasticsearch_files()
                
                print(f"📋 _get_elasticsearch_files 結果:")
                print(f"   文件數量: {len(files)}")
                
                for i, file_info in enumerate(files):
                    print(f"   文件 {i+1}: {file_info}")
            else:
                print("❌ _get_elasticsearch_files 方法不存在")
        
        except Exception as e:
            print(f"❌ _get_elasticsearch_files 方法調用失敗: {e}")
            print(f"📜 詳細錯誤:")
            print(traceback.format_exc())
        
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        print(f"📜 完整錯誤:")
        print(traceback.format_exc())

if __name__ == "__main__":
    debug_files_list()