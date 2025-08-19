# RAG LlamaIndex POC

## 📂 專案結構

```
rag_llamaindex_poc/
├── src/                          # 主要源碼
│   ├── rag_system/              # RAG 系統核心
│   │   ├── rag_system.py        # 基礎 RAG 系統
│   │   ├── enhanced_rag_system.py   # 增強 RAG 系統
│   │   ├── elasticsearch_rag_system.py  # Elasticsearch RAG 系統
│   │   └── graph_rag_system.py  # Graph RAG 系統
│   ├── storage/                 # 儲存相關
│   │   ├── chroma_vector_store.py   # ChromaDB 儲存
│   │   ├── custom_elasticsearch_store.py  # 自定義 ES 儲存
│   │   └── conversation_memory.py   # 對話記憶
│   ├── processors/              # 文檔處理
│   │   ├── pdf_downloader.py    # PDF 下載器
│   │   ├── enhanced_pdf_downloader.py  # 增強 PDF 下載器
│   │   ├── gemini_ocr.py        # Gemini OCR 處理
│   │   └── user_file_manager.py # 用戶文件管理
│   ├── ui/                      # 用戶界面
│   │   └── components/          # UI 組件
│   └── utils/                   # 工具函數
│       ├── utils.py             # 主要工具函數
│       ├── embedding_fix.py     # 嵌入修復
│       └── immediate_fix.py     # 即時修復
├── apps/                        # 應用程式入口
│   ├── simple_app.py           # 簡化版應用 (推薦)
│   ├── main_app.py             # 主要應用
│   ├── enhanced_ui_app.py      # 增強 UI 應用
│   └── run_graphrag.py         # Graph RAG 應用
├── tests/                       # 測試文件
│   ├── test_elasticsearch_rag.py   # ES RAG 測試
│   ├── test_pdf_discovery.py       # PDF 發現測試
│   └── test_upload_workflow.py     # 上傳工作流程測試
├── config/                      # 配置文件
│   └── config.py               # 主要配置
├── docs/                        # 文檔
│   ├── README.md               # 項目說明
│   ├── CLAUDE.md               # 開發指南
│   └── *.md                    # 其他文檔
├── scripts/                     # 腳本
│   ├── deploy.sh               # 部署腳本
│   └── emergency-cleanup.sh    # 清理腳本
├── docker/                      # Docker 相關
│   ├── Dockerfile              # Docker 容器配置
│   ├── docker-compose.yml      # Docker Compose 配置
│   └── .dockerignore           # Docker 忽略文件
├── data/                        # 數據目錄
│   ├── pdfs/                   # PDF 文件
│   ├── index/                  # 索引文件
│   └── user_uploads/           # 用戶上傳文件
├── main.py                      # 統一啟動入口
├── requirements.txt             # Python 依賴
└── .env                        # 環境變數
```

## 🚀 快速開始

### 使用統一啟動器

```bash
# 簡化版應用 (推薦)
python main.py simple

# 主要應用
python main.py main

# 增強 UI 應用
python main.py enhanced

# Graph RAG 應用
python main.py graphrag
```

### 直接啟動

```bash
# 簡化版應用
streamlit run apps/simple_app.py

# 主要應用
streamlit run apps/main_app.py
```

### Docker 部署

```bash
# 使用部署腳本
./scripts/deploy.sh elasticsearch

# 直接使用 docker-compose
docker-compose -f docker/docker-compose.yml up --build
```

## 📝 文檔

詳細文檔請參見 [docs/](./docs/) 目錄：

- [CLAUDE.md](./docs/CLAUDE.md) - 開發指南
- [SYSTEM_DOCUMENTATION.md](./docs/SYSTEM_DOCUMENTATION.md) - 系統文檔
- [DOCKER_DEPLOYMENT.md](./docs/DOCKER_DEPLOYMENT.md) - Docker 部署指南

## 🧪 測試

```bash
# 運行核心測試
python tests/test_elasticsearch_rag.py
python tests/test_pdf_discovery.py
python tests/test_upload_workflow.py

# 效能測試
python tests/benchmark_startup.py
streamlit run tests/rag_system_benchmark.py
```

## ⚙️ 配置

主要配置文件位於 [config/config.py](./config/config.py)，環境變數設定請參考 [.env.example](./.env.example)。