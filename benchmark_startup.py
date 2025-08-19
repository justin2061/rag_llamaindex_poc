#!/usr/bin/env python3
"""
啟動速度基準測試
比較不同啟動方式的載入時間
"""

import time
import subprocess
import sys
import os
from datetime import datetime

def measure_import_time(module_name, description):
    """測量模組導入時間"""
    print(f"🔍 測試 {description}...")
    start_time = time.time()
    
    try:
        if module_name == "config":
            import config
        elif module_name == "streamlit":
            import streamlit
        elif module_name == "llama_index":
            import llama_index
        elif module_name == "graph_rag_system":
            from graph_rag_system import GraphRAGSystem
        elif module_name == "enhanced_rag_system":
            from enhanced_rag_system import EnhancedRAGSystem
        elif module_name == "sentence_transformers":
            import sentence_transformers
        elif module_name == "chromadb":
            import chromadb
        elif module_name == "networkx":
            import networkx
        elif module_name == "groq":
            import groq
        elif module_name == "elasticsearch":
            import elasticsearch
        
        end_time = time.time()
        load_time = end_time - start_time
        print(f"✅ {description}: {load_time:.3f}秒")
        return load_time
        
    except ImportError as e:
        end_time = time.time()
        load_time = end_time - start_time
        print(f"⚠️ {description}: {load_time:.3f}秒 (未安裝: {str(e)})")
        return load_time
    except Exception as e:
        end_time = time.time()
        load_time = end_time - start_time
        print(f"❌ {description}: {load_time:.3f}秒 (錯誤: {str(e)})")
        return load_time

def measure_file_operations():
    """測量檔案系統操作時間"""
    print("\n📁 測試檔案系統操作...")
    
    operations = []
    
    # 測試目錄檢查
    start_time = time.time()
    exists = os.path.exists("data/index")
    end_time = time.time()
    operations.append(("目錄檢查", end_time - start_time))
    
    # 測試環境變數讀取
    start_time = time.time()
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    end_time = time.time()
    operations.append(("環境變數讀取", end_time - start_time))
    
    for desc, duration in operations:
        print(f"⚡ {desc}: {duration:.6f}秒")
    
    return sum(op[1] for op in operations)

