# 🤖 Graph RAG 智能文檔問答助理

基於 **Graph RAG** 技術的先進問答系統，結合 LlamaIndex PropertyGraph 和 Streamlit，提供知識圖譜驅動的智能對話體驗。

## 🌟 系統特色

### 🚀 核心功能
- **🕸️ Graph RAG 架構**: 基於知識圖譜的增強檢索生成
- **📄 多格式支援**: PDF, DOCX, TXT, Markdown, 圖片 OCR
- **🎯 知識圖譜可視化**: 互動式圖譜展示與實體探索
- **💬 智能對話**: 上下文記憶與多輪對話
- **🔍 社群檢測**: 自動識別知識群組與概念關聯

### 🎨 用戶體驗
- **✨ 現代化 UI**: 響應式設計與直覺操作
- **📱 多頁面架構**: 首頁、知識庫、演示、圖譜、設定
- **📤 拖拽上傳**: 批量檔案處理與進度顯示
- **⚡ 即時反饋**: 處理狀態與錯誤提示

### 🔧 技術特色
- **🔄 漸進式載入**: 智能回退機制
- **🔀 混合檢索**: 向量 + 圖檢索
- **🐳 Docker 部署**: 一鍵容器化方案
- **❤️ 健康檢查**: 服務監控與自動恢復

## 🏗️ 技術架構

| 組件 | 技術 | 說明 |
|------|------|------|
| **前端** | Streamlit + 自定義 UI 組件 | 現代化響應式介面 |
| **Graph RAG** | LlamaIndex PropertyGraph | 知識圖譜建構與檢索 |
| **向量資料庫** | ChromaDB (可選) | 高性能向量儲存 |
| **圖資料庫** | NetworkX + SimpleGraphStore | 圖結構管理 |
| **LLM** | Groq LLaMA 3.3-70B | 高性能語言模型 |
| **嵌入模型** | sentence-transformers | 語義向量化 |
| **OCR** | Google Gemini Vision API | 圖片文字識別 |
| **可視化** | Pyvis | 互動式圖譜展示 |
| **容器化** | Docker & Docker Compose | 一鍵部署方案 |

## 🚀 快速開始

### 方法一：Docker 部署 (推薦)

```bash
# 1. 克隆專案
git clone <repository-url>
cd rag_llamaindex_poc

# 2. 運行部署腳本
chmod +x docker-deploy.sh
./docker-deploy.sh

# 3. 訪問系統
open http://localhost:8501
```

### 方法二：本地開發

```bash
# 1. 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 配置環境變數
cp .env.example .env
# 編輯 .env 檔案，設定 API 金鑰

# 4. 啟動系統
python run_graphrag.py
# 或者
streamlit run main_app.py
```

## ⚙️ 配置設定

### API 金鑰設定

在 `.env` 檔案中配置：

```env
# 必需 - Groq API (用於 LLM)
GROQ_API_KEY=your_groq_api_key_here

# 可選 - Gemini API (用於 OCR 功能)
GEMINI_API_KEY=your_gemini_api_key_here

# Graph RAG 設定
ENABLE_GRAPH_RAG=true
MAX_TRIPLETS_PER_CHUNK=10
GRAPH_COMMUNITY_SIZE=5

# 檔案上傳設定
MAX_FILE_SIZE_MB=10
MAX_IMAGE_SIZE_MB=5
```

### 取得 API 金鑰

- **Groq API**: [https://console.groq.com/keys](https://console.groq.com/keys)
- **Gemini API**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 📋 使用指南

### 1. 上傳文檔
- 支援格式：PDF, DOCX, TXT, Markdown, 圖片
- 批量上傳與進度顯示
- 自動檔案驗證

### 2. 知識圖譜建構
- AI 自動提取實體與關係
- 社群檢測與分群
- 圖譜可視化展示

### 3. 智能問答
- 基於知識圖譜的上下文查詢
- 多輪對話記憶
- 參考來源顯示

### 4. 圖譜探索
- 互動式知識圖譜
- 實體關係瀏覽
- 社群結構分析

## 🐳 Docker 部署

### 服務架構

```yaml
services:
  graphrag-app:      # 主應用程式
    ports: ["8501:8501"]
  
  chromadb:          # 向量資料庫 (可選)
    ports: ["8000:8000"]
```

### 常用命令

```bash
# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down

# 重新建置
docker-compose up -d --build

# 查看狀態
docker-compose ps
```

## 📊 系統架構圖

```
📱 用戶介面 (Streamlit)
    ↓
🤖 主應用程式 (main_app.py)
    ↓
🕸️ Graph RAG 系統 (graph_rag_system.py)
    ↓
┌─────────────────┬─────────────────┐
📚 知識圖譜      📊 向量資料庫    🔍 LLM 推理
(NetworkX)       (ChromaDB)       (Groq)
```

## 🔧 開發說明

### 專案結構

```
📦 rag_llamaindex_poc/
├── 🤖 main_app.py                    # 主應用入口
├── 🕸️ graph_rag_system.py          # Graph RAG 核心
├── 🔧 enhanced_rag_system.py       # 增強 RAG 基礎
├── ⚙️ config.py                     # 配置管理
├── 🐳 docker-compose.yml           # Docker 編排
├── 📋 requirements.txt              # 依賴套件
└── 📁 components/                   # UI 組件
    ├── layout/
    ├── knowledge_base/
    └── chat/
```

### 新增功能開發

1. **UI 組件**: 在 `components/` 目錄下新增
2. **RAG 功能**: 擴展 `graph_rag_system.py`
3. **配置選項**: 在 `config.py` 中添加
4. **頁面功能**: 在 `main_app.py` 中實作

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🆘 問題回報

如果遇到問題，請在 [Issues](../../issues) 頁面回報，並提供：

- 系統環境資訊
- 錯誤訊息截圖
- 重現步驟說明

## 📞 聯絡方式

- 💬 討論：[Discussions](../../discussions)
- 🐛 問題：[Issues](../../issues)
- 📧 Email: [your-email@example.com]

---

⭐ 如果這個專案對您有幫助，請給我們一個星星！
