#!/usr/bin/env python3
"""
測試文件刪除功能
"""

import sys
import os
from pathlib import Path
import requests

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_es_documents():
    """檢查ES中的文檔數量"""
    try:
        response = requests.get("http://elasticsearch:9200/rag_intelligent_assistant/_count", timeout=5)
        if response.status_code == 200:
            count = response.json().get('count', 0)
            print(f"📊 ES中當前文檔數量: {count}")
            return count
        else:
            print(f"❌ 無法獲取ES文檔數量，狀態碼: {response.status_code}")
            return -1
    except Exception as e:
        print(f"❌ 檢查ES文檔數量失敗: {e}")
        return -1

def get_document_sources():
    """獲取ES中的文檔來源"""
    try:
        query = {
            "size": 0,
            "aggs": {
                "sources": {
                    "terms": {
                        "field": "metadata.source.keyword",
                        "size": 100
                    }
                }
            }
        }
        
        response = requests.post(
            "http://elasticsearch:9200/rag_intelligent_assistant/_search",
            json=query,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            buckets = response.json().get('aggregations', {}).get('sources', {}).get('buckets', [])
            sources = [(bucket['key'], bucket['doc_count']) for bucket in buckets]
            print(f"📋 文檔來源:")
            for source, count in sources:
                print(f"   - {source}: {count} 個文檔")
            return sources
        else:
            print(f"❌ 無法獲取文檔來源，狀態碼: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 獲取文檔來源失敗: {e}")
        return []

def test_delete_single_file():
    """測試刪除單個文件"""
    print("\n🔄 測試刪除單個文件功能")
    print("=" * 50)
    
    try:
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        
        # 初始化RAG系統
        rag_system = ElasticsearchRAGSystem()
        
        # 檢查初始狀態
        print("📊 刪除前狀態:")
        initial_count = check_es_documents()
        sources = get_document_sources()
        
        if not sources:
            print("⚠️ 沒有文檔可以刪除")
            return False
        
        # 選擇第一個來源進行刪除
        target_source = sources[0][0]
        print(f"\n🎯 嘗試刪除文件: {target_source}")
        
        # 執行刪除
        success = rag_system.delete_file_from_knowledge_base(target_source)
        
        if success:
            print(f"✅ 刪除文件 {target_source} 成功")
        else:
            print(f"❌ 刪除文件 {target_source} 失敗")
            return False
        
        # 檢查刪除後狀態
        print("\n📊 刪除後狀態:")
        final_count = check_es_documents()
        get_document_sources()
        
        deleted_count = initial_count - final_count
        print(f"\n📈 刪除結果: {deleted_count} 個文檔被刪除")
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"❌ 測試刪除單個文件失敗: {e}")
        import traceback
        print(f"   詳細錯誤: {traceback.format_exc()}")
        return False

def test_clear_knowledge_base():
    """測試清空知識庫功能"""
    print("\n🔄 測試清空知識庫功能")
    print("=" * 50)
    
    try:
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        
        # 初始化RAG系統
        rag_system = ElasticsearchRAGSystem()
        
        # 檢查初始狀態
        print("📊 清空前狀態:")
        initial_count = check_es_documents()
        get_document_sources()
        
        if initial_count == 0:
            print("⚠️ 知識庫已經為空")
            return True
        
        print(f"\n🎯 嘗試清空知識庫")
        
        # 執行清空
        success = rag_system.clear_knowledge_base()
        
        if success:
            print(f"✅ 清空知識庫成功")
        else:
            print(f"❌ 清空知識庫失敗")
            return False
        
        # 檢查清空後狀態
        print("\n📊 清空後狀態:")
        final_count = check_es_documents()
        get_document_sources()
        
        print(f"\n📈 清空結果: 從 {initial_count} 個文檔清空到 {final_count} 個文檔")
        
        return final_count == 0
        
    except Exception as e:
        print(f"❌ 測試清空知識庫失敗: {e}")
        import traceback
        print(f"   詳細錯誤: {traceback.format_exc()}")
        return False

def main():
    """主函數"""
    print("🧪 文件刪除功能測試")
    print("=" * 60)
    
    # 檢查初始狀態
    print("📊 測試開始前的ES狀態:")
    check_es_documents()
    get_document_sources()
    
    # 測試單個文件刪除
    single_delete_success = test_delete_single_file()
    
    # 如果還有剩餘文檔，測試清空功能
    remaining_count = check_es_documents()
    if remaining_count > 0:
        clear_success = test_clear_knowledge_base()
    else:
        print("\n⚠️ 沒有剩餘文檔，跳過清空測試")
        clear_success = True
    
    # 最終總結
    print("\n" + "=" * 60)
    print("🎯 測試結果總結:")
    print(f"   單個文件刪除: {'✅ 成功' if single_delete_success else '❌ 失敗'}")
    print(f"   清空知識庫: {'✅ 成功' if clear_success else '❌ 失敗'}")
    
    if single_delete_success and clear_success:
        print("\n🎉 所有刪除功能測試通過！")
        return 0
    else:
        print("\n💥 部分刪除功能測試失敗！")
        return 1

if __name__ == "__main__":
    sys.exit(main())