def benchmark_startup_approaches():
    """基準測試不同的啟動方法"""
    print("🚀 Graph RAG 智能文檔問答助理 - 啟動速度基準測試")
    print("=" * 60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")
    print(f"作業系統: {os.name}")
    print("=" * 60)
    
    # 測試基本導入
    print("\n📦 基本模組導入測試")
    basic_imports = [
        ("streamlit", "Streamlit 框架"),
        ("config", "配置系統"),
    ]
    
    basic_total = 0
    for module, desc in basic_imports:
        basic_total += measure_import_time(module, desc)
    
    print(f"\n🔥 基本模組總計: {basic_total:.3f}秒")
    
    # 測試重型模組導入
    print("\n🏗️ 重型模組導入測試")
    heavy_imports = [
        ("llama_index", "LlamaIndex 框架"),
        # ("sentence_transformers", "句子轉換器"),  # 已改用 API 嵌入
        # ("chromadb", "ChromaDB 向量資料庫"),  # 已替換為 Elasticsearch
        # ("networkx", "NetworkX 圖資料庫"),  # Graph RAG 已禁用
        ("elasticsearch", "Elasticsearch 客戶端"),
        ("groq", "Groq API 客戶端"),
    ]
    
    heavy_total = 0
    for module, desc in heavy_imports:
        heavy_total += measure_import_time(module, desc)
    
    print(f"\n⚖️ 重型模組總計: {heavy_total:.3f}秒")
    
    # 測試系統特定模組
    print("\n🕸️ 系統特定模組測試")
    system_imports = [
        ("graph_rag_system", "Graph RAG 系統"),
        ("enhanced_rag_system", "Enhanced RAG 系統"),
    ]
    
    system_total = 0
    for module, desc in system_imports:
        system_total += measure_import_time(module, desc)
    
    print(f"\n🎯 系統模組總計: {system_total:.3f}秒")
    
    # 測試檔案操作
    file_total = measure_file_operations()
    print(f"\n💾 檔案操作總計: {file_total:.6f}秒")
    
    # 計算總計和分析
    print("\n" + "=" * 60)
    print("📊 綜合分析報告")
    print("=" * 60)
    
    all_modules_total = basic_total + heavy_total + system_total
    
    print(f"⚡ 基本啟動時間 (ultra_fast_start.py): {basic_total + file_total:.3f}秒")
    print(f"🚀 快速啟動時間 (quick_start.py): {basic_total + heavy_total * 0.3 + file_total:.3f}秒")
    print(f"🔧 完整啟動時間 (main_app.py): {all_modules_total + file_total:.3f}秒")
    
    # 提供優化建議
    print("\n💡 優化建議:")
    
    if basic_total > 2.0:
        print("- 🔴 基本模組載入時間過長，考慮減少不必要的初始導入")
    elif basic_total > 1.0:
        print("- 🟡 基本模組載入時間中等，可進一步優化")
    else:
        print("- 🟢 基本模組載入時間良好")
    
    if heavy_total > 10.0:
        print("- 🔴 重型模組載入時間很長，強烈建議延遲載入")
    elif heavy_total > 5.0:
        print("- 🟡 重型模組載入時間中等，建議按需載入")
    else:
        print("- 🟢 重型模組載入時間可接受")
    
    # 啟動策略建議
    print(f"\n🎯 推薦啟動策略:")
    if basic_total < 1.0:
        print(f"✅ ultra_fast_start.py - 極速啟動 (~{basic_total + file_total:.1f}秒)")
    if basic_total + heavy_total * 0.3 < 3.0:
        print(f"⚡ quick_start.py - 快速啟動 (~{basic_total + heavy_total * 0.3:.1f}秒)")
    print(f"🔧 main_app.py - 完整功能 (~{all_modules_total:.1f}秒)")
    
    return {
        'basic_total': basic_total,
        'heavy_total': heavy_total,
        'system_total': system_total,
        'file_total': file_total,
        'ultra_fast_estimate': basic_total + file_total,
        'quick_start_estimate': basic_total + heavy_total * 0.3 + file_total,
        'full_app_estimate': all_modules_total + file_total
    }

def generate_performance_report(results):
    """生成效能報告"""
    report_file = f"startup_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Graph RAG 智能文檔問答助理 - 啟動效能報告\n\n")
        f.write(f"**測試時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Python 版本**: {sys.version}\n")
        f.write(f"**系統**: {os.name}\n\n")
        
        f.write("## 📊 啟動時間對比\n\n")
        f.write("| 啟動方式 | 預估時間 | 推薦場景 |\n")
        f.write("|----------|----------|----------|\n")
        f.write(f"| ultra_fast_start.py | {results['ultra_fast_estimate']:.1f}秒 | 快速演示、新手體驗 |\n")
        f.write(f"| quick_start.py | {results['quick_start_estimate']:.1f}秒 | 日常使用、功能測試 |\n")
        f.write(f"| main_app.py | {results['full_app_estimate']:.1f}秒 | 完整功能、生產環境 |\n\n")
        
        f.write("## 📦 模組載入分析\n\n")
        f.write(f"- **基本模組**: {results['basic_total']:.3f}秒\n")
        f.write(f"- **重型模組**: {results['heavy_total']:.3f}秒\n")
        f.write(f"- **系統模組**: {results['system_total']:.3f}秒\n")
        f.write(f"- **檔案操作**: {results['file_total']:.6f}秒\n\n")
        
        f.write("## 🎯 優化策略\n\n")
        f.write("1. **極速啟動**: 僅載入基本 UI 和環境檢查\n")
        f.write("2. **延遲載入**: AI 模組在使用時才載入\n")
        f.write("3. **智能快取**: 重複使用已載入的模組\n")
        f.write("4. **漸進式**: 分步驟載入和初始化\n\n")
        
        f.write("---\n")
        f.write("*此報告由 benchmark_startup.py 自動生成*\n")
    
    print(f"\n📋 詳細報告已儲存至: {report_file}")

if __name__ == "__main__":
    try:
        results = benchmark_startup_approaches()
        generate_performance_report(results)
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
