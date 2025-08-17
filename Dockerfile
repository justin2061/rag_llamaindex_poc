# 使用官方 Python 3.11 基礎映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 安裝系統依賴 (Graph RAG 需要的額外套件)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libmupdf-dev \
    mupdf-tools \
    git \
    wget \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip 和安裝基礎工具
RUN pip install --upgrade pip setuptools wheel

# 複製 requirements 檔案並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 創建資料目錄和工作目錄結構
RUN mkdir -p data/pdfs data/index data/user_uploads data/chroma_db

# 注意：應用程式代碼透過 volume 掛載，不在此複製

# 暴露 Streamlit 預設端口
EXPOSE 8501

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 啟動新的主應用程式
CMD ["streamlit", "run", "main_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
