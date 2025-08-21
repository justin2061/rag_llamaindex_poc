#!/usr/bin/env python3
"""
Elasticsearch 向量維度分析報告
基於測試結果和 Jina v3 論文數據的綜合分析
"""

import json

def analyze_dimension_performance():
    """分析維度性能並提供建議"""
    
    print("📊 Elasticsearch 向量維度性能分析報告")
    print("=" * 60)
    
    # 基於 Jina v3 論文的性能數據
    jina_performance_data = {
        32: {'retrieval_retention': 82.9, 'sts_retention': 98.4, 'storage_reduction': 96.9},
        64: {'retrieval_retention': 92.4, 'sts_retention': 99.3, 'storage_reduction': 93.8},
        128: {'retrieval_retention': 97.3, 'sts_retention': 99.8, 'storage_reduction': 87.5},
        256: {'retrieval_retention': 99.0, 'sts_retention': 99.97, 'storage_reduction': 75.0},
        384: {'retrieval_retention': 99.4, 'sts_retention': 99.98, 'storage_reduction': 62.5},
        512: {'retrieval_retention': 99.7, 'sts_retention': 100.0, 'storage_reduction': 50.0},
        768: {'retrieval_retention': 99.8, 'sts_retention': 100.0, 'storage_reduction': 25.0},
        1024: {'retrieval_retention': 100.0, 'sts_retention': 100.0, 'storage_reduction': 0.0}
    }
    
    # 我們測試中觀察到的數據（部分）
    our_test_data = {
        128: {
            'query_time_ms': 8.5,
            'embedding_time_ms': 7609.9,
            'index_size_kb': 17.6,
            'index_creation_time_s': 0.91
        },
        256: {
            'query_time_ms': 6.0,  # 從控制台輸出估算
            'index_size_kb': 25.7,  # 從控制台輸出
            'embedding_time_ms': 4734.0
        },
        384: {
            'query_time_ms': 5.0,  # 從控制台輸出估算
            'index_size_kb': 33.8,  # 從控制台輸出
            'embedding_time_ms': 6096.0
        },
        512: {
            'query_time_ms': 5.0,  # 從控制台輸出估算
            'index_size_kb': 41.4,  # 從控制台輸出
            'embedding_time_ms': 4134.0
        }
    }
    
    print("\n📚 Jina v3 論文基準數據:")
    print("維度\t檢索性能保留\tSTS性能保留\t存儲節省")
    print("-" * 50)
    for dim in [128, 256, 384, 512, 768, 1024]:
        data = jina_performance_data[dim]
        print(f"{dim}\t{data['retrieval_retention']:.1f}%\t\t{data['sts_retention']:.1f}%\t\t{data['storage_reduction']:.1f}%")
    
    print(f"\n🔬 我們的測試數據:")
    print("維度\t查詢時間\t嵌入時間\t索引大小")
    print("-" * 45)
    for dim in [128, 256, 384, 512]:
        if dim in our_test_data:
            data = our_test_data[dim]
            embed_time_s = data['embedding_time_ms'] / 1000
            print(f"{dim}\t{data['query_time_ms']:.1f}ms\t\t{embed_time_s:.1f}s\t\t{data['index_size_kb']:.1f}KB")
    
    print(f"\n💡 綜合分析和建議:")
    print("-" * 30)
    
    print(f"\n1. 🚀 查詢性能 (Query Performance):")
    print(f"   - 所有測試維度的查詢時間都在 5-8.5ms 範圍內")
    print(f"   - 維度對查詢速度的影響很小")
    print(f"   - 較低維度 (128-256) 稍微更快")
    
    print(f"\n2. 💾 存儲效率 (Storage Efficiency):")
    print(f"   - 128維度: 17.6KB (最小存儲)")
    print(f"   - 256維度: 25.7KB (75%存儲節省)")
    print(f"   - 384維度: 33.8KB (62.5%存儲節省)")
    print(f"   - 512維度: 41.4KB (50%存儲節省)")
    
    print(f"\n3. 🎯 準確性保留 (Accuracy Retention):")
    print(f"   - 256維度: 保留99.0%檢索性能，99.97% STS性能")
    print(f"   - 384維度: 保留99.4%檢索性能，99.98% STS性能")
    print(f"   - 512維度: 保留99.7%檢索性能，100% STS性能")
    
    print(f"\n4. ⚖️ 生產環境建議:")
    
    # 計算效率分數
    efficiency_scores = {}
    for dim in [256, 384, 512]:
        if dim in our_test_data and dim in jina_performance_data:
            # 權重：準確性(50%) + 查詢速度(30%) + 存儲效率(20%)
            accuracy_score = jina_performance_data[dim]['retrieval_retention']
            speed_score = 100 - (our_test_data[dim]['query_time_ms'] - 5)  # 基準5ms
            storage_score = jina_performance_data[dim]['storage_reduction']
            
            efficiency_score = (accuracy_score * 0.5) + (speed_score * 0.3) + (storage_score * 0.2)
            efficiency_scores[dim] = efficiency_score
    
    # 排序推薦
    sorted_dims = sorted(efficiency_scores.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n   排名 | 維度 | 效率分數 | 使用場景")
    print(f"   -----|------|----------|----------")
    
    scenarios = {
        256: "高QPS、存儲受限環境",
        384: "平衡性能與存儲（推薦）",
        512: "高準確性要求環境"
    }
    
    for i, (dim, score) in enumerate(sorted_dims, 1):
        scenario = scenarios.get(dim, "")
        print(f"   {i}    | {dim}  | {score:.1f}     | {scenario}")
    
    print(f"\n🎯 最終推薦:")
    if sorted_dims:
        best_dim = sorted_dims[0][0]
        print(f"   推薦維度: {best_dim}")
        
        if best_dim == 256:
            print(f"   理由: 最佳存儲效率，僅損失1%檢索性能")
        elif best_dim == 384:
            print(f"   理由: 性能與存儲的最佳平衡點")
        elif best_dim == 512:
            print(f"   理由: 接近完美的檢索性能")
    
    print(f"\n📝 實施建議:")
    print(f"   1. 從384維度開始（當前配置）")
    print(f"   2. 根據實際業務需求調整：")
    print(f"      - 存儲成本敏感 → 256維度")
    print(f"      - 準確性要求極高 → 512維度")
    print(f"   3. 可以隨時通過環境變數調整")
    print(f"   4. 建議在生產環境測試不同維度的實際效果")
    
    print(f"\n⚠️ 注意事項:")
    print(f"   - 變更維度需要重建索引")
    print(f"   - 不同維度的嵌入不兼容")
    print(f"   - 建議在低峰期進行維度調整")

if __name__ == "__main__":
    analyze_dimension_performance()