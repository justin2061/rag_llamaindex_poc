#!/bin/bash

# 檢查 Docker 構建上下文腳本
echo "🔍 分析 Docker 構建上下文..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}📊 目錄大小分析：${NC}"
echo "總目錄大小："
du -sh . 2>/dev/null

echo -e "\n主要子目錄："
du -sh */ 2>/dev/null | sort -hr | head -10

echo -e "\n${YELLOW}🔍 檢查 data/ 目錄：${NC}"
if [ -d "data" ]; then
    echo "data/ 目錄大小："
    du -sh data/ 2>/dev/null
    
    echo -e "\ndata/ 子目錄："
    du -sh data/*/ 2>/dev/null | sort -hr
    
    echo -e "\n最大的文件："
    find data/ -type f -exec du -h {} + 2>/dev/null | sort -hr | head -5
else
    echo "data/ 目錄不存在"
fi

echo -e "\n${YELLOW}📋 檢查 .dockerignore：${NC}"
if [ -f ".dockerignore" ]; then
    echo "✅ .dockerignore 存在"
    echo -e "\n被忽略的模式："
    grep -E "^data|^\*\.bin|chroma" .dockerignore
else
    echo "❌ .dockerignore 不存在"
fi

echo -e "\n${YELLOW}🔬 模擬 Docker 構建上下文：${NC}"
echo "創建臨時 tar 文件來測試上下文大小..."

# 創建臨時目錄
temp_dir=$(mktemp -d)
echo "臨時目錄：$temp_dir"

# 模擬 Docker 上下文
tar --exclude-from=.dockerignore -cf "$temp_dir/context.tar" . 2>/dev/null

if [ -f "$temp_dir/context.tar" ]; then
    context_size=$(du -sh "$temp_dir/context.tar" | cut -f1)
    echo -e "${GREEN}估計的 Docker 上下文大小：$context_size${NC}"
else
    echo -e "${RED}無法創建上下文文件${NC}"
fi

# 清理
rm -rf "$temp_dir"

echo -e "\n${YELLOW}💡 建議：${NC}"
echo "1. 如果 Docker 上下文 > 1GB，構建會很慢"
echo "2. 檢查 .dockerignore 是否正確排除大文件"
echo "3. 考慮清理不必要的數據文件"

# 檢查 ChromaDB 問題
if [ -d "data/chroma_db" ]; then
    chroma_size=$(du -sh data/chroma_db 2>/dev/null | cut -f1)
    echo -e "\n${RED}⚠️  ChromaDB 大小：$chroma_size${NC}"
    
    if [ -f "data/chroma_db/*/link_lists.bin" ]; then
        link_size=$(du -sh data/chroma_db/*/link_lists.bin 2>/dev/null | cut -f1)
        echo -e "${RED}⚠️  link_lists.bin 大小：$link_size${NC}"
        echo -e "${YELLOW}這個文件異常大，可能需要重建 ChromaDB${NC}"
    fi
fi

echo -e "\n${GREEN}🎉 分析完成！${NC}"