#!/bin/bash

# Graph RAG 智能文檔問答系統 Docker 部署腳本

set -e

echo "🚀 Graph RAG 智能文檔問答系統 Docker 部署"
echo "=" * 50

# 檢查 Docker 和 Docker Compose
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    
    echo "✅ Docker 環境檢查通過"
}

# 檢查 .env 檔案
check_env() {
    if [ ! -f ".env" ]; then
        echo "⚠️ .env 檔案不存在，正在創建範本..."
        cat > .env << EOF
# API 設定
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Graph RAG 設定
ENABLE_GRAPH_RAG=true
MAX_TRIPLETS_PER_CHUNK=10
GRAPH_COMMUNITY_SIZE=5

# 檔案上傳設定
MAX_FILE_SIZE_MB=10
MAX_IMAGE_SIZE_MB=5

# 系統設定
CONVERSATION_MEMORY_STEPS=5
MAX_CONTEXT_LENGTH=4000
ENABLE_CONVERSATION_MEMORY=true
ENABLE_OCR=true
EOF
        echo "📝 請編輯 .env 檔案並設定您的 API 金鑰"
        echo "   - GROQ_API_KEY: 必需，用於 LLM"
        echo "   - GEMINI_API_KEY: 可選，用於 OCR 功能"
        echo ""
        read -p "是否現在編輯 .env 檔案？(y/N): " edit_env
        if [[ $edit_env =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    else
        echo "✅ .env 檔案存在"
    fi
}

# 檢查 API 金鑰
check_api_keys() {
    source .env
    
    if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_groq_api_key_here" ]; then
        echo "⚠️ 請在 .env 檔案中設定有效的 GROQ_API_KEY"
        echo "   取得金鑰: https://console.groq.com/keys"
        exit 1
    fi
    
    echo "✅ API 金鑰檢查通過"
}

# 創建必要目錄
create_directories() {
    echo "📁 創建必要目錄..."
    mkdir -p data/{pdfs,index,user_uploads,chroma_db}
    echo "✅ 目錄創建完成"
}

# 構建並啟動服務
deploy_services() {
    echo "🔨 構建 Docker 映像..."
    
    # 使用適當的 Docker Compose 命令
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    # 構建映像
    $DOCKER_COMPOSE build --no-cache
    
    echo "🚀 啟動服務..."
    $DOCKER_COMPOSE up -d
    
    echo "📊 檢查服務狀態..."
    sleep 10
    $DOCKER_COMPOSE ps
}

# 顯示部署資訊
show_deployment_info() {
    echo ""
    echo "🎉 部署完成！"
    echo "=" * 50
    echo "🌐 主應用程式: http://localhost:8501"
    echo "🗄️ ChromaDB 管理: http://localhost:8000"
    echo ""
    echo "📋 常用命令:"
    echo "   查看日誌: docker-compose logs -f"
    echo "   停止服務: docker-compose down"
    echo "   重啟服務: docker-compose restart"
    echo "   查看狀態: docker-compose ps"
    echo ""
    echo "🔧 如需重新部署:"
    echo "   docker-compose down && docker-compose up -d --build"
    echo ""
}

# 主函數
main() {
    echo "開始部署流程..."
    
    check_docker
    check_env
    check_api_keys
    create_directories
    deploy_services
    show_deployment_info
    
    echo "✅ Graph RAG 系統部署完成！"
}

# 處理中斷信號
trap 'echo "❌ 部署中斷"; exit 1' INT TERM

# 執行主函數
main "$@"
