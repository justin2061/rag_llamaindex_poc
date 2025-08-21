#!/usr/bin/env python3
"""
Elasticsearch 向量維度基準測試
測試不同維度下的查詢速度和準確性
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_dimension_performance(dimensions: List[int], test_queries: List[str]) -> Dict[str, Any]:
    """測試不同維度下的性能
    
    Args:
        dimensions: 要測試的維度列表
        test_queries: 測試查詢列表
        
    Returns:
        Dict: 性能測試結果
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_queries': test_queries,
        'dimension_results': {}
    }
    
    for dim in dimensions:
        print(f"\n🔧 測試維度: {dim}")
        
        try:
            # 設置測試維度
            os.environ['ELASTICSEARCH_VECTOR_DIMENSION'] = str(dim)
            
            # 重新加載配置
            import importlib
            import config.config
            importlib.reload(config.config)
            
            # 創建測試索引名稱
            test_index = f"dimension_test_{dim}"
            
            # 測試嵌入生成速度
            embed_start = time.time()
            from src.utils.embedding_fix import setup_safe_embedding
            embedding_model = setup_safe_embedding()
            
            # 生成測試嵌入
            test_embeddings = []
            for query in test_queries:
                embed = embedding_model.get_text_embedding(query)
                test_embeddings.append(embed)
            
            embed_time = time.time() - embed_start
            
            # 驗證維度
            actual_dim = len(test_embeddings[0]) if test_embeddings else 0
            
            print(f"✅ 嵌入生成完成: {len(test_queries)} 查詢, 實際維度: {actual_dim}")
            print(f"⏱️ 嵌入生成時間: {embed_time:.3f}s ({embed_time/len(test_queries):.3f}s/query)")
            
            # 測試 Elasticsearch 索引創建
            from elasticsearch import Elasticsearch
            es_client = Elasticsearch([{'host': 'elasticsearch', 'port': 9200, 'scheme': 'http'}])
            
            if not es_client.ping():
                print(f"❌ 無法連接到 Elasticsearch")
                continue
            
            # 創建測試索引的 mapping
            from config.elasticsearch.mapping_loader import ElasticsearchMappingLoader
            loader = ElasticsearchMappingLoader()
            
            variables = {
                'SHARDS': 1,
                'REPLICAS': 0,
                'DIMENSION': dim,
                'SIMILARITY': 'cosine'
            }
            
            mapping = loader.load_mapping(**variables)
            
            # 刪除舊測試索引（如果存在）
            if es_client.indices.exists(index=test_index):
                es_client.indices.delete(index=test_index)
            
            # 創建測試索引
            index_start = time.time()
            es_client.indices.create(index=test_index, body=mapping)
            index_time = time.time() - index_start
            
            print(f"⏱️ 索引創建時間: {index_time:.3f}s")
            
            # 索引一些測試文檔
            docs_start = time.time()
            for i, (query, embedding) in enumerate(zip(test_queries, test_embeddings)):
                doc = {
                    'content': f"測試文檔 {i+1}: {query}",
                    'embedding': embedding,
                    'metadata': {
                        'source': f'test_doc_{i+1}',
                        'timestamp': datetime.now().isoformat()
                    }
                }
                es_client.index(index=test_index, document=doc)
            
            # 刷新索引
            es_client.indices.refresh(index=test_index)
            docs_time = time.time() - docs_start
            
            print(f"⏱️ 文檔索引時間: {docs_time:.3f}s ({docs_time/len(test_queries):.3f}s/doc)")
            
            # 測試查詢性能
            query_times = []
            for query, query_embedding in zip(test_queries, test_embeddings):
                query_start = time.time()
                
                search_query = {
                    "size": 5,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": query_embedding}
                            }
                        }
                    }
                }
                
                response = es_client.search(index=test_index, body=search_query)
                query_time = time.time() - query_start
                query_times.append(query_time)
            
            avg_query_time = sum(query_times) / len(query_times)
            print(f"⏱️ 平均查詢時間: {avg_query_time:.3f}s")
            
            # 獲取索引統計
            stats = es_client.indices.stats(index=test_index)
            index_size = stats['indices'][test_index]['total']['store']['size_in_bytes']
            
            print(f"📊 索引大小: {index_size / 1024:.2f} KB")
            
            # 記錄結果
            results['dimension_results'][dim] = {
                'actual_dimension': actual_dim,
                'embedding_time_total': embed_time,
                'embedding_time_per_query': embed_time / len(test_queries),
                'index_creation_time': index_time,
                'document_indexing_time': docs_time,
                'document_indexing_time_per_doc': docs_time / len(test_queries),
                'average_query_time': avg_query_time,
                'index_size_bytes': index_size,
                'index_size_kb': index_size / 1024
            }
            
            # 清理測試索引
            es_client.indices.delete(index=test_index)
            print(f"🗑️ 已清理測試索引: {test_index}")
            
        except Exception as e:
            print(f"❌ 維度 {dim} 測試失敗: {str(e)}")
            results['dimension_results'][dim] = {
                'error': str(e)
            }
    
    return results

def main():
    """主函數"""
    print("🚀 開始 Elasticsearch 向量維度性能基準測試")
    
    # 測試維度（根據 Jina v3 的 MRL 支持）
    test_dimensions = [128, 256, 384, 512, 768, 1024]
    
    # 測試查詢
    test_queries = [
        "什麼是機器學習？",
        "如何優化數據庫性能？",
        "Python 程式設計最佳實踐",
        "雲端運算的優勢和挑戰",
        "人工智能在醫療領域的應用"
    ]
    
    print(f"📋 測試維度: {test_dimensions}")
    print(f"📋 測試查詢數量: {len(test_queries)}")
    
    # 執行測試
    results = test_dimension_performance(test_dimensions, test_queries)
    
    # 保存結果
    results_file = "data/dimension_benchmark_results.json"
    os.makedirs("data", exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 測試結果已保存到: {results_file}")
    
    # 分析結果
    print("\n📊 性能分析摘要:")
    print("維度\t嵌入時間\t查詢時間\t索引大小")
    print("-" * 50)
    
    for dim, result in results['dimension_results'].items():
        if 'error' not in result:
            embed_time = result['embedding_time_per_query'] * 1000  # 轉換為毫秒
            query_time = result['average_query_time'] * 1000        # 轉換為毫秒
            index_size = result['index_size_kb']
            
            print(f"{dim}\t{embed_time:.1f}ms\t\t{query_time:.1f}ms\t\t{index_size:.1f}KB")
        else:
            print(f"{dim}\t錯誤: {result['error']}")
    
    # 推薦最佳維度
    print("\n💡 基於測試結果的建議:")
    
    valid_results = {dim: result for dim, result in results['dimension_results'].items() 
                    if 'error' not in result}
    
    if valid_results:
        # 找出查詢速度最快的維度
        fastest_query = min(valid_results.items(), 
                          key=lambda x: x[1]['average_query_time'])
        
        # 找出索引大小最小的維度
        smallest_index = min(valid_results.items(), 
                           key=lambda x: x[1]['index_size_bytes'])
        
        print(f"🚀 查詢速度最快: {fastest_query[0]} 維度 ({fastest_query[1]['average_query_time']*1000:.1f}ms)")
        print(f"💾 存儲效率最佳: {smallest_index[0]} 維度 ({smallest_index[1]['index_size_kb']:.1f}KB)")
        
        # 平衡建議
        if len(valid_results) >= 3:
            # 選擇中等維度作為平衡推薦
            dimensions_sorted = sorted(valid_results.keys())
            balanced_dim = dimensions_sorted[len(dimensions_sorted)//2]
            print(f"⚖️ 平衡推薦: {balanced_dim} 維度（性能與存儲的平衡）")

if __name__ == "__main__":
    main()