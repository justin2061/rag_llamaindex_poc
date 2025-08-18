#!/usr/bin/env python3
"""
台灣茶葉知識RAG系統啟動腳本
"""

import os
import sys
import subprocess

def check_requirements():
    """檢查依賴套件"""
    try:
        import streamlit
        import llama_index
        import groq
        print("✅ 所有依賴套件已安裝")
        return True
    except ImportError as e:
        print(f"❌ 缺少依賴套件: {e}")
        print("請執行: pip install -r requirements.txt")
        return False

def check_env_file():
    """檢查環境變數檔案"""
    if not os.path.exists('.env'):
        print("❌ 找不到 .env 檔案")
        print("請複製 .env.example 為 .env 並設定您的 Groq API Key")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key or groq_key == 'your_groq_api_key_here':
        print("❌ 請在 .env 檔案中設定正確的 GROQ_API_KEY")
        return False
    
    print("✅ 環境變數設定正確")
    return True

def run_app(app_name="main_app.py"):
    """啟動應用程式"""
    if not check_requirements():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)
    
    print(f"🚀 啟動 {app_name}...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_name,
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 再見！")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    # 選擇要啟動的應用程式
    if len(sys.argv) > 1 and sys.argv[1] == "enhanced":
        run_app("enhanced_ui_app.py")
    else:
        run_app("main_app.py") 