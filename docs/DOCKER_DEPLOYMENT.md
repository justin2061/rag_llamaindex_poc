# Docker 部署指南

## 🚀 Volume Bind 部署方式

我們現在使用 **volume bind** 方式來大幅加速 Docker 構建和開發流程。

### 兩種部署模式

#### 1. 開發模式（推薦）⚡
- **特點**：代碼通過 volume 掛載，不複製到容器
- **優勢**：
  - 構建極快（從 38 分鐘 → 2-5 分鐘）
  - 代碼變更即時生效
  - 方便調試和開發
- **適用**：開發、測試環境

#### 2. 生產模式 🏭
- **特點**：代碼複製到容器內
- **優勢**：
  - 獨立性強
  - 不依賴宿主機代碼
- **適用**：生產部署

## 快速開始

### 方法一：使用自動化腳本（推薦）

```bash
# Linux/Mac
./docker-fast-build.sh

# Windows
docker-fast-build.bat
```

腳本會自動：
1. 檢查環境
2. 讓您選擇模式
3. 執行構建
4. 啟動服務

### 方法二：手動執行

#### 開發模式
```bash
# 構建（超快）
docker-compose build

# 啟動
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

#### 生產模式
```bash
# 構建
docker-compose -f docker-compose.prod.yml build

# 啟動  
docker-compose -f docker-compose.prod.yml up -d

# 查看日誌
docker-compose -f docker-compose.prod.yml logs -f
```

## 構建時間對比

| 模式 | 構建時間 | 代碼變更 | 用途 |
|------|----------|----------|------|
| 開發模式 | 2-5 分鐘 | 即時生效 | 開發/測試 |
| 生產模式 | 5-10 分鐘 | 需重新構建 | 生產部署 |
| 舊方式 | 38+ 分鐘 | 需重新構建 | 已淘汰 |

## Volume 掛載說明

### 開發模式 Volume 配置
```yaml
volumes:
  - .:/app                     # 整個專案目錄
  - /app/data                  # 排除 data（避免覆蓋）
  - ./data:/app/data           # 重新掛載 data（持久化）
  - ./.env:/app/.env           # 環境變數
```

### 優點
1. **極速構建**：不複製 140GB+ 的內容
2. **即時更新**：修改代碼立即生效，無需重建
3. **開發友好**：本地編輯器和容器內同步
4. **資料持久**：data 目錄依然持久化

### 注意事項
1. **權限問題**：Linux 可能需要調整文件權限
2. **路徑問題**：確保掛載路徑正確
3. **環境變數**：確保 .env 文件存在

## 故障排除

### 常見問題

#### 1. 權限錯誤（Linux）
```bash
# 修復權限
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

#### 2. Volume 掛載失敗
```bash
# 檢查路徑
docker-compose config

# 重新創建容器
docker-compose down
docker-compose up -d
```

#### 3. 代碼變更不生效
```bash
# 確認 volume 掛載
docker exec -it graphrag-intelligent-assistant ls -la /app

# 重啟服務
docker-compose restart
```

## 開發工作流程

### 日常開發
1. 啟動服務：`docker-compose up -d`
2. 修改代碼：直接在本地編輯
3. 查看效果：瀏覽器刷新即可
4. 查看日誌：`docker-compose logs -f`

### 新增依賴
1. 修改 `requirements.txt`
2. 重新構建：`docker-compose build`
3. 重啟服務：`docker-compose up -d`

### 清理環境
```bash
# 停止服務
docker-compose down

# 清理容器和映像
docker system prune -f

# 重新開始
./docker-fast-build.sh
```

## 效能比較

### 構建上下文大小
- **優化前**：140.76GB（包含所有文件）
- **優化後**：~100MB（只有 requirements.txt 和系統文件）

### 構建步驟
- **優化前**：15+ Docker layers
- **優化後**：8 Docker layers

### 開發體驗
- **代碼修改**：立即生效 vs 需要重建
- **調試效率**：實時 vs 批次處理
- **依賴管理**：分層緩存優化

## 總結

Volume bind 方式是現代 Docker 開發的最佳實踐，特別適合：
- 🔥 頻繁修改代碼的開發階段
- 🐛 需要快速調試的場景  
- 👥 團隊協作開發
- 📈 CI/CD 流程優化

這種方式讓 Docker 開發變得**快速**、**靈活**且**高效**！