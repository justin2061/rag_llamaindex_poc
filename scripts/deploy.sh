#!/bin/bash

# RAG 智能問答系統 - 部署腳本
# 支援多種部署模式

set -e

# 顯示使用說明
show_help() {
    echo "RAG 智能問答系統 - 部署腳本"
    echo ""
    echo "使用方式:"
    echo "  ./deploy.sh [模式] [選項]"
    echo ""
    echo "部署模式:"
    echo "  standard       - 標準部署 (RAG + Elasticsearch)"
    echo "  elasticsearch  - 標準部署 (同 standard)"
    echo "  kibana         - 啟動 Kibana (Elasticsearch 管理界面)"
    echo "  down          - 停止所有服務"
    echo "  logs          - 顯示服務日誌"
    echo "  status        - 檢查服務狀態"
    echo ""
    echo "選項:"
    echo "  --build       - 強制重新建置映像"
    echo "  --help        - 顯示此說明"
    echo ""
    echo "範例:"
    echo "  ./deploy.sh elasticsearch     # 啟動 Elasticsearch RAG 系統"
    echo "  ./deploy.sh standard --build  # 重新建置並啟動標準系統"
    echo "  ./deploy.sh down              # 停止所有服務"
}

# 檢查依賴
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安裝或不在 PATH 中"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose 未安裝或不在 PATH 中"
        exit 1
    fi
}

# 檢查環境文件
check_env() {
    if [ ! -f ".env" ]; then
        echo "⚠️  警告: .env 檔案不存在"
        echo "請創建 .env 檔案並設定必要的 API 金鑰:"
        echo ""
        echo "必要設定:"
        echo "GROQ_API_KEY=your_groq_api_key"
        echo ""
        echo "可選設定:"
        echo "JINA_API_KEY=your_jina_api_key"
        echo "GEMINI_API_KEY=your_gemini_api_key"
        echo ""
        read -p "是否繼續部署? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 創建必要目錄
create_directories() {
    echo "📁 創建必要目錄..."
    mkdir -p data/{pdfs,index,user_uploads,chroma_db}
    mkdir -p elasticsearch_data
}

# 部署 Elasticsearch RAG 系統
deploy_elasticsearch() {
    echo "🚀 部署 Elasticsearch RAG 系統..."
    
    local build_flag=""
    if [[ "$1" == "--build" ]]; then
        build_flag="--build"
        echo "🔨 強制重新建置映像..."
    fi
    
    docker-compose -f docker/docker-compose.yml up -d $build_flag
    
    echo "⏳ 等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Elasticsearch RAG 系統部署成功!"
        echo ""
        echo "🌐 RAG 應用程式: http://localhost:8501"
        echo "🔍 Elasticsearch: http://localhost:9200"
        echo "📊 Kibana (可選): 使用 './deploy.sh kibana' 啟動"
        echo ""
        echo "💡 使用 './deploy.sh logs' 查看日誌"
        echo "💡 使用 './deploy.sh down' 停止服務"
    else
        echo "❌ 部署失敗，檢查日誌:"
        docker-compose logs
    fi
}

# 部署標準系統
deploy_standard() {
    echo "🚀 部署標準 RAG 系統..."
    
    local build_flag=""
    if [[ "$1" == "--build" ]]; then
        build_flag="--build"
        echo "🔨 強制重新建置映像..."
    fi
    
    docker-compose -f docker/docker-compose.yml up -d $build_flag
    
    echo "⏳ 等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    if docker-compose ps | grep -q "Up"; then
        echo "✅ 標準 RAG 系統部署成功!"
        echo ""
        echo "🌐 應用程式: http://localhost:8501"
        echo "🔍 Elasticsearch: http://localhost:9200"
        echo ""
        echo "💡 使用 './deploy.sh logs' 查看日誌"
        echo "💡 使用 './deploy.sh down' 停止服務"
    else
        echo "❌ 部署失敗，檢查日誌:"
        docker-compose logs
    fi
}

# 部署 Kibana
deploy_kibana() {
    echo "📊 啟動 Kibana 管理界面..."
    
    docker-compose -f docker/docker-compose.yml --profile kibana up -d kibana
    
    echo "⏳ 等待 Kibana 啟動..."
    sleep 15
    
    if docker-compose ps kibana | grep -q "Up"; then
        echo "✅ Kibana 部署成功!"
        echo ""
        echo "📊 Kibana 管理界面: http://localhost:5601"
        echo "🔍 Elasticsearch: http://localhost:9200"
        echo ""
        echo "💡 使用 './deploy.sh down' 停止所有服務"
    else
        echo "❌ Kibana 部署失敗，檢查日誌:"
        docker-compose logs kibana
    fi
}

# 停止服務
stop_services() {
    echo "🛑 停止所有 RAG 系統服務..."
    
    # 停止包含 profiles 的所有服務
    docker-compose --profile "*" down 2>/dev/null || true
    docker-compose -f docker/docker-compose.yml down 2>/dev/null || true
    
    echo "✅ 所有服務已停止"
}

# 顯示日誌
show_logs() {
    echo "📋 顯示服務日誌..."
    
    # 檢查哪個服務在運行
    if docker-compose ps | grep -q "Up"; then
        echo "標準系統日誌:"
        docker-compose logs -f --tail=100
    elif docker-compose -f docker-compose.elasticsearch.yml ps | grep -q "Up"; then
        echo "Elasticsearch 系統日誌:"
        docker-compose -f docker-compose.elasticsearch.yml logs -f --tail=100
    else
        echo "❌ 沒有正在運行的服務"
    fi
}

# 檢查服務狀態
check_status() {
    echo "📊 檢查服務狀態..."
    echo ""
    
    echo "標準系統:"
    docker-compose ps
    echo ""
    
    echo "Elasticsearch 系統:"
    docker-compose -f docker-compose.elasticsearch.yml ps
}

# 主程式
main() {
    # 檢查參數
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        show_help
        exit 0
    fi
    
    # 檢查依賴
    check_dependencies
    
    # 執行對應命令
    case "$1" in
        "elasticsearch"|"standard")
            check_env
            create_directories
            deploy_elasticsearch "$2"
            ;;
        "kibana")
            deploy_kibana
            ;;
        "down")
            stop_services
            ;;
        "logs")
            show_logs
            ;;
        "status")
            check_status
            ;;
        "")
            echo "❌ 請指定部署模式"
            echo "使用 './deploy.sh --help' 查看使用說明"
            exit 1
            ;;
        *)
            echo "❌ 未知的部署模式: $1"
            echo "使用 './deploy.sh --help' 查看使用說明"
            exit 1
            ;;
    esac
}

# 執行主程式
main "$@"