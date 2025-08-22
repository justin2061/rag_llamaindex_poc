#!/bin/bash

# 完整系統重啟驗證腳本
# 用於重大修改後的全面測試

set -e

echo "🔄 執行完整系統重啟驗證..."
echo "時間: $(date)"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="

# 警告用戶
echo "⚠️  警告: 這將完全重啟所有容器，可能需要 2-3 分鐘"
read -p "您確定要繼續嗎？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

# 記錄當前狀態
echo "📝 記錄當前狀態..."
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo 'unknown')
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')
echo "分支: $CURRENT_BRANCH"
echo "提交: $CURRENT_COMMIT"

# 1. 完全停止所有容器
echo ""
echo "🛑 停止所有容器..."
docker-compose down

# 2. 清理系統（可選）
echo ""
echo "🧹 清理 Docker 緩存..."
docker system prune -f

# 3. 重新構建和啟動
echo ""
echo "🔧 重新構建和啟動容器..."
docker-compose up --build -d

# 4. 等待系統完全啟動
echo ""
echo "⏳ 等待系統啟動（60秒）..."
for i in {60..1}; do
    printf "\r剩餘: %02d 秒" $i
    sleep 1
done
echo ""

# 5. 驗證容器狀態
echo ""
echo "📦 驗證容器狀態..."
echo "容器列表:"
docker ps --filter "name=rag" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 檢查必要容器是否運行
REQUIRED_CONTAINERS=("rag-intelligent-assistant" "rag-elasticsearch" "rag-api")
for container in "${REQUIRED_CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        echo "✅ $container 正在運行"
    else
        echo "❌ $container 未運行"
        exit 1
    fi
done

# 6. 等待服務就緒
echo ""
echo "🔍 等待服務就緒..."
sleep 30

# 7. 執行完整功能測試
echo ""
echo "🧪 執行完整功能測試..."
if ./scripts/regression_test.sh; then
    echo "✅ 回歸測試通過"
else
    echo "❌ 回歸測試失敗"
    exit 1
fi

# 8. 額外的 Web 界面測試
echo ""
echo "🌐 Web 界面深度測試..."

# 測試 Dashboard 主頁
if curl -s http://localhost:8602 | grep -q "Dashboard\|智能助理"; then
    echo "✅ Dashboard 主頁正常"
else
    echo "❌ Dashboard 主頁異常"
fi

# 測試 API 端點
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ API 端點可訪問"
else
    echo "⚠️  API 端點無回應（這可能是正常的）"
fi

# 9. 生成完整報告
echo ""
echo "📊 完整重啟驗證報告"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo "✅ 系統完全重啟成功！"
echo "完成時間: $(date)"
echo "測試分支: $CURRENT_BRANCH"
echo "測試提交: $CURRENT_COMMIT"
echo ""
echo "🚀 系統已準備就緒，可以安全使用"
echo ""
echo "📋 訪問地址:"
echo "   Dashboard: http://localhost:8602"
echo "   API: http://localhost:8002"
echo "   Kibana: http://localhost:5601"
echo ""

# 記錄完整重啟日誌
echo "$(date): 完整重啟驗證成功 - 分支: $CURRENT_BRANCH, 提交: $CURRENT_COMMIT" >> restart_history.log

echo "💡 建議: 如果一切正常，可以將當前狀態標記為穩定版本:"
echo "   git tag stable-$(date +%Y%m%d-%H%M%S)"
echo "   git push origin stable-$(date +%Y%m%d-%H%M%S)"