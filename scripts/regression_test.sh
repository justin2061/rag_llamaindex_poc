#!/bin/bash

# RAG 系統回歸測試腳本
# 用於確保修改後系統核心功能仍然正常工作

set -e  # 遇到錯誤立即退出

echo "🧪 RAG 系統回歸測試開始..."
echo "時間: $(date)"
echo "分支: $(git branch --show-current 2>/dev/null || echo 'unknown')"
echo "提交: $(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="

# 檢查容器狀態
echo "📦 檢查容器狀態..."
if ! docker ps --filter "name=rag-intelligent-assistant" --format "{{.Names}}" | grep -q "rag-intelligent-assistant"; then
    echo "❌ rag-intelligent-assistant 容器未運行"
    echo "請先啟動容器: docker-compose up -d"
    exit 1
fi

if ! docker ps --filter "name=rag-elasticsearch" --format "{{.Names}}" | grep -q "rag-elasticsearch"; then
    echo "❌ rag-elasticsearch 容器未運行"
    echo "請先啟動容器: docker-compose up -d"
    exit 1
fi

echo "✅ 容器狀態正常"

# 執行核心功能測試
echo ""
echo "🔧 執行核心功能測試..."

docker exec rag-intelligent-assistant python -c "
import sys
sys.path.append('/app')

print('測試 1/5: 系統初始化...')
try:
    from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
    rag = ElasticsearchRAGSystem()
    print('✅ 系統初始化正常')
except Exception as e:
    print(f'❌ 系統初始化失敗: {e}')
    exit(1)

print('測試 2/5: 統計功能...')
try:
    stats = rag.get_document_statistics()
    doc_count = stats.get('total_documents', 0)
    print(f'✅ 統計功能正常: {doc_count} 個文檔')
except Exception as e:
    print(f'❌ 統計功能失敗: {e}')
    exit(1)

print('測試 3/5: 關鍵屬性檢查...')
try:
    assert hasattr(rag, 'memory_stats'), 'memory_stats 屬性缺失'
    assert hasattr(rag, 'elasticsearch_client'), 'elasticsearch_client 屬性缺失'
    assert hasattr(rag, 'system_status'), 'system_status 屬性缺失'
    print('✅ 關鍵屬性檢查通過')
except Exception as e:
    print(f'❌ 屬性檢查失敗: {e}')
    exit(1)

print('測試 4/5: 系統狀態功能...')
try:
    status = rag.get_system_status()
    print(f'✅ 系統狀態功能正常: {len(status)} 個狀態項')
except Exception as e:
    print(f'❌ 系統狀態功能失敗: {e}')
    exit(1)

print('測試 5/5: Elasticsearch 連接...')
try:
    if hasattr(rag, 'elasticsearch_client') and rag.elasticsearch_client:
        if rag.elasticsearch_client.ping():
            print('✅ Elasticsearch 連接正常')
        else:
            print('❌ Elasticsearch 連接失敗')
            exit(1)
    else:
        print('❌ Elasticsearch 客戶端未初始化')
        exit(1)
except Exception as e:
    print(f'❌ Elasticsearch 連接測試失敗: {e}')
    exit(1)

print('')
print('🎉 所有核心功能測試通過！')
"

# 檢查 Web 界面可訪問性
echo ""
echo "🌐 檢查 Web 界面..."
if curl -s http://localhost:8602 > /dev/null; then
    echo "✅ Dashboard 可訪問 (http://localhost:8602)"
else
    echo "❌ Dashboard 無法訪問"
    exit 1
fi

# 生成測試報告
echo ""
echo "📊 回歸測試報告"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo "✅ 所有回歸測試通過！"
echo "時間: $(date)"
echo "系統狀態: 正常"
echo ""
echo "💡 如果最近進行了重大修改，建議執行:"
echo "   ./scripts/full_restart_test.sh"
echo ""

# 記錄測試結果
echo "$(date): 回歸測試通過 - 分支: $(git branch --show-current 2>/dev/null || echo 'unknown')" >> test_history.log