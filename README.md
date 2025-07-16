# 台灣茶葉知識RAG系統

基於LlamaIndex和Streamlit的茶葉知識問答系統，使用台灣茶及飲料作物改良場的PDF文件作為知識庫。

## 功能特色

- 自動下載並處理台灣茶及飲料作物改良場的PDF文件
- 使用HuggingFace嵌入模型進行文本向量化
- 基於Groq LLM的智能問答系統
- 友善的Streamlit網頁介面

## 安裝步驟

1. 複製環境變數檔案：
```bash
cp .env.example .env
```

2. 在 `.env` 檔案中設定您的Groq API密鑰

3. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

4. 執行應用程式：
```bash
streamlit run app.py
```

## 使用方式

1. 首次使用時，系統會自動下載並處理PDF文件
2. 在側邊欄中可以查看已載入的文件
3. 在主頁面輸入您的問題，系統會基於茶葉知識庫回答

## 技術架構

- **前端**: Streamlit
- **RAG框架**: LlamaIndex
- **LLM**: Groq
- **嵌入模型**: HuggingFace Sentence Transformers
- **向量資料庫**: ChromaDB 