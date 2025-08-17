#!/bin/bash

# Docker 運行腳本 - 台灣茶葉知識RAG系統

echo "🚀 啟動台灣茶葉知識RAG系統 Docker 容器..."

# 檢查 .env 檔案是否存在
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 檔案不存在"
    echo "請創建 .env 檔案並設定 GROQ_API_KEY"
    echo "範例內容:"
    echo "GROQ_API_KEY=your_groq_api_key_here"
    exit 1
fi

# 創建必要的目錄
mkdir -p data/pdfs
mkdir -p data/index

# 建立 Docker 映像 (如果不存在)
echo "📦 建立 Docker 映像..."
docker build -t taiwan-tea-rag .

# 停止現有容器 (如果存在)
echo "🛑 停止現有容器..."
docker stop taiwan-tea-rag 2>/dev/null || true
docker rm taiwan-tea-rag 2>/dev/null || true

# 啟動新容器
echo "🐳 啟動新容器..."
docker run -d \
  --name taiwan-tea-rag \
  -p 8620:8501 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/.env:/app/.env" \
  --restart unless-stopped \
  taiwan-tea-rag

# 檢查容器狀態
sleep 5
if docker ps | grep -q taiwan-tea-rag; then
    echo "✅ 容器成功啟動!"
    echo "🌐 應用程式網址: http://localhost:8620"
    echo "📊 查看容器日誌: docker logs -f taiwan-tea-rag"
    echo "🛑 停止容器: docker stop taiwan-tea-rag"
else
    echo "❌ 容器啟動失敗，查看日誌:"
    docker logs taiwan-tea-rag
fi 