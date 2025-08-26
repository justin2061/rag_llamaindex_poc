# Requirements 管理結構

這個目錄包含了項目的所有依賴管理文件，採用模組化設計。

## 文件結構

- **`base.txt`** - 核心 RAG 系統依賴，被其他文件引用
- **`api.txt`** - API 服務專用依賴 (包含 base.txt)
- **`dashboard.txt`** - Dashboard UI 專用依賴 (包含 base.txt)  
- **`dev.txt`** - 開發和測試環境依賴 (包含 api.txt 和 dashboard.txt)

## 使用方法

### 不同模式安裝

```bash
# Dashboard 模式 (默認)
pip install -r requirements.txt

# API 模式
pip install -r requirements/api.txt

# 開發模式 (包含所有功能)
pip install -r requirements/dev.txt
```

### Docker 構建

- **API 容器**: 使用 `api/requirements_api.txt` → `requirements/api.txt`
- **Dashboard 容器**: 使用 `requirements.txt` → `requirements/dashboard.txt`

## 核心依賴

### LlamaIndex 生態系統
- `llama-index` - 核心框架
- `llama-index-llms-groq` - Groq LLM 支援
- `llama-index-embeddings-jinaai` - Jina 嵌入模型 (推薦)
- `llama-index-vector-stores-elasticsearch` - Elasticsearch 支援

### 向量資料庫
- `elasticsearch` - 主要向量存儲

### 文檔處理
- `PyMuPDF` - PDF 處理
- `python-docx` - Word 文檔支援
- `beautifulsoup4` - HTML 解析

### API 服務 (api.txt)
- `fastapi` - API 框架
- `uvicorn` - ASGI 服務器
- `python-multipart` - 文件上傳支援

### UI 界面 (dashboard.txt)
- `streamlit` - Web UI 框架
- `streamlit-option-menu` - UI 組件

## 維護指南

1. **更新基礎依賴**: 修改 `base.txt`
2. **添加 API 功能**: 修改 `api.txt`
3. **添加 UI 功能**: 修改 `dashboard.txt`
4. **添加開發工具**: 修改 `dev.txt`

所有更改會自動影響引用這些文件的其他 requirements 文件。