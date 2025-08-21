#!/usr/bin/env python3
"""
Elasticsearch 向量維度基準測試（修正版）
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

def test_single_dimension(dimension: int, test_queries: List[str]) -> Dict[str, Any]:
    """測試單個維度的性能
    
    Args:
        dimension: 要測試的維度
        test_queries: 測試查詢列表
        
    Returns:
        Dict: 該維度的測試結果
    """
    print(f"\n🔧 測試維度: {dimension}")
    
    try:
        # 直接創建指定維度的 embedding 模型
        from src.utils.embedding_fix import SafeJinaEmbedding
        
        api_key = os.getenv("JINA_API_KEY")
        embedding_model = SafeJinaEmbedding(
            api_key=api_key,
            model="jina-embeddings-v3",
            task="text-matching",
            dimensions=dimension
        )
        
        if not embedding_model.use_api:
            print(f"⚠️ API 不可用，跳過維度 {dimension}")
            return {'error': 'API not available'}
        
        # 測試嵌入生成速度
        embed_start = time.time()
        test_embeddings = []
        for query in test_queries:
            embed = embedding_model.get_text_embedding(query)
            test_embeddings.append(embed)
        embed_time = time.time() - embed_start
        
        # 驗證維度
        actual_dim = len(test_embeddings[0]) if test_embeddings else 0
        if actual_dim != dimension:
            print(f"❌ 維度不匹配: 請求 {dimension}, 實際 {actual_dim}")
            return {'error': f'Dimension mismatch: expected {dimension}, got {actual_dim}'}
        
        print(f"✅ 嵌入生成完成: {len(test_queries)} 查詢, 維度: {actual_dim}")
        print(f"⏱️ 嵌入生成時間: {embed_time:.3f}s ({embed_time/len(test_queries):.3f}s/query)")
        
        # 測試 Elasticsearch 索引創建
        from elasticsearch import Elasticsearch
        es_client = Elasticsearch([{'host': 'elasticsearch', 'port': 9200, 'scheme': 'http'}])
        
        if not es_client.ping():
            print(f"❌ 無法連接到 Elasticsearch")
            return {'error': 'Cannot connect to Elasticsearch'}
        
        # 創建測試索引的 mapping
        test_index = f"dimension_test_{dimension}"
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "chinese_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "cjk_width", "cjk_bigram"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "content": {
                        "type": "text",
                        "analyzer": "chinese_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": dimension,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                        "ignore_above": 256
                                    }
                                }
                            },
                            "timestamp": {
                                "type": "date"
                            }
                        }
                    }
                }
            }
        }
        
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
        
        # 測試查詢性能（多次測試取平均值）
        query_times = []
        for query, query_embedding in zip(test_queries, test_embeddings):
            # 每個查詢測試3次取平均值
            times = []
            for _ in range(3):
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
                times.append(query_time)
            
            avg_time = sum(times) / len(times)
            query_times.append(avg_time)
        
        avg_query_time = sum(query_times) / len(query_times)
        print(f"⏱️ 平均查詢時間: {avg_query_time:.3f}s")
        
        # 獲取索引統計
        stats = es_client.indices.stats(index=test_index)
        index_size = stats['indices'][test_index]['total']['store']['size_in_bytes']
        
        print(f"📊 索引大小: {index_size / 1024:.2f} KB")
        
        # 清理測試索引
        es_client.indices.delete(index=test_index)
        print(f"🗑️ 已清理測試索引: {test_index}")
        
        return {
            'dimension': dimension,
            'actual_dimension': actual_dim,
            'embedding_time_total': embed_time,
            'embedding_time_per_query': embed_time / len(test_queries),
            'index_creation_time': index_time,
            'document_indexing_time': docs_time,
            'document_indexing_time_per_doc': docs_time / len(test_queries),
            'average_query_time': avg_query_time,
            'index_size_bytes': index_size,
            'index_size_kb': index_size / 1024,
            'queries_tested': len(test_queries)
        }
        
    except Exception as e:
        print(f"❌ 維度 {dimension} 測試失敗: {str(e)}")
        return {'error': str(e)}

def main():
    """主函數"""
    print("🚀 開始 Elasticsearch 向量維度性能基準測試（修正版）")
    
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
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_queries': test_queries,
        'dimension_results': {}
    }
    
    for dim in test_dimensions:
        result = test_single_dimension(dim, test_queries)
        results['dimension_results'][dim] = result
        
        # 在每個測試之間稍作暫停
        time.sleep(2)
    
    # 保存結果
    results_file = "data/dimension_benchmark_results.json"
    os.makedirs("data", exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 測試結果已保存到: {results_file}")
    
    # 分析結果
    print("\n📊 性能分析摘要:")
    print("維度\t嵌入時間\t查詢時間\t索引大小\t效率分數")
    print("-" * 60)
    
    valid_results = {}
    for dim, result in results['dimension_results'].items():
        if 'error' not in result:
            embed_time = result['embedding_time_per_query'] * 1000  # 轉換為毫秒
            query_time = result['average_query_time'] * 1000        # 轉換為毫秒
            index_size = result['index_size_kb']
            
            # 計算效率分數（越低越好）
            # 結合查詢時間和存儲大小
            efficiency_score = (query_time * 0.7) + (index_size * 0.3)
            
            print(f"{dim}\t{embed_time:.1f}ms\t\t{query_time:.1f}ms\t\t{index_size:.1f}KB\t\t{efficiency_score:.1f}")
            
            valid_results[dim] = {
                'embed_time': embed_time,
                'query_time': query_time,
                'index_size': index_size,
                'efficiency_score': efficiency_score
            }
        else:
            print(f"{dim}\t錯誤: {result['error']}")
    
    # 推薦最佳維度
    print("\n💡 基於測試結果的建議:")
    
    if valid_results:
        # 找出查詢速度最快的維度
        fastest_query = min(valid_results.items(), key=lambda x: x[1]['query_time'])
        
        # 找出存儲效率最佳的維度
        smallest_index = min(valid_results.items(), key=lambda x: x[1]['index_size'])
        
        # 找出整體效率最佳的維度
        most_efficient = min(valid_results.items(), key=lambda x: x[1]['efficiency_score'])
        
        print(f"🚀 查詢速度最快: {fastest_query[0]} 維度 ({fastest_query[1]['query_time']:.1f}ms)")
        print(f"💾 存儲效率最佳: {smallest_index[0]} 維度 ({smallest_index[1]['index_size']:.1f}KB)")
        print(f"⚖️ 整體效率最佳: {most_efficient[0]} 維度 (效率分數: {most_efficient[1]['efficiency_score']:.1f})")
        
        # 基於論文結果的建議
        print(f"\n📚 基於 Jina v3 論文的建議:")
        print(f"   - 256 維度: 保留 99.37% 性能，存儲減少 75%")
        print(f"   - 384 維度: 平衡推薦，性能和存儲的良好平衡")
        print(f"   - 512 維度: 保留 99.81% 性能，存儲減少 50%")
        
        # 根據測試結果推薦
        if 384 in valid_results and 256 in valid_results:
            score_384 = valid_results[384]['efficiency_score']
            score_256 = valid_results[256]['efficiency_score']
            
            if abs(score_384 - score_256) < 5:  # 如果分數相近
                print(f"\n🎯 最終推薦: 384 維度")
                print(f"   理由: 在性能和存儲之間提供最佳平衡")
            elif score_256 < score_384:
                print(f"\n🎯 最終推薦: 256 維度")
                print(f"   理由: 更好的存儲效率，性能損失minimal")
            else:
                print(f"\n🎯 最終推薦: 384 維度")
                print(f"   理由: 更好的查詢性能")

if __name__ == "__main__":
    main()