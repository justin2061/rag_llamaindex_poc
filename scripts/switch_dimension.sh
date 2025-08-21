#!/bin/bash

# Elasticsearch 向量維度快速切換腳本
# 使用方法: ./scripts/switch_dimension.sh [維度]

set -e  # 遇到錯誤時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數定義
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查參數
TARGET_DIMENSION=${1:-128}

if ! [[ "$TARGET_DIMENSION" =~ ^[0-9]+$ ]]; then
    log_error "無效的維度參數: $TARGET_DIMENSION"
    echo "使用方法: $0 [維度]"
    echo "例如: $0 128"
    exit 1
fi

# 檢查是否在項目根目錄
if [[ ! -f "docker-compose.yml" ]]; then
    log_error "請在項目根目錄執行此腳本"
    exit 1
fi

# 獲取當前維度
get_current_dimension() {
    if [[ -f ".env" ]]; then
        grep "ELASTICSEARCH_VECTOR_DIMENSION=" .env | cut -d'=' -f2 | tr -d ' '
    else
        echo "unknown"
    fi
}

CURRENT_DIMENSION=$(get_current_dimension)

echo "🔧 Elasticsearch 向量維度切換工具"
echo "=================================="
echo "📊 當前維度: $CURRENT_DIMENSION"
echo "🎯 目標維度: $TARGET_DIMENSION"
echo ""

# 檢查是否需要切換
if [[ "$CURRENT_DIMENSION" == "$TARGET_DIMENSION" ]]; then
    log_info "當前維度已是 $TARGET_DIMENSION，無需切換"
    exit 0
fi

# 確認切換
echo "⚠️  重要提醒:"
echo "   - 此操作將重啟所有服務"
echo "   - Elasticsearch 數據將被清理"
echo "   - 需要重新索引所有文檔"
echo ""

read -p "確認要切換維度嗎？(y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "操作已取消"
    exit 0
fi

# 開始切換流程
log_info "開始維度切換流程..."

# 1. 停止服務
log_info "停止 Docker 服務..."
if docker-compose down > /dev/null 2>&1; then
    log_success "服務已停止"
else
    log_warning "停止服務時出現警告，繼續執行"
fi

# 2. 備份當前配置
BACKUP_DIR="data/migration_backups/backup_$(date +%Y%m%d_%H%M%S)"
log_info "備份當前配置到 $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

if [[ -f ".env" ]]; then
    cp .env "$BACKUP_DIR/"
    log_success "已備份 .env 文件"
fi

if [[ -f "config/config.py" ]]; then
    cp config/config.py "$BACKUP_DIR/"
    log_success "已備份 config.py 文件"
fi

# 3. 清理 Elasticsearch 數據
if [[ -d "elasticsearch_data" ]]; then
    log_info "清理 Elasticsearch 數據..."
    sudo rm -rf elasticsearch_data/* > /dev/null 2>&1 || rm -rf elasticsearch_data/* > /dev/null 2>&1
    log_success "數據已清理"
fi

# 4. 更新 .env 文件
log_info "更新 .env 文件..."
if [[ -f ".env" ]]; then
    if grep -q "ELASTICSEARCH_VECTOR_DIMENSION=" .env; then
        # 替換現有行
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/ELASTICSEARCH_VECTOR_DIMENSION=.*/ELASTICSEARCH_VECTOR_DIMENSION=$TARGET_DIMENSION/" .env
        else
            # Linux
            sed -i "s/ELASTICSEARCH_VECTOR_DIMENSION=.*/ELASTICSEARCH_VECTOR_DIMENSION=$TARGET_DIMENSION/" .env
        fi
    else
        # 添加新行
        echo "ELASTICSEARCH_VECTOR_DIMENSION=$TARGET_DIMENSION" >> .env
    fi
    log_success "已更新 .env 文件"
else
    log_error "未找到 .env 文件"
    exit 1
fi

# 5. 更新 config.py (可選)
if [[ -f "config/config.py" ]]; then
    log_info "更新 config.py 默認值..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/ELASTICSEARCH_VECTOR_DIMENSION = int(os.getenv(\"ELASTICSEARCH_VECTOR_DIMENSION\", [0-9]*)/ELASTICSEARCH_VECTOR_DIMENSION = int(os.getenv(\"ELASTICSEARCH_VECTOR_DIMENSION\", $TARGET_DIMENSION)/" config/config.py
    else
        # Linux
        sed -i "s/ELASTICSEARCH_VECTOR_DIMENSION = int(os.getenv(\"ELASTICSEARCH_VECTOR_DIMENSION\", [0-9]*)/ELASTICSEARCH_VECTOR_DIMENSION = int(os.getenv(\"ELASTICSEARCH_VECTOR_DIMENSION\", $TARGET_DIMENSION)/" config/config.py
    fi
    log_success "已更新 config.py 文件"
fi

# 6. 啟動服務
log_info "啟動 Docker 服務..."
if docker-compose up -d > /dev/null 2>&1; then
    log_success "服務已啟動"
else
    log_error "啟動服務失敗"
    exit 1
fi

# 7. 等待服務就緒
log_info "等待服務就緒..."
for i in {1..60}; do
    if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
        log_success "Elasticsearch 服務已就緒"
        break
    fi
    
    if [[ $i -eq 60 ]]; then
        log_warning "Elasticsearch 服務啟動超時，但繼續執行"
        break
    fi
    
    if [[ $((i % 10)) -eq 0 ]]; then
        log_info "等待中... ($i/60s)"
    fi
    
    sleep 1
done

# 8. 驗證新配置
log_info "驗證新維度配置..."
sleep 10  # 等待容器完全啟動

NEW_DIMENSION=$(get_current_dimension)
if [[ "$NEW_DIMENSION" == "$TARGET_DIMENSION" ]]; then
    log_success "維度配置驗證成功: $NEW_DIMENSION"
else
    log_warning "維度配置可能未完全生效，請檢查"
fi

# 9. 顯示完成信息
echo ""
echo "✅ 維度切換完成！"
echo "=================="
echo "📊 新維度: $TARGET_DIMENSION"
echo "💾 配置備份: $BACKUP_DIR"
echo ""
echo "🔄 後續步驟:"
echo "   1. 重新上傳並索引文檔"
echo "   2. 測試查詢功能"
echo "   3. 驗證結果質量"
echo ""
echo "🛠️  測試命令:"
echo "   docker exec rag-intelligent-assistant python test_jina_api.py"
echo ""

log_success "維度切換流程完成！"