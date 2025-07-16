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

# Streamlit 設定
PAGE_TITLE = "台灣茶葉知識問答系統"
PAGE_ICON = "🍵" 