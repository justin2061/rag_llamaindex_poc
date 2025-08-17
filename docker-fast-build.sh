#!/bin/bash

# Docker 快速構建腳本
# 用於解決構建緩慢問題

echo "🚀 Docker 快速構建腳本"
echo "========================"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Docker 狀態
echo -e "${YELLOW}📋 檢查 Docker 狀態...${NC}"
if ! docker --version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未安裝或未啟動${NC}"
    exit 1
fi

# 顯示當前目錄大小
echo -e "${YELLOW}📊 分析目錄大小...${NC}"
echo "當前目錄大小："
du -sh . 2>/dev/null || echo "無法獲取目錄大小"

echo "data/ 目錄大小："
du -sh data/ 2>/dev/null || echo "data/ 目錄不存在"

# 清理 Docker 緩存
echo -e "${YELLOW}🧹 清理 Docker 緩存 (可選)...${NC}"
read -p "是否要清理 Docker 緩存？這會刪除未使用的映像 (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理 Docker 緩存..."
    docker system prune -f
    docker image prune -f
fi

# 檢查 .dockerignore
echo -e "${YELLOW}📋 檢查 .dockerignore 設定...${NC}"
if [ ! -f .dockerignore ]; then
    echo -e "${RED}❌ 找不到 .dockerignore 文件${NC}"
    exit 1
fi

echo "✅ .dockerignore 存在"
echo "忽略的重要目錄："
grep -E "^data/|^\.cache|^models/" .dockerignore || echo "未找到數據目錄忽略設定"

# 顯示構建前資訊
echo -e "${YELLOW}🔧 準備構建...${NC}"
echo "構建上下文將排除以下大型目錄："
echo "- data/pdfs/"
echo "- data/chroma_db/"
echo "- data/index/"
echo "- data/user_uploads/"
echo "- .cache/"
echo "- models/"

# 選擇構建模式
echo -e "${YELLOW}🔧 選擇構建模式...${NC}"
echo "1) 開發模式 (代碼 volume 掛載，快速)"
echo "2) 生產模式 (代碼複製到容器)"
read -p "請選擇模式 (1/2，默認 1): " -n 1 -r
echo

if [[ $REPLY =~ ^[2]$ ]]; then
    echo -e "${GREEN}🚀 開始生產模式構建...${NC}"
    echo "使用命令：docker-compose -f docker-compose.prod.yml build --no-cache"
    
    start_time=$(date +%s)
    if docker-compose -f docker-compose.prod.yml build --no-cache; then
        build_success=true
        compose_file="docker-compose.prod.yml"
    else
        build_success=false
    fi
else
    echo -e "${GREEN}🚀 開始開發模式構建...${NC}"
    echo "使用命令：docker-compose build --no-cache"
    echo "注意：代碼將通過 volume 掛載，構建會更快"
    
    start_time=$(date +%s)
    if docker-compose build --no-cache; then
        build_success=true
        compose_file="docker-compose.yml"
    else
        build_success=false
    fi
fi

# 檢查構建結果
if [ "$build_success" = true ]; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo -e "${GREEN}✅ 構建成功！${NC}"
    echo -e "${GREEN}⏱️  構建時間：${duration} 秒${NC}"
    
    echo -e "${YELLOW}🚀 啟動服務...${NC}"
    docker-compose -f $compose_file up -d
    
    echo -e "${GREEN}✅ 服務已啟動！${NC}"
    echo "訪問地址：http://localhost:8501"
    echo "查看日誌：docker-compose logs -f"
else
    echo -e "${RED}❌ 構建失敗${NC}"
    echo "請檢查錯誤訊息並重試"
    exit 1
fi

echo -e "${GREEN}🎉 完成！${NC}"