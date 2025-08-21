#!/usr/bin/env python3
"""
測試第一次啟動時的 Elasticsearch mapping 自動創建功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_first_startup():
    """測試第一次啟動功能"""
    print("🚀 測試 Elasticsearch 第一次啟動自動創建 mapping 功能")
    
    try:
        # 導入 ElasticsearchRAGSystem
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        
        print("📋 正在初始化 ElasticsearchRAGSystem...")
        
        # 創建 RAG 系統實例 - 這應該會觸發第一次啟動檢測
        rag_system = ElasticsearchRAGSystem()
        
        # 檢查初始化是否成功
        if not rag_system.use_elasticsearch:
            print("⚠️ Elasticsearch 未啟用，可能初始化失敗")
            return False
        
        print("✅ ElasticsearchRAGSystem 初始化完成")
        
        # 檢查 ES 客戶端是否正確初始化
        if hasattr(rag_system, 'elasticsearch_client') and rag_system.elasticsearch_client:
            print("✅ Elasticsearch 客戶端已初始化")
            
            # 檢查索引是否存在
            client = rag_system.elasticsearch_client
            index_name = rag_system.index_name
            
            if client.indices.exists(index=index_name):
                print(f"✅ 索引 '{index_name}' 已成功創建")
                
                # 獲取 mapping 信息
                mapping_response = client.indices.get_mapping(index=index_name)
                mapping = mapping_response[index_name]['mappings']
                
                print(f"📊 Mapping 信息:")
                properties = mapping.get('properties', {})
                print(f"   字段數量: {len(properties)}")
                
                if 'embedding' in properties:
                    embedding_config = properties['embedding']
                    print(f"   向量維度: {embedding_config.get('dims', 'N/A')}")
                    print(f"   相似度算法: {embedding_config.get('similarity', 'N/A')}")
                
                return True
            else:
                print(f"❌ 索引 '{index_name}' 未能創建")
                return False
        else:
            print("❌ Elasticsearch 客戶端未正確初始化")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"❌ 錯誤詳情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_first_startup()
    if success:
        print("\n🎉 第一次啟動測試成功！")
        sys.exit(0)
    else:
        print("\n💥 第一次啟動測試失敗！")
        sys.exit(1)