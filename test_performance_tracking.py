#!/usr/bin/env python3
"""
測試性能追蹤功能
"""

import sys
import os
from pathlib import Path
import time

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_performance_tracker_basic():
    """測試基本性能追蹤功能"""
    print("🧪 測試基本性能追蹤功能")
    print("=" * 50)
    
    try:
        from src.utils.performance_tracker import PerformanceTracker, RAGStages
        
        # 創建追蹤器
        tracker = PerformanceTracker()
        
        # 測試基本追蹤
        with tracker.track_stage(RAGStages.DOCUMENT_PARSING, file_count=3):
            time.sleep(0.1)
        
        with tracker.track_stage(RAGStages.EMBEDDING_GENERATION, vector_count=100):
            time.sleep(0.2)
        
        with tracker.track_stage(RAGStages.INDEX_CREATION):
            time.sleep(0.05)
        
        # 獲取摘要
        summary = tracker.get_session_summary()
        
        print(f"✅ 追蹤了 {summary['total_stages']} 個階段")
        print(f"✅ 總時間: {summary['total_time']:.3f}s")
        print(f"✅ 平均時間: {summary['average_stage_time']:.3f}s")
        
        # 檢查各階段
        for stage in summary['stages']:
            print(f"   🔧 {stage['stage']}: {stage['duration']:.3f}s ({stage['percentage']}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本性能追蹤測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_rag_system_performance():
    """測試RAG系統性能追蹤集成"""
    print("\n🧪 測試RAG系統性能追蹤集成")
    print("=" * 50)
    
    try:
        from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
        from llama_index.core import Document
        
        # 初始化RAG系統
        rag_system = ElasticsearchRAGSystem()
        
        # 如果ES不可用，創建一些測試文檔
        if not rag_system.use_elasticsearch:
            print("⚠️ Elasticsearch不可用，跳過RAG系統測試")
            return True
        
        # 創建測試文檔
        test_docs = [
            Document(text="這是第一個性能測試文檔。", metadata={"source": "perf_test_1", "type": "performance_test"}),
            Document(text="這是第二個性能測試文檔。", metadata={"source": "perf_test_2", "type": "performance_test"})
        ]
        
        print(f"📄 準備索引 {len(test_docs)} 個測試文檔")
        
        # 測試索引創建（如果有性能追蹤）
        start_time = time.time()
        index = rag_system.create_index(test_docs)
        index_time = time.time() - start_time
        
        if index:
            print(f"✅ 索引創建成功，耗時: {index_time:.3f}s")
            
            # 測試查詢（如果有性能追蹤）
            test_query = "測試文檔"
            
            start_time = time.time()
            result = rag_system.query(test_query)
            query_time = time.time() - start_time
            
            print(f"✅ 查詢成功，耗時: {query_time:.3f}s")
            print(f"📝 查詢結果長度: {len(str(result))} 字符")
        else:
            print("❌ 索引創建失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ RAG系統性能測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_global_tracker():
    """測試全局追蹤器"""
    print("\n🧪 測試全局追蹤器")
    print("=" * 50)
    
    try:
        from src.utils.performance_tracker import get_performance_tracker, track_rag_stage, RAGStages
        
        # 清空之前的指標
        tracker = get_performance_tracker()
        tracker.clear_session_metrics()
        
        # 使用全局追蹤器
        with track_rag_stage(RAGStages.QUERY_PROCESSING, query="test query"):
            time.sleep(0.1)
            
            with track_rag_stage(RAGStages.SIMILARITY_SEARCH):
                time.sleep(0.05)
        
        # 檢查結果
        summary = tracker.get_session_summary()
        
        print(f"✅ 全局追蹤器記錄了 {summary['total_stages']} 個階段")
        
        for stage in summary['stages']:
            print(f"   🔧 {stage['stage']}: {tracker.format_duration(stage['duration'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 全局追蹤器測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_export_functionality():
    """測試導出功能"""
    print("\n🧪 測試導出功能")
    print("=" * 50)
    
    try:
        from src.utils.performance_tracker import get_performance_tracker
        
        tracker = get_performance_tracker()
        
        # 導出JSON
        json_data = tracker.export_metrics('json')
        print(f"✅ JSON導出成功，大小: {len(json_data)} 字符")
        
        # 導出CSV
        csv_data = tracker.export_metrics('csv')
        print(f"✅ CSV導出成功，大小: {len(csv_data)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 導出功能測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主函數"""
    print("🚀 性能追蹤系統完整測試")
    print("=" * 60)
    
    tests = [
        test_performance_tracker_basic,
        test_global_tracker,
        test_export_functionality,
        test_rag_system_performance
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_func.__name__} 通過")
            else:
                failed += 1
                print(f"❌ {test_func.__name__} 失敗")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 異常: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 測試結果總結:")
    print(f"   ✅ 通過: {passed}")
    print(f"   ❌ 失敗: {failed}")
    print(f"   📊 總測試數: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有性能追蹤功能測試通過！")
        return 0
    else:
        print(f"\n💥 有 {failed} 個測試失敗！")
        return 1

if __name__ == "__main__":
    sys.exit(main())