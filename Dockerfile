# 使用官方 Python 3.11 基礎映像 (更穩定的版本)
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安裝系統依賴 (解決 PyMuPDF 編譯問題)
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
    && rm -rf /var/lib/apt/lists/*

# 升級 pip 和安裝基礎工具
RUN pip install --upgrade pip setuptools wheel

# 複製 requirements 檔案
COPY requirements.txt .

# 安裝 Python 依賴 (分階段安裝避免記憶體問題)
RUN pip install --no-cache-dir numpy pandas
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir sentence-transformers
RUN pip install --no-cache-dir streamlit
RUN pip install --no-cache-dir llama-index
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建資料目錄
RUN mkdir -p data/pdfs data/index

# 暴露 Streamlit 預設端口
EXPOSE 8501

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 啟動命令
CMD ["streamlit", "run", "enhanced_ui_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
