"""
Graph RAG 智能文檔問答系統啟動腳本
基於 LlamaIndex + Streamlit 的知識圖譜問答系統
"""

import streamlit as st
import os
import sys
from pathlib import Path

# 確保正確的模組路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_requirements():
    """檢查依賴套件是否已安裝"""
    required_packages = [
        'streamlit',
        'llama-index',
        'networkx',
        'pyvis',
        'streamlit-option-menu',
        'python-docx',
        # 'chromadb'  # 不再必需，已改用 Elasticsearch
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少以下套件，請先安裝: {', '.join(missing_packages)}")
        print("運行: pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """檢查環境變數配置"""
    env_file = current_dir / '.env'
    
    if not env_file.exists():
        print("⚠️ 未找到 .env 檔案")
        print("請根據 .env.example 創建 .env 檔案並設定 API 金鑰")
        return False
    
    # 載入環境變數
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not groq_key:
        print("⚠️ 請在 .env 檔案中設定 GROQ_API_KEY")
        return False
    
    print("✅ 環境設定檢查通過")
    return True

def main():
    """主啟動函數"""
    print("🚀 啟動 Graph RAG 智能文檔問答系統...")
    print("=" * 50)
    
    # 檢查依賴
    if not check_requirements():
        return
    
    # 檢查環境
    if not check_environment():
        return
    
    # 設定 Streamlit 配置
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    print("🔧 系統配置:")
    print(f"   • Python: {sys.version.split()[0]}")
    print(f"   • 工作目錄: {current_dir}")
    print(f"   • 主應用程式: main_app.py")
    
    from config import ENABLE_GRAPH_RAG
    mode = "Graph RAG" if ENABLE_GRAPH_RAG else "Enhanced RAG"
    print(f"   • RAG 模式: {mode}")
    
    print("\n🌐 啟動 Streamlit 應用程式...")
    print("   訪問網址: http://localhost:8501")
    print("   按 Ctrl+C 停止服務")
    print("=" * 50)
    
    # 啟動主應用程式
    try:
        # 直接運行主應用程式
        from main_app import main
        main()
        
    except ImportError as e:
        print(f"❌ 模組導入失敗: {e}")
        print("請確保所有相依套件都已正確安裝")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    # 使用 streamlit run 命令啟動
    import subprocess
    import sys
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(current_dir / "main_app.py"),
            "--server.port=8501",
            "--server.headless=true",
            "--browser.gather_usage_stats=false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 系統已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        main()  # 回退到直接啟動
