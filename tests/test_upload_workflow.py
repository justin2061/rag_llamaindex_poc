#!/usr/bin/env python3
"""
完整測試文件上傳到 Elasticsearch RAG 的工作流程
模擬 main_app.py 中的實際操作
"""

import os
import sys
from io import BytesIO
from typing import List, Dict, Any

# 模擬 Streamlit 上傳檔案物件
class MockUploadedFile:
    def __init__(self, name: str, content: str, file_type: str = "text/plain"):
        self.name = name
        self.size = len(content.encode('utf-8'))
        self.type = file_type
        self._content = content.encode('utf-8')
        self._position = 0
    
    def read(self, size=-1):
        if size == -1:
            data = self._content[self._position:]
            self._position = len(self._content)
        else:
            data = self._content[self._position:self._position+size]
            self._position += len(data)
        return data
    
    def seek(self, position):
        self._position = position
    
    def getvalue(self):
        return self._content

def test_complete_workflow():
    """測試完整的文件上傳到 RAG 工作流程"""
    print("🧪 開始測試完整的文件上傳工作流程")
    print("=" * 60)
    
    # 步驟 1: 測試 ElasticsearchRAGSystem 初始化
    print("📝 步驟 1: 初始化 ElasticsearchRAGSystem")
    try:
        from elasticsearch_rag_system import ElasticsearchRAGSystem
        rag_system = ElasticsearchRAGSystem()
        print("✅ ElasticsearchRAGSystem 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False
    
    # 步驟 2: 測試文件管理器
    print("\n📝 步驟 2: 測試用戶文件管理器")
    try:
        from user_file_manager import UserFileManager
        file_manager = UserFileManager()
        print("✅ UserFileManager 初始化成功")
        print(f"   上傳目錄: {file_manager.upload_dir}")
        print(f"   支援格式: {file_manager.supported_file_types}")
    except Exception as e:
        print(f"❌ 文件管理器初始化失敗: {e}")
        return False
    
    # 步驟 3: 創建模擬上傳文件
    print("\n📝 步驟 3: 創建模擬上傳文件")
    mock_files = [
        MockUploadedFile("測試文件1.txt", "這是第一個測試文件的內容。\n包含中文文字用來測試 RAG 系統的處理能力。", "text/plain"),
        MockUploadedFile("測試文件2.txt", "這是第二個測試文件。\n測試多文件處理和索引建立功能。", "text/plain"),
        MockUploadedFile("測試筆記.md", "# 測試筆記\n\n## 重要資訊\n這是一個 Markdown 格式的測試文件。", "text/markdown"),
    ]
    
    print(f"✅ 創建了 {len(mock_files)} 個模擬文件:")
    for file in mock_files:
        print(f"   - {file.name} ({file.size} bytes)")
    
    # 步驟 4: 測試文件驗證
    print("\n📝 步驟 4: 測試文件驗證")
    valid_files = []
    for file in mock_files:
        try:
            is_valid = file_manager.validate_file(file)
            if is_valid:
                valid_files.append(file)
                print(f"✅ {file.name} 驗證通過")
            else:
                print(f"❌ {file.name} 驗證失敗")
        except Exception as e:
            print(f"❌ {file.name} 驗證時發生錯誤: {e}")
    
    if not valid_files:
        print("❌ 沒有有效的文件可以處理")
        return False
    
    print(f"✅ 共有 {len(valid_files)} 個文件通過驗證")
    
    # 步驟 5: 測試文件處理（模擬 main_app.py 的邏輯）
    print("\n📝 步驟 5: 測試文件處理")
    try:
        # 這裡模擬 main_app.py 中的處理邏輯
        print("   正在處理上傳的檔案...")
        docs = rag_system.process_uploaded_files(valid_files)
        
        if docs:
            print(f"✅ 成功處理文件，產生 {len(docs)} 個文檔物件")
            for i, doc in enumerate(docs):
                print(f"   文檔 {i+1}: {len(doc.text)} 字符, 來源: {doc.metadata.get('source', 'unknown')}")
        else:
            print("❌ 文件處理失敗，沒有產生文檔物件")
            return False
            
    except Exception as e:
        print(f"❌ 文件處理時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟 6: 測試索引建立
    print("\n📝 步驟 6: 測試 Elasticsearch 索引建立")
    try:
        print("   正在建立 Elasticsearch 索引...")
        index = rag_system.create_index(docs)
        
        if index:
            print("✅ Elasticsearch 索引建立成功")
            print(f"   索引類型: {type(index).__name__}")
        else:
            print("❌ Elasticsearch 索引建立失敗")
            return False
            
    except Exception as e:
        print(f"❌ 索引建立時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟 7: 測試查詢引擎設置
    print("\n📝 步驟 7: 測試查詢引擎設置")
    try:
        rag_system.setup_query_engine()
        print("✅ 查詢引擎設置成功")
        
        if hasattr(rag_system, 'query_engine') and rag_system.query_engine:
            print(f"   查詢引擎類型: {type(rag_system.query_engine).__name__}")
        else:
            print("⚠️ 查詢引擎未正確設置")
            
    except Exception as e:
        print(f"❌ 查詢引擎設置失敗: {e}")
        return False
    
    # 步驟 8: 測試查詢功能
    print("\n📝 步驟 8: 測試查詢功能")
    try:
        test_query = "測試文件的內容是什麼？"
        print(f"   測試查詢: {test_query}")
        
        response = rag_system.query_with_context(test_query)
        
        if response and len(response) > 0:
            print(f"✅ 查詢成功，回應長度: {len(response)} 字符")
            print(f"   回應預覽: {response[:100]}...")
        else:
            print("❌ 查詢失敗或無回應")
            return False
            
    except Exception as e:
        print(f"❌ 查詢時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟 9: 測試統計資訊
    print("\n📝 步驟 9: 測試統計資訊獲取")
    try:
        stats = rag_system.get_enhanced_statistics()
        print("✅ 統計資訊獲取成功")
        print(f"   系統類型: {stats.get('system_type', 'unknown')}")
        
        base_stats = stats.get('base_statistics', {})
        es_stats = stats.get('elasticsearch_stats', {})
        
        print(f"   處理文檔數: {base_stats.get('documents_processed', 0)}")
        print(f"   向量數量: {base_stats.get('vectors_stored', 0)}")
        print(f"   ES 索引: {es_stats.get('index_name', 'unknown')}")
        print(f"   ES 文檔數: {es_stats.get('document_count', 0)}")
        
    except Exception as e:
        print(f"❌ 統計資訊獲取失敗: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 完整工作流程測試成功！")
    print("📊 測試總結:")
    print(f"   - 處理文件數: {len(valid_files)}")
    print(f"   - 生成文檔數: {len(docs)}")
    print(f"   - 索引建立: 成功")
    print(f"   - 查詢功能: 正常")
    print(f"   - 統計資訊: 可用")
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n✅ 所有測試通過！Elasticsearch RAG 文件上傳工作流程正常運作。")
        sys.exit(0)
    else:
        print("\n❌ 測試失敗！請檢查上述錯誤訊息。")
        sys.exit(1)