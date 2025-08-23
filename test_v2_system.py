#!/usr/bin/env python3
"""
Enhanced RAG System V2.0 測試腳本
測試所有Phase 1-3優化功能的效果
"""

import requests
import json
import time
from datetime import datetime

# API配置
API_BASE_URL = "http://localhost:8003"
DEMO_API_KEY = "demo-api-key-123"

def get_jwt_token():
    """獲取JWT Token"""
    response = requests.post(f"{API_BASE_URL}/auth/token", 
                           json={"api_key": DEMO_API_KEY})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Token獲取失敗: {response.text}")
        return None

def test_health():
    """測試健康狀態"""
    print("🏥 測試系統健康狀態...")
    response = requests.get(f"{API_BASE_URL}/health")
    
    if response.status_code == 200:
        health_data = response.json()
        print("✅ 系統健康狀態良好")
        print(f"   - API版本: {health_data.get('api_version', 'unknown')}")
        print(f"   - 總文檔數: {health_data.get('total_documents', 0)}")
        print(f"   - Elasticsearch: {'已連接' if health_data.get('elasticsearch_connected') else '未連接'}")
        return True
    else:
        print(f"❌ 系統健康檢查失敗: {response.status_code}")
        return False

def test_v2_chat(token, questions):
    """測試V2.0聊天功能"""
    print("\n🧠 測試Enhanced RAG V2.0智能問答...")
    
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 測試查詢 {i}: {question}")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/chat",
            headers=headers,
            json={
                "question": question,
                "include_sources": True,
                "max_sources": 3
            }
        )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ 查詢成功 (耗時: {duration:.3f}秒)")
            print(f"   - 回答長度: {len(data['answer'])} 字符")
            print(f"   - 來源數量: {len(data['sources'])}")
            
            # 分析優化使用情況
            metadata = data.get('metadata', {})
            optimization_used = metadata.get('optimization_used', [])
            if optimization_used:
                print(f"   - 使用優化: {', '.join(optimization_used)}")
            
            # 顯示性能指標
            performance = metadata.get('performance', {})
            if performance:
                print(f"   - 處理階段: {performance.get('total_stages', 0)} 個")
                for stage in performance.get('stages', []):
                    print(f"     * {stage['stage']}: {stage['duration']:.3f}秒")
            
            # 顯示回答預覽
            answer_preview = data['answer'][:150] + "..." if len(data['answer']) > 150 else data['answer']
            print(f"   - 回答預覽: {answer_preview}")
            
            results.append({
                "question": question,
                "success": True,
                "duration": duration,
                "sources_count": len(data['sources']),
                "optimization_used": optimization_used,
                "answer_length": len(data['answer'])
            })
        else:
            print(f"❌ 查詢失敗: {response.status_code}")
            print(f"   錯誤信息: {response.text}")
            
            results.append({
                "question": question,
                "success": False,
                "error": response.text
            })
    
    return results

def analyze_results(results):
    """分析測試結果"""
    print("\n📊 測試結果分析")
    print("="*50)
    
    successful = [r for r in results if r.get('success', False)]
    total_queries = len(results)
    
    print(f"總查詢數: {total_queries}")
    print(f"成功查詢: {len(successful)}")
    print(f"成功率: {len(successful)/total_queries*100:.1f}%")
    
    if successful:
        durations = [r['duration'] for r in successful]
        sources_counts = [r['sources_count'] for r in successful]
        answer_lengths = [r['answer_length'] for r in successful]
        
        print(f"\n⏱️ 性能指標:")
        print(f"   - 平均響應時間: {sum(durations)/len(durations):.3f}秒")
        print(f"   - 最快響應: {min(durations):.3f}秒")
        print(f"   - 最慢響應: {max(durations):.3f}秒")
        
        print(f"\n📚 內容指標:")
        print(f"   - 平均來源數: {sum(sources_counts)/len(sources_counts):.1f}")
        print(f"   - 平均回答長度: {sum(answer_lengths)/len(answer_lengths):.0f} 字符")
        
        # 統計優化功能使用
        all_optimizations = []
        for r in successful:
            all_optimizations.extend(r.get('optimization_used', []))
        
        if all_optimizations:
            from collections import Counter
            opt_counter = Counter(all_optimizations)
            print(f"\n🎯 優化功能使用統計:")
            for opt, count in opt_counter.most_common():
                print(f"   - {opt}: {count}次 ({count/len(successful)*100:.1f}%)")

def main():
    """主測試流程"""
    print("🚀 Enhanced RAG System V2.0 測試開始")
    print("="*60)
    
    # 1. 健康檢查
    if not test_health():
        print("❌ 系統不健康，終止測試")
        return
    
    # 2. 獲取Token
    print("\n🔑 獲取API Token...")
    token = get_jwt_token()
    if not token:
        print("❌ Token獲取失敗，終止測試")
        return
    print("✅ Token獲取成功")
    
    # 3. 準備測試查詢
    test_questions = [
        "你好，請介紹一下你的功能",
        "蘇聯專家的大玩笑這篇文章的內容是什麼？",
        "這個系統有哪些優化功能？",
        "機器學習和深度學習的區別是什麼？",
        "請解釋一下RAG系統的工作原理"
    ]
    
    # 4. 執行V2.0聊天測試
    results = test_v2_chat(token, test_questions)
    
    # 5. 分析結果
    analyze_results(results)
    
    print("\n🎉 測試完成！")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()