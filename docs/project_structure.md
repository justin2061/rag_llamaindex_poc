# 專案結構說明

## 檔案組織

```
POC-7_lamaindex/
├── README.md                    # 專案說明
├── requirements.txt             # Python 依賴套件
├── .env.example                 # 環境變數範例
├── .env                        # 環境變數設定檔 (需要建立)
├── run.py                      # 啟動腳本
├── project_structure.md        # 本檔案
│
├── config.py                   # 配置設定
├── utils.py                    # 工具函數
│
├── pdf_downloader.py           # 基本PDF下載器
├── enhanced_pdf_downloader.py  # 增強版PDF下載器
├── rag_system.py              # RAG系統核心
│
├── app.py                     # 基本Streamlit應用程式
├── enhanced_app.py            # 增強版Streamlit應用程式
│
└── data/                      # 資料目錄 (自動建立)
    ├── pdfs/                  # PDF檔案儲存
    └── index/                 # 向量索引儲存
```

## 主要模組功能

### 核心模組

1. **config.py**
   - 系統配置設定
   - API金鑰管理
   - 檔案路徑設定
   - PDF來源網址

2. **rag_system.py**
   - RAG系統核心邏輯
   - 文檔載入與處理
   - 向量索引建立
   - 查詢引擎設定

3. **utils.py**
   - 工具函數集合
   - 文本處理
   - 網頁爬取
   - 檔案操作

### 下載器模組

1. **pdf_downloader.py**
   - 基本PDF下載功能
   - 預設URL下載
   - 檔案管理

2. **enhanced_pdf_downloader.py**
   - 增強版下載器
   - 自動連結發現
   - 進度追蹤
   - 檔案資訊管理

### 前端介面

1. **app.py**
   - 基本Streamlit介面
   - 核心問答功能
   - 簡潔的使用者界面

2. **enhanced_app.py**
   - 增強版介面
   - 豐富的互動功能
   - 美化的UI設計
   - 詳細的系統控制

## 使用方式

### 1. 環境準備
```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，設定您的 Groq API Key
```

### 2. 啟動應用程式

#### 基本版本
```bash
python run.py
# 或
streamlit run app.py
```

#### 增強版本
```bash
python run.py enhanced
# 或
streamlit run enhanced_app.py
```

### 3. 使用流程
1. 首次使用點擊「初始化系統」
2. 等待系統下載並處理PDF文件
3. 開始使用問答功能

## 技術特色

### AI技術棧
- **語言模型**: Groq Llama3-8B
- **嵌入模型**: HuggingFace Sentence Transformers
- **RAG框架**: LlamaIndex
- **向量資料庫**: ChromaDB

### 功能特色
- 自動PDF發現與下載
- 智能文檔處理
- 向量化語義搜尋
- 即時問答系統
- 歷史記錄管理

### 界面特色
- 響應式設計
- 即時狀態反饋
- 進度追蹤顯示
- 友善的使用者體驗

## 擴展建議

1. **資料來源擴展**
   - 加入更多PDF來源
   - 支援其他文檔格式
   - 定期更新機制

2. **功能增強**
   - 多語言支援
   - 圖表識別
   - 文檔摘要功能

3. **效能優化**
   - 快取機制
   - 分散式處理
   - 增量更新

4. **使用者體驗**
   - 語音輸入
   - 結果匯出
   - 個人化設定 