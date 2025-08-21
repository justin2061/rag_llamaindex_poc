#!/usr/bin/env python3
"""
調試 Elasticsearch mapping 創建
"""

import sys
import json
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_mapping_creation():
    """測試 mapping 創建"""
    print("🔧 測試 Elasticsearch mapping 創建")
    
    try:
        # 測試 mapping 加載器
        from config.elasticsearch.mapping_loader import ElasticsearchMappingLoader
        
        print("📋 測試 mapping 加載器...")
        loader = ElasticsearchMappingLoader()
        
        # 獲取默認變數
        variables = loader.get_default_variables()
        print(f"📊 默認變數: {variables}")
        
        # 加載 mapping
        mapping = loader.load_mapping(**variables)
        print(f"✅ 成功加載 mapping，字段數: {len(mapping['mappings']['properties'])}")
        
        # 驗證 mapping
        if loader.validate_mapping(mapping):
            print("✅ Mapping 驗證通過")
        else:
            print("❌ Mapping 驗證失敗")
            return False
        
        # 顯示處理後的 mapping
        print("📋 處理後的 mapping:")
        print(json.dumps(mapping, indent=2, ensure_ascii=False))
        
        # 測試直接創建索引
        from elasticsearch import Elasticsearch
        
        es_client = Elasticsearch([{'host': 'elasticsearch', 'port': 9200, 'scheme': 'http'}])
        
        if not es_client.ping():
            print("❌ 無法連接到 Elasticsearch")
            return False
        
        print("✅ 已連接到 Elasticsearch")
        
        index_name = "test_first_startup_mapping"
        
        # 刪除測試索引（如果存在）
        if es_client.indices.exists(index=index_name):
            es_client.indices.delete(index=index_name)
            print(f"🗑️ 已刪除現有測試索引: {index_name}")
        
        # 創建索引
        print(f"🔧 創建測試索引: {index_name}")
        response = es_client.indices.create(
            index=index_name,
            body=mapping
        )
        
        if response.get('acknowledged', False):
            print(f"✅ 成功創建測試索引: {index_name}")
            
            # 驗證索引
            if es_client.indices.exists(index=index_name):
                print("✅ 索引驗證通過")
                
                # 獲取實際 mapping
                actual_mapping = es_client.indices.get_mapping(index=index_name)
                actual_props = actual_mapping[index_name]['mappings']['properties']
                
                print(f"📊 實際索引信息:")
                print(f"   字段數: {len(actual_props)}")
                if 'embedding' in actual_props:
                    embedding_config = actual_props['embedding']
                    print(f"   向量維度: {embedding_config.get('dims', 'N/A')}")
                    print(f"   相似度: {embedding_config.get('similarity', 'N/A')}")
                
                # 清理測試索引
                es_client.indices.delete(index=index_name)
                print(f"🗑️ 已清理測試索引: {index_name}")
                
                return True
            else:
                print("❌ 索引驗證失敗")
                return False
        else:
            print(f"❌ 創建索引失敗: {response}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"❌ 錯誤詳情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_mapping_creation()
    if success:
        print("\n🎉 Mapping 創建測試成功！")
        sys.exit(0)
    else:
        print("\n💥 Mapping 創建測試失敗！")
        sys.exit(1)