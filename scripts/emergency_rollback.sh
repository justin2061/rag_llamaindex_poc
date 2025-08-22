#!/bin/bash

# 緊急回滾腳本
# 當發現嚴重回歸錯誤時使用

echo "🚨 緊急回滾腳本"
echo "時間: $(date)"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="

# 檢查 git 狀態
if ! git status > /dev/null 2>&1; then
    echo "❌ 當前目錄不是 git 倉庫"
    exit 1
fi

# 顯示最近的提交
echo "📜 最近的提交歷史:"
git log --oneline -10

echo ""
echo "🔍 選擇回滾選項:"
echo "1) 回滾到上一個提交"
echo "2) 回滾到指定提交"
echo "3) 暫存當前修改並回滾到 main 分支"
echo "4) 取消操作"

read -p "請選擇 (1-4): " choice

case $choice in
    1)
        echo "📤 回滾到上一個提交..."
        LAST_COMMIT=$(git rev-parse HEAD~1)
        echo "目標提交: $LAST_COMMIT"
        ;;
    2)
        read -p "請輸入目標提交 ID: " TARGET_COMMIT
        if ! git rev-parse --verify "$TARGET_COMMIT" > /dev/null 2>&1; then
            echo "❌ 無效的提交 ID: $TARGET_COMMIT"
            exit 1
        fi
        LAST_COMMIT=$TARGET_COMMIT
        echo "目標提交: $LAST_COMMIT"
        ;;
    3)
        echo "📦 暫存當前修改並回滾到 main..."
        git stash push -m "Emergency rollback stash - $(date)"
        LAST_COMMIT="main"
        echo "目標分支: main"
        ;;
    4)
        echo "操作已取消"
        exit 0
        ;;
    *)
        echo "❌ 無效選擇"
        exit 1
        ;;
esac

# 確認操作
echo ""
echo "⚠️  警告: 這將會:"
echo "   - 回滾代碼到指定版本"
echo "   - 完全重啟所有容器"
echo "   - 可能丟失未提交的修改"
echo ""
read -p "您確定要繼續嗎？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

# 記錄回滾操作
echo "$(date): 緊急回滾開始 - 從 $(git rev-parse HEAD) 到 $LAST_COMMIT" >> rollback_history.log

# 執行回滾
echo ""
echo "🔄 執行回滾操作..."

# 停止容器
echo "🛑 停止容器..."
docker-compose down

# Git 回滾
echo "📤 Git 回滾..."
if [ "$LAST_COMMIT" = "main" ]; then
    git checkout main
else
    git checkout $LAST_COMMIT
fi

# 重啟系統
echo "🔧 重啟系統..."
docker-compose up -d

# 等待啟動
echo "⏳ 等待系統啟動..."
sleep 60

# 驗證回滾結果
echo ""
echo "🧪 驗證回滾結果..."

if ./scripts/regression_test.sh; then
    echo ""
    echo "✅ 緊急回滾成功！"
    echo "系統已恢復到穩定狀態"
    echo "當前版本: $(git rev-parse HEAD)"
    
    # 記錄成功
    echo "$(date): 緊急回滾成功 - 當前版本: $(git rev-parse HEAD)" >> rollback_history.log
else
    echo ""
    echo "❌ 回滾後系統仍有問題"
    echo "建議檢查系統配置或聯繫管理員"
    
    # 記錄失敗
    echo "$(date): 緊急回滾失敗 - 系統仍有問題" >> rollback_history.log
    exit 1
fi

echo ""
echo "📋 後續建議:"
echo "1. 檢查回滾是否解決了問題"
echo "2. 如果使用了 stash，可以用 'git stash list' 查看暫存的修改"
echo "3. 分析原始問題的原因，避免再次發生"
echo "4. 如需恢復修改，請謹慎操作並執行完整測試"
echo ""
echo "🔗 相關命令:"
echo "   查看暫存: git stash list"
echo "   恢復暫存: git stash pop"
echo "   查看回滾歷史: cat rollback_history.log"