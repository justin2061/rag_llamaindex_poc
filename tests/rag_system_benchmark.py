import os
import time
import psutil
from typing import Dict, List, Any
import streamlit as st
from datetime import datetime

# 可選的繪圖依賴
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    PLOTTING_AVAILABLE = True
except ImportError:
    plt = None
    pd = None
    PLOTTING_AVAILABLE = False

# RAG 系統導入
from enhanced_rag_system import EnhancedRAGSystem

# Graph RAG 系統 - 可選導入
try:
    from graph_rag_system import GraphRAGSystem
    GRAPH_RAG_AVAILABLE = True
except ImportError:
    GraphRAGSystem = None
    GRAPH_RAG_AVAILABLE = False

try:
    from elasticsearch_rag_system import ElasticsearchRAGSystem
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

class RAGSystemBenchmark:
    """RAG 系統效能基準測試"""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process(os.getpid())
        
    def get_memory_usage(self) -> Dict[str, float]:
        """獲取記憶體使用情況"""
        memory_info = self.process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # 實際記憶體使用
            'vms_mb': memory_info.vms / 1024 / 1024,  # 虛擬記憶體使用
            'cpu_percent': self.process.cpu_percent(),
            'memory_percent': self.process.memory_percent()
        }
    
    def benchmark_system_initialization(self, system_class, system_name: str) -> Dict[str, Any]:
        """測試系統初始化效能"""
        st.info(f"🔄 測試 {system_name} 初始化...")
        
        # 記錄開始狀態
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        try:
            # 初始化系統
            if system_class == ElasticsearchRAGSystem and not ELASTICSEARCH_AVAILABLE:
                return {
                    'success': False,
                    'error': 'Elasticsearch dependencies not available'
                }
            
            system = system_class()
            
            # 記錄結束狀態
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            result = {
                'success': True,
                'initialization_time': end_time - start_time,
                'memory_before': start_memory,
                'memory_after': end_memory,
                'memory_increase': end_memory['rss_mb'] - start_memory['rss_mb'],
                'system': system
            }
            
            st.success(f"✅ {system_name} 初始化完成 - {result['initialization_time']:.2f}秒")
            return result
            
        except Exception as e:
            st.error(f"❌ {system_name} 初始化失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'initialization_time': time.time() - start_time
            }
    
    def benchmark_document_processing(self, system, documents: List, system_name: str) -> Dict[str, Any]:
        """測試文檔處理效能"""
        st.info(f"📄 測試 {system_name} 文檔處理...")
        
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        try:
            # 處理文檔
            with st.spinner(f"正在處理 {len(documents)} 個文檔..."):
                index = system.create_index(documents)
                system.setup_query_engine()
            
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            result = {
                'success': index is not None,
                'processing_time': end_time - start_time,
                'documents_count': len(documents),
                'processing_speed': len(documents) / (end_time - start_time),
                'memory_before': start_memory,
                'memory_after': end_memory,
                'memory_increase': end_memory['rss_mb'] - start_memory['rss_mb'],
                'peak_memory': end_memory['rss_mb']
            }
            
            if result['success']:
                st.success(f"✅ {system_name} 文檔處理完成")
                st.metric("處理速度", f"{result['processing_speed']:.2f} 文檔/秒")
                st.metric("記憶體增加", f"{result['memory_increase']:.1f} MB")
            else:
                st.error(f"❌ {system_name} 文檔處理失敗")
            
            return result
            
        except Exception as e:
            st.error(f"❌ {system_name} 文檔處理失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'memory_increase': self.get_memory_usage()['rss_mb'] - start_memory['rss_mb']
            }
    
    def benchmark_query_performance(self, system, test_queries: List[str], system_name: str) -> Dict[str, Any]:
        """測試查詢效能"""
        st.info(f"🔍 測試 {system_name} 查詢效能...")
        
        query_results = []
        total_start_time = time.time()
        
        for i, query in enumerate(test_queries):
            st.write(f"查詢 {i+1}/{len(test_queries)}: {query[:50]}...")
            
            start_memory = self.get_memory_usage()
            start_time = time.time()
            
            try:
                # 執行查詢
                if hasattr(system, 'query_with_graph_context'):
                    response = system.query_with_graph_context(query)
                elif hasattr(system, 'query_with_context'):
                    response = system.query_with_context(query)
                else:
                    response = system.query_engine.query(query)
                
                end_time = time.time()
                end_memory = self.get_memory_usage()
                
                query_result = {
                    'query': query,
                    'response_time': end_time - start_time,
                    'response_length': len(str(response)),
                    'memory_before': start_memory['rss_mb'],
                    'memory_after': end_memory['rss_mb'],
                    'success': True
                }
                
            except Exception as e:
                query_result = {
                    'query': query,
                    'response_time': time.time() - start_time,
                    'error': str(e),
                    'success': False
                }
            
            query_results.append(query_result)
        
        total_end_time = time.time()
        
        # 計算統計
        successful_queries = [r for r in query_results if r['success']]
        
        if successful_queries:
            avg_response_time = sum(r['response_time'] for r in successful_queries) / len(successful_queries)
            max_response_time = max(r['response_time'] for r in successful_queries)
            min_response_time = min(r['response_time'] for r in successful_queries)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        result = {
            'total_queries': len(test_queries),
            'successful_queries': len(successful_queries),
            'success_rate': len(successful_queries) / len(test_queries) * 100,
            'total_time': total_end_time - total_start_time,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'min_response_time': min_response_time,
            'queries_per_second': len(successful_queries) / (total_end_time - total_start_time),
            'query_details': query_results
        }
        
        st.success(f"✅ {system_name} 查詢測試完成")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("成功率", f"{result['success_rate']:.1f}%")
        with col2:
            st.metric("平均回應時間", f"{result['avg_response_time']:.2f}秒")
        with col3:
            st.metric("QPS", f"{result['queries_per_second']:.2f}")
        
        return result
    
    def run_full_benchmark(self, documents: List, test_queries: List[str]) -> Dict[str, Any]:
        """執行完整基準測試"""
        st.header("🚀 RAG 系統效能基準測試")
        
        systems_to_test = [
            (EnhancedRAGSystem, "Enhanced RAG"),
        ]
        
        if GRAPH_RAG_AVAILABLE:
            systems_to_test.append((GraphRAGSystem, "Graph RAG"))
        else:
            st.warning("⚠️ Graph RAG 系統不可用（依賴已禁用），跳過 Graph RAG 測試")
        
        if ELASTICSEARCH_AVAILABLE:
            systems_to_test.append((ElasticsearchRAGSystem, "Elasticsearch RAG"))
        
        benchmark_results = {}
        
        for system_class, system_name in systems_to_test:
            st.subheader(f"📊 測試 {system_name}")
            
            # 系統初始化測試
            init_result = self.benchmark_system_initialization(system_class, system_name)
            
            if not init_result['success']:
                benchmark_results[system_name] = {
                    'initialization': init_result,
                    'document_processing': {'success': False, 'skipped': True},
                    'query_performance': {'success': False, 'skipped': True}
                }
                continue
            
            system = init_result['system']
            
            # 文檔處理測試
            doc_result = self.benchmark_document_processing(system, documents, system_name)
            
            # 查詢效能測試
            if doc_result['success']:
                query_result = self.benchmark_query_performance(system, test_queries, system_name)
            else:
                query_result = {'success': False, 'skipped': True}
            
            benchmark_results[system_name] = {
                'initialization': init_result,
                'document_processing': doc_result,
                'query_performance': query_result
            }
            
            # 清理記憶體
            del system
            import gc
            gc.collect()
            
            st.markdown("---")
        
        # 生成比較報告
        self.generate_comparison_report(benchmark_results)
        
        return benchmark_results
    
    def generate_comparison_report(self, results: Dict[str, Any]):
        """生成比較報告"""
        st.header("📈 效能比較報告")
        
        # 準備數據
        systems = []
        init_times = []
        processing_times = []
        memory_usage = []
        avg_query_times = []
        success_rates = []
        
        for system_name, result in results.items():
            if result['initialization']['success']:
                systems.append(system_name)
                init_times.append(result['initialization']['initialization_time'])
                
                if result['document_processing']['success']:
                    processing_times.append(result['document_processing']['processing_time'])
                    memory_usage.append(result['document_processing']['memory_increase'])
                else:
                    processing_times.append(0)
                    memory_usage.append(0)
                
                if result['query_performance'].get('success', False):
                    avg_query_times.append(result['query_performance']['avg_response_time'])
                    success_rates.append(result['query_performance']['success_rate'])
                else:
                    avg_query_times.append(0)
                    success_rates.append(0)
        
        if not systems:
            st.warning("沒有成功的測試結果可以比較")
            return
        
        # 創建比較表格
        if PLOTTING_AVAILABLE:
            comparison_df = pd.DataFrame({
                '系統': systems,
                '初始化時間(秒)': [f"{t:.2f}" for t in init_times],
                '文檔處理時間(秒)': [f"{t:.2f}" for t in processing_times],
                '記憶體增加(MB)': [f"{m:.1f}" for m in memory_usage],
                '平均查詢時間(秒)': [f"{t:.3f}" for t in avg_query_times],
                '查詢成功率(%)': [f"{r:.1f}" for r in success_rates]
            })
            
            st.subheader("📊 效能對比表")
            st.dataframe(comparison_df)
        else:
            # 簡單的表格顯示，不依賴 pandas
            st.subheader("📊 效能對比表")
            data = []
            for i, system in enumerate(systems):
                data.append({
                    '系統': system,
                    '初始化時間(秒)': f"{init_times[i]:.2f}",
                    '文檔處理時間(秒)': f"{processing_times[i]:.2f}",
                    '記憶體增加(MB)': f"{memory_usage[i]:.1f}",
                    '平均查詢時間(秒)': f"{avg_query_times[i]:.3f}",
                    '查詢成功率(%)': f"{success_rates[i]:.1f}"
                })
            st.table(data)
        
        # 視覺化比較
        if PLOTTING_AVAILABLE and len(systems) > 1:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # 初始化時間比較
            axes[0, 0].bar(systems, init_times)
            axes[0, 0].set_title('初始化時間比較')
            axes[0, 0].set_ylabel('時間 (秒)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # 記憶體使用比較
            axes[0, 1].bar(systems, memory_usage)
            axes[0, 1].set_title('記憶體使用比較')
            axes[0, 1].set_ylabel('記憶體增加 (MB)')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # 文檔處理時間比較
            axes[1, 0].bar(systems, processing_times)
            axes[1, 0].set_title('文檔處理時間比較')
            axes[1, 0].set_ylabel('時間 (秒)')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # 查詢響應時間比較
            axes[1, 1].bar(systems, avg_query_times)
            axes[1, 1].set_title('平均查詢時間比較')
            axes[1, 1].set_ylabel('時間 (秒)')
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            st.pyplot(fig)
        elif not PLOTTING_AVAILABLE:
            st.info("📊 視覺化圖表不可用（matplotlib 未安裝），使用文字版比較")
            
            # 使用 Streamlit 內建圖表功能
            if len(systems) > 1:
                st.subheader("📈 效能指標比較")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.bar_chart({system: time for system, time in zip(systems, init_times)})
                    st.caption("初始化時間比較 (秒)")
                
                with col2:
                    st.bar_chart({system: mem for system, mem in zip(systems, memory_usage)})
                    st.caption("記憶體使用比較 (MB)")
        
        # 推薦建議
        st.subheader("💡 建議")
        
        if memory_usage:
            min_memory_idx = memory_usage.index(min(memory_usage))
            max_memory_idx = memory_usage.index(max(memory_usage))
            
            st.success(f"🏆 記憶體效率最佳: {systems[min_memory_idx]} ({memory_usage[min_memory_idx]:.1f} MB)")
            if max_memory_idx != min_memory_idx:
                st.warning(f"⚠️ 記憶體消耗最大: {systems[max_memory_idx]} ({memory_usage[max_memory_idx]:.1f} MB)")
        
        if avg_query_times:
            fastest_idx = avg_query_times.index(min([t for t in avg_query_times if t > 0]))
            st.success(f"⚡ 查詢速度最快: {systems[fastest_idx]} ({avg_query_times[fastest_idx]:.3f}秒)")
        
        # 使用場景推薦
        st.markdown("""
        ### 🎯 使用場景推薦
        
        - **Enhanced RAG**: 適合中小型文檔集合，記憶體使用適中，響應速度快
        - **Graph RAG**: 適合需要複雜關係分析的場景，但記憶體消耗較大
        - **Elasticsearch RAG**: 適合大規模文檔集合，高並發查詢，可水平擴展
        """)

def run_benchmark_app():
    """運行基準測試應用"""
    st.set_page_config(
        page_title="RAG 系統效能測試",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 RAG 系統效能基準測試")
    st.markdown("比較不同 RAG 系統的效能表現")
    
    benchmark = RAGSystemBenchmark()
    
    # 測試文檔準備
    if st.button("開始基準測試"):
        # 創建測試文檔
        test_documents = [
            "這是一個關於茶葉的測試文檔。",
            "台灣茶葉種類繁多，包括烏龍茶、包種茶等。",
            "製茶工藝對茶葉品質有重要影響。"
        ]
        
        # 創建 Document 對象
        from llama_index.core import Document
        documents = [Document(text=doc) for doc in test_documents]
        
        # 測試查詢
        test_queries = [
            "什麼是台灣茶葉？",
            "製茶工藝有哪些？",
            "烏龍茶的特色是什麼？"
        ]
        
        # 執行測試
        results = benchmark.run_full_benchmark(documents, test_queries)

if __name__ == "__main__":
    run_benchmark_app()