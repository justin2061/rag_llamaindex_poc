#!/bin/bash

# 緊急清理腳本 - 解決 Docker 構建慢的問題
echo "🚨 緊急清理腳本"
echo "================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  警告：此腳本將清理大型數據文件${NC}"
echo -e "${YELLOW}這會重置您的 ChromaDB 和索引數據${NC}"
echo

# 顯示當前大小
echo "當前數據大小："
du -sh data/ 2>/dev/null || echo "data/ 目錄不存在"

echo
read -p "確定要繼續清理嗎？這將刪除所有 ChromaDB 和索引數據 (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 開始清理...${NC}"
    
    # 停止 Docker 服務
    echo "停止 Docker 服務..."
    docker-compose down 2>/dev/null || true
    
    # 備份重要配置
    echo "備份用戶配置..."
    if [ -f "data/user_preferences.json" ]; then
        cp data/user_preferences.json /tmp/user_preferences.json.backup
        echo "✅ 用戶配置已備份到 /tmp/"
    fi
    
    # 清理 ChromaDB
    echo -e "${YELLOW}清理 ChromaDB (161GB)...${NC}"
    if [ -d "data/chroma_db" ]; then
        rm -rf data/chroma_db/*
        echo "✅ ChromaDB 已清理"
    fi
    
    # 清理索引
    echo -e "${YELLOW}清理索引文件...${NC}"
    if [ -d "data/index" ]; then
        rm -rf data/index/*
        echo "✅ 索引文件已清理"
    fi
    
    # 保留但清理上傳文件
    echo -e "${YELLOW}清理上傳文件...${NC}"
    if [ -d "data/user_uploads" ]; then
        rm -rf data/user_uploads/*
        echo "✅ 上傳文件已清理"
    fi
    
    # 恢復配置
    if [ -f "/tmp/user_preferences.json.backup" ]; then
        mkdir -p data/
        cp /tmp/user_preferences.json.backup data/user_preferences.json
        echo "✅ 用戶配置已恢復"
    fi
    
    # 清理 Docker
    echo -e "${YELLOW}清理 Docker 緩存...${NC}"
    docker system prune -f
    docker image prune -f
    
    echo -e "${GREEN}✅ 清理完成！${NC}"
    echo
    echo "現在數據大小："
    du -sh data/ 2>/dev/null || echo "data/ 目錄為空"
    
    echo -e "\n${GREEN}🚀 現在可以快速構建了：${NC}"
    echo "docker-compose build"
    
else
    echo "清理已取消"
fi

echo -e "\n${YELLOW}💡 提示：${NC}"
echo "1. 如果不想清理數據，使用 docker-compose.light.yml"
echo "2. 或者移動 data/ 目錄到別處暫時避免"