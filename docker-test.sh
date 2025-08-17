#!/bin/bash

echo "🐳 Docker Elasticsearch RAG 系統測試腳本"
echo "============================================"

# 檢查 Docker 是否運行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未運行，請先啟動 Docker"
    exit 1
fi

# 檢查 docker-compose 是否可用
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose 未安裝"
    exit 1
fi

echo "✅ Docker 環境檢查完成"

# 建構並啟動服務
echo "🔨 建構並啟動 Elasticsearch RAG 服務..."
docker-compose -f docker-compose.elasticsearch.yml up --build -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "📋 檢查服務狀態："
docker-compose -f docker-compose.elasticsearch.yml ps

# 檢查 Elasticsearch 健康狀態
echo "🏥 檢查 Elasticsearch 健康狀態："
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
        echo "✅ Elasticsearch 健康檢查通過"
        break
    else
        echo "⏳ 等待 Elasticsearch 啟動... (嘗試 $((retry_count + 1))/$max_retries)"
        sleep 5
        retry_count=$((retry_count + 1))
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Elasticsearch 啟動超時"
    echo "📋 查看 Elasticsearch 日誌："
    docker-compose -f docker-compose.elasticsearch.yml logs elasticsearch
    exit 1
fi

# 檢查 Web 應用
echo "🌐 檢查 Web 應用 (http://localhost:8502)："
if curl -s http://localhost:8502 >/dev/null 2>&1; then
    echo "✅ Web 應用正常運行"
else
    echo "⚠️ Web 應用可能還在啟動中"
    echo "📋 查看應用日誌："
    docker-compose -f docker-compose.elasticsearch.yml logs graphrag-app-elasticsearch --tail=20
fi

# 執行容器內測試
echo "🧪 在容器內執行測試..."
docker-compose -f docker-compose.elasticsearch.yml exec -T graphrag-app-elasticsearch python test_elasticsearch_rag.py

echo "🎉 測試完成！"
echo "📱 訪問 http://localhost:8502 使用應用"
echo "🔍 訪問 http://localhost:5601 使用 Kibana (如果啟用)"

# 顯示日誌查看命令
echo ""
echo "📋 實用命令："
echo "  查看所有日誌: docker-compose -f docker-compose.elasticsearch.yml logs"
echo "  查看應用日誌: docker-compose -f docker-compose.elasticsearch.yml logs graphrag-app-elasticsearch"
echo "  停止服務: docker-compose -f docker-compose.elasticsearch.yml down"
echo "  重啟服務: docker-compose -f docker-compose.elasticsearch.yml restart"