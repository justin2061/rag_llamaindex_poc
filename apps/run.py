#!/usr/bin/env python3
"""
RAG 智能文檔問答助理啟動腳本
"""

import os
import sys
import subprocess
from pathlib import Path

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
        print("請複製 .env.example 為 .env 並設定您的 API Key")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key or groq_key == 'your_groq_api_key_here':
        print("❌ 請在 .env 檔案中設定正確的 GROQ_API_KEY")
        return False
    
    print("✅ 環境變數設定正確")
    return True

def get_app_choice():
    """獲取應用程式選擇"""
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
        if choice == "simple":
            return "simple_app.py"
        elif choice == "main":
            return "main_app.py"
        elif choice == "enhanced":
            return "enhanced_app.py"
        elif choice == "basic":
            return "app.py"
        elif choice == "quick":
            return "quick_start.py"
        elif choice == "benchmark":
            return "rag_system_benchmark.py"
        else:
            print(f"未知的應用程式選擇: {choice}")
            return None
    
    # 沒有參數時顯示選單
    return show_menu()

def show_menu():
    """顯示應用程式選單"""
    print("🤖 RAG 智能文檔問答助理")
    print("=" * 50)
    print("請選擇要啟動的版本:")
    print()
    print("1. simple      - 🎯 簡化版 (推薦) - 僅知識庫管理+問答")
    print("2. main        - 🌟 完整版 - 所有功能")
    print("3. enhanced    - 🚀 增強版 - 傳統功能")  
    print("4. basic       - 📝 基礎版")
    print("5. quick       - ⚡ 快速啟動版")
    print("6. benchmark   - 📊 效能測試")
    print()
    
    while True:
        choice = input("請輸入選擇 (1-6，或按 Enter 使用簡化版): ").strip()
        
        if choice == "" or choice == "1":
            return "simple_app.py"
        elif choice == "2":
            return "main_app.py"
        elif choice == "3":
            return "enhanced_app.py"
        elif choice == "4":
            return "app.py"
        elif choice == "5":
            return "quick_start.py"
        elif choice == "6":
            return "rag_system_benchmark.py"
        else:
            print("無效選擇，請重新輸入")

def run_app(app_name):
    """啟動應用程式"""
    if not check_requirements():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)
    
    # 檢查檔案是否存在
    if not Path(app_name).exists():
        print(f"❌ 找不到檔案 {app_name}")
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
    app_file = get_app_choice()
    
    if app_file is None:
        sys.exit(1)
    
    run_app(app_file) 