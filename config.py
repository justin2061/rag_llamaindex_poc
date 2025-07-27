import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# API 設定
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# PDF 來源網址
PDF_SOURCES = {
    "茶業研究彙報": [
        "https://www.tbrs.gov.tw/files/tbrs/web_structure/4399/A01_1.pdf",  # 第1期
        "https://www.tbrs.gov.tw/files/tbrs/web_structure/4410/A01_1.pdf",  # 第2期
        "https://www.tbrs.gov.tw/files/tbrs/web_structure/4427/A01_1.pdf",  # 第3期
    ],
    "茶業專訊與其他文件": [
        # 這裡可以加入更多從網頁上找到的PDF連結
    ]
}

# 網頁來源 - 用於自動發現PDF連結
WEB_SOURCES = [
    "https://www.tbrs.gov.tw/ws.php?id=4189",  # 台灣茶業研究彙報摘要
    "https://www.tbrs.gov.tw/ws.php?id=1569",  # 其他茶業相關頁面
]

# 模型設定
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq 模型

# 檔案路徑設定
DATA_DIR = "data"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
INDEX_DIR = os.path.join(DATA_DIR, "index")

# 建立目錄
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

# Google Gemini設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ENABLE_OCR = os.getenv("ENABLE_OCR", "true").lower() == "true"

# 檔案上傳設定
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 5))
SUPPORTED_FILE_TYPES = os.getenv("SUPPORTED_FILE_TYPES", "pdf,txt,docx,md,png,jpg,jpeg,webp,bmp").split(',')
MAX_UPLOAD_FILES = int(os.getenv("MAX_UPLOAD_FILES", 50))

# 對話記憶設定
CONVERSATION_MEMORY_STEPS = int(os.getenv("CONVERSATION_MEMORY_STEPS", 5))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", 4000))
ENABLE_CONVERSATION_MEMORY = os.getenv("ENABLE_CONVERSATION_MEMORY", "true").lower() == "true"

# 檔案路徑設定
USER_UPLOADS_DIR = os.path.join(DATA_DIR, "user_uploads")

# 建立目錄
os.makedirs(USER_UPLOADS_DIR, exist_ok=True)

# Streamlit 設定
PAGE_TITLE = "台灣茶葉知識問答系統"
PAGE_ICON = "🍵"
