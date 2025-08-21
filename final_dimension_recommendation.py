#!/usr/bin/env python3
"""
最終維度推薦報告
基於完整測試數據的詳細分析
"""

import json

def load_test_results():
    """載入測試結果"""
    with open('data/dimension_benchmark_results.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_complete_results():
    """分析完整測試結果"""
    
    print("🎯 Elasticsearch 向量維度最終推薦報告")
    print("=" * 60)
    
    # 載入我們的測試數據
    results = load_test_results()
    test_data = results['dimension_results']
    
    # Jina v3 論文數據
    jina_data = {
        128: {'retrieval_retention': 97.3, 'sts_retention': 99.8},
        256: {'retrieval_retention': 99.0, 'sts_retention': 99.97},
        384: {'retrieval_retention': 99.4, 'sts_retention': 99.98},
        512: {'retrieval_retention': 99.7, 'sts_retention': 100.0},
        768: {'retrieval_retention': 99.8, 'sts_retention': 100.0},
        1024: {'retrieval_retention': 100.0, 'sts_retention': 100.0}
    }
    
    print(f"\n📊 完整測試結果對比:")
    print("維度\t查詢時間\t嵌入時間\t索引大小\t檢索性能\t存儲效率")
    print("-" * 75)
    
    performance_analysis = {}
    
    for dim_str, data in test_data.items():
        if 'error' in data:
            continue
            
        dim = int(dim_str)
        query_time = data['average_query_time'] * 1000  # 轉為 ms
        embed_time = data['embedding_time_per_query']   # 已是 s
        index_size = data['index_size_kb']
        
        # 計算存儲效率 (相對於1024維度)
        storage_efficiency = (1 - index_size / test_data['1024']['index_size_kb']) * 100
        
        # 獲取準確性數據
        accuracy = jina_data.get(dim, {}).get('retrieval_retention', 0)
        
        print(f"{dim}\t{query_time:.1f}ms\t\t{embed_time:.1f}s\t\t{index_size:.1f}KB\t\t{accuracy:.1f}%\t\t{storage_efficiency:.1f}%")
        
        # 計算綜合分數
        # 權重：準確性(40%) + 查詢速度(30%) + 存儲效率(20%) + 嵌入速度(10%)
        speed_score = max(0, 100 - (query_time - 3) * 10)  # 以3ms為基準
        embed_speed_score = max(0, 100 - (embed_time - 3) * 5)  # 以3s為基準
        
        total_score = (accuracy * 0.4) + (speed_score * 0.3) + (storage_efficiency * 0.2) + (embed_speed_score * 0.1)
        
        performance_analysis[dim] = {
            'query_time': query_time,
            'embed_time': embed_time,
            'index_size': index_size,
            'accuracy': accuracy,
            'storage_efficiency': storage_efficiency,
            'total_score': total_score
        }
    
    # 排序分析
    sorted_performance = sorted(performance_analysis.items(), key=lambda x: x[1]['total_score'], reverse=True)
    
    print(f"\n🏆 綜合排名:")
    print("排名\t維度\t綜合分數\t主要優勢")
    print("-" * 50)
    
    advantages = {
        128: "存儲最小, 查詢略慢",
        256: "存儲效率高, 性能均衡", 
        384: "當前配置, 平衡推薦",
        512: "高準確性, 適中存儲",
        768: "接近完美準確性",
        1024: "最高準確性, 存儲最大"
    }
    
    for i, (dim, perf) in enumerate(sorted_performance, 1):
        advantage = advantages.get(dim, "")
        print(f"{i}\t{dim}\t{perf['total_score']:.1f}\t\t{advantage}")
    
    # 詳細建議
    print(f"\n💡 詳細使用場景建議:")
    print("-" * 40)
    
    # 找出最佳性能的維度
    best_overall = sorted_performance[0][0]
    best_query_speed = min(performance_analysis.items(), key=lambda x: x[1]['query_time'])[0]
    best_storage = max(performance_analysis.items(), key=lambda x: x[1]['storage_efficiency'])[0]
    best_accuracy = max(performance_analysis.items(), key=lambda x: x[1]['accuracy'])[0]
    
    print(f"\n1. 🚀 最佳整體性能: {best_overall} 維度")
    print(f"   - 綜合分數: {performance_analysis[best_overall]['total_score']:.1f}")
    print(f"   - 查詢時間: {performance_analysis[best_overall]['query_time']:.1f}ms")
    print(f"   - 準確性: {performance_analysis[best_overall]['accuracy']:.1f}%")
    
    print(f"\n2. ⚡ 最快查詢速度: {best_query_speed} 維度")
    print(f"   - 查詢時間: {performance_analysis[best_query_speed]['query_time']:.1f}ms")
    
    print(f"\n3. 💾 最佳存儲效率: {best_storage} 維度")
    print(f"   - 存儲節省: {performance_analysis[best_storage]['storage_efficiency']:.1f}%")
    print(f"   - 索引大小: {performance_analysis[best_storage]['index_size']:.1f}KB")
    
    print(f"\n4. 🎯 最高準確性: {best_accuracy} 維度")
    print(f"   - 檢索性能: {performance_analysis[best_accuracy]['accuracy']:.1f}%")
    
    print(f"\n📋 實際部署建議:")
    print("-" * 25)
    
    print(f"\n🎯 推薦配置優先順序:")
    
    # 基於不同需求的推薦
    recommendations = [
        (256, "存儲成本敏感環境", "75%存儲節省，僅1%性能損失"),
        (384, "平衡生產環境（當前）", "62.5%存儲節省，高性能保留"),
        (512, "高準確性要求", "50%存儲節省，接近完美性能"),
        (1024, "極高準確性要求", "完美性能，存儲成本較高")
    ]
    
    for i, (dim, scenario, desc) in enumerate(recommendations, 1):
        current_marker = " (當前配置)" if dim == 384 else ""
        print(f"\n{i}. {dim} 維度{current_marker}")
        print(f"   適用: {scenario}")
        print(f"   特點: {desc}")
        if dim in performance_analysis:
            perf = performance_analysis[dim]
            print(f"   性能: 查詢{perf['query_time']:.1f}ms | 準確性{perf['accuracy']:.1f}% | 存儲{perf['index_size']:.1f}KB")
    
    print(f"\n🔧 配置變更指南:")
    print(f"   1. 修改 .env 文件中的 ELASTICSEARCH_VECTOR_DIMENSION")
    print(f"   2. 重啟 Elasticsearch 服務")
    print(f"   3. 重新創建索引（會觸發自動 mapping 創建）")
    print(f"   4. 重新索引所有文檔")
    
    print(f"\n⚠️ 重要提醒:")
    print(f"   - 不同維度的嵌入向量不兼容")
    print(f"   - 變更維度需要完全重建索引")
    print(f"   - 建議在維護窗口期間進行變更")
    print(f"   - 可以先在測試環境驗證效果")
    
    # 最終推薦
    print(f"\n🎯 最終推薦: {sorted_performance[0][0]} 維度")
    final_perf = performance_analysis[sorted_performance[0][0]]
    print(f"   理由: 綜合考慮準確性、速度和存儲的最佳平衡")
    print(f"   預期效果:")
    print(f"     • 查詢延遲: {final_perf['query_time']:.1f}ms")
    print(f"     • 檢索準確性: {final_perf['accuracy']:.1f}%")
    print(f"     • 存儲節省: {final_perf['storage_efficiency']:.1f}%")
    
    # 如果當前不是最佳配置，提供升級建議
    if 384 != sorted_performance[0][0]:
        print(f"\n📈 升級建議:")
        print(f"   當前 384 維度 → 推薦 {sorted_performance[0][0]} 維度")
        current_perf = performance_analysis[384]
        best_perf = performance_analysis[sorted_performance[0][0]]
        
        query_improvement = current_perf['query_time'] - best_perf['query_time']
        storage_improvement = best_perf['storage_efficiency'] - current_perf['storage_efficiency']
        
        if query_improvement > 0:
            print(f"   查詢速度提升: {query_improvement:.1f}ms")
        if storage_improvement > 0:
            print(f"   存儲效率提升: {storage_improvement:.1f}%")

if __name__ == "__main__":
    analyze_complete_results()