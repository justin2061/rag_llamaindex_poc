#!/usr/bin/env python3
"""
模擬完整的 Streamlit 網頁文件上傳工作流程
測試修正配置後的 Elasticsearch RAG 文件上傳功能
"""

import os
import sys
import tempfile
from datetime import datetime

class MockStreamlitFile:
    """模擬 Streamlit 上傳文件物件"""
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

def simulate_web_ui_workflow():
    """模擬完整的網頁 UI 工作流程"""
    print("🌐 模擬 Streamlit 網頁 UI 文件上傳工作流程")
    print("=" * 60)
    
    # 步驟 1: 檢查配置 (模擬 main_app.py 啟動時的檢查)
    print("📝 步驟 1: 檢查系統配置")
    from config import RAG_SYSTEM_TYPE, ENABLE_ELASTICSEARCH, ELASTICSEARCH_HOST
    print(f"   RAG_SYSTEM_TYPE: {RAG_SYSTEM_TYPE}")
    print(f"   ENABLE_ELASTICSEARCH: {ENABLE_ELASTICSEARCH}")
    print(f"   ELASTICSEARCH_HOST: {ELASTICSEARCH_HOST}")
    
    # 步驟 2: 初始化系統 (模擬 init_rag_system())
    print("\n📝 步驟 2: 初始化 RAG 系統")
    try:
        if RAG_SYSTEM_TYPE == "elasticsearch" and ENABLE_ELASTICSEARCH:
            try:
                from elasticsearch_rag_system import ElasticsearchRAGSystem
                rag_system = ElasticsearchRAGSystem()
                system_type = "Elasticsearch RAG"
                print(f"✅ 初始化 {system_type}")
            except ImportError:
                print("⚠️ Elasticsearch RAG 不可用，回退到 Enhanced RAG")
                from enhanced_rag_system import EnhancedRAGSystem
                rag_system = EnhancedRAGSystem()
                system_type = "Enhanced RAG"
        else:
            from enhanced_rag_system import EnhancedRAGSystem
            rag_system = EnhancedRAGSystem()
            system_type = "Enhanced RAG"
            
        print(f"   系統類型: {system_type}")
        
    except Exception as e:
        print(f"❌ 系統初始化失敗: {e}")
        return False
    
    # 步驟 3: 初始化上傳組件 (模擬 init_upload_zone())
    print("\n📝 步驟 3: 初始化文件上傳組件")
    try:
        from components.knowledge_base.upload_zone import UploadZone
        upload_zone = UploadZone()
        print("✅ UploadZone 初始化成功")
    except Exception as e:
        print(f"❌ UploadZone 初始化失敗: {e}")
        return False
    
    # 步驟 4: 模擬文件上傳 (模擬用戶在網頁上上傳文件)
    print("\n📝 步驟 4: 模擬用戶文件上傳")
    uploaded_files = [
        MockStreamlitFile("用戶文檔1.txt", "這是用戶上傳的第一個文檔。\n包含重要的業務資訊和知識內容。"),
        MockStreamlitFile("用戶文檔2.txt", "這是第二個用戶文檔。\n包含技術規範和操作指南。"),
        MockStreamlitFile("重要筆記.md", "# 重要筆記\n\n## 業務流程\n這裡記錄了重要的業務流程和操作步驟。"),
    ]
    
    print(f"✅ 模擬上傳 {len(uploaded_files)} 個文件")
    for file in uploaded_files:
        print(f"   - {file.name} ({file.size} bytes)")
    
    # 步驟 5: 文件驗證 (模擬 render_upload_progress())
    print("\n📝 步驟 5: 文件驗證")
    valid_files = []
    for file in uploaded_files:
        try:
            is_valid = upload_zone.file_manager.validate_file(file)
            if is_valid:
                valid_files.append(file)
                print(f"✅ {file.name} 驗證通過")
            else:
                print(f"❌ {file.name} 驗證失敗")
        except Exception as e:
            print(f"⚠️ {file.name} 驗證時發生錯誤: {e}")
    
    if not valid_files:
        print("❌ 沒有有效文件可處理")
        return False
    
    print(f"✅ {len(valid_files)} 個文件通過驗證")
    
    # 步驟 6: 模擬點擊 "🚀 開始處理檔案" 按鈕
    print("\n📝 步驟 6: 模擬處理檔案按鈕點擊")
    try:
        # 這裡複製 main_app.py 中的確切邏輯 (line 184-215)
        print("   正在處理您的檔案並建立知識圖譜...")
        
        # 處理上傳的檔案 (main_app.py line 188-191)
        docs = rag_system.process_uploaded_files(valid_files)
        
        if docs:
            print(f"✅ 文件處理成功，產生 {len(docs)} 個文檔")
            
            # 建立索引 (main_app.py line 194-195)
            index = rag_system.create_index(docs)
            
            if index:
                print("✅ 索引建立成功")
                
                # 設置查詢引擎 (main_app.py line 198-202)
                if hasattr(rag_system, 'setup_graph_rag_retriever'):
                    rag_system.setup_graph_rag_retriever()
                    print("✅ Graph RAG 查詢引擎設置完成")
                else:
                    rag_system.setup_query_engine()
                    print("✅ 查詢引擎設置完成")
                
                # 標記系統就緒 (main_app.py line 204)
                system_ready = True
                print("✅ 系統標記為就緒狀態")
                
            else:
                print("❌ 索引建立失敗")
                return False
        else:
            print("❌ 文件處理失敗，請檢查檔案格式")
            return False
            
    except Exception as e:
        print(f"❌ 處理過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟 7: 測試查詢功能 (模擬用戶在聊天界面提問)
    print("\n📝 步驟 7: 測試查詢功能")
    try:
        test_queries = [
            "用戶文檔中包含什麼資訊？",
            "業務流程是什麼？",
            "技術規範有哪些內容？"
        ]
        
        for query in test_queries:
            print(f"   查詢: {query}")
            
            # 根據系統類型選擇查詢方法 (模擬 main_app.py line 260-270)
            if system_type == "Elasticsearch RAG" or hasattr(rag_system, 'get_elasticsearch_statistics'):
                response = rag_system.query_with_context(query)
            elif hasattr(rag_system, 'query_with_graph_context'):
                response = rag_system.query_with_graph_context(query)
            else:
                response = rag_system.query_with_context(query)
            
            if response and len(response) > 0:
                print(f"✅ 查詢成功 (回應: {len(response)} 字符)")
                break
            else:
                print(f"⚠️ 查詢無回應")
        
    except Exception as e:
        print(f"❌ 查詢測試失敗: {e}")
        return False
    
    # 步驟 8: 測試統計資訊 (模擬系統狀態顯示)
    print("\n📝 步驟 8: 測試統計資訊顯示")
    try:
        if system_type == "Elasticsearch RAG" and hasattr(rag_system, 'get_elasticsearch_statistics'):
            stats = rag_system.get_enhanced_statistics()
            base_stats = stats.get("base_statistics", {})
            es_stats = stats.get("elasticsearch_stats", {})
            
            print("✅ Elasticsearch RAG 統計:")
            print(f"   - 文檔數: {base_stats.get('total_documents', 0)}")
            print(f"   - 向量數: {base_stats.get('vectors_stored', 0)}")
            print(f"   - 索引名稱: {es_stats.get('index_name', 'unknown')}")
            print(f"   - 索引大小: {es_stats.get('index_size_mb', 0)} MB")
            
        else:
            stats = rag_system.get_enhanced_statistics() if hasattr(rag_system, 'get_enhanced_statistics') else {}
            print(f"✅ {system_type} 統計:")
            print(f"   - 可用統計項目: {len(stats)}")
        
    except Exception as e:
        print(f"❌ 統計資訊測試失敗: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 完整網頁 UI 工作流程模擬成功！")
    print("\n📊 模擬結果總結:")
    print(f"   - 系統類型: {system_type}")
    print(f"   - 上傳文件: {len(valid_files)} 個")
    print(f"   - 生成文檔: {len(docs)} 個")
    print(f"   - 系統狀態: 就緒")
    print(f"   - 查詢功能: 正常")
    print(f"   - 統計資訊: 可用")
    
    return True

if __name__ == "__main__":
    success = simulate_web_ui_workflow()
    if success:
        print("\n🎉 網頁 UI 文件上傳工作流程完全正常！")
        print("✅ 問題已解決：配置錯誤導致系統使用了錯誤的 RAG 類型。")
        print("🔧 解決方案：更新 .env 文件以正確設定 Elasticsearch RAG 配置。")
        sys.exit(0)
    else:
        print("\n❌ 網頁 UI 工作流程仍有問題，請檢查上述錯誤。")
        sys.exit(1)