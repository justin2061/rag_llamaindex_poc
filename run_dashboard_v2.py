#!/usr/bin/env python3
"""
RAG 系統 Dashboard V2.0 啟動腳本
API串接版本的Streamlit應用啟動器
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_api_availability():
    """檢查API服務是否可用"""
    import requests
    
    # 檢查是否在容器內運行
    in_container = os.path.exists('/.dockerenv')
    if in_container:
        api_url = os.getenv("API_BASE_URL", "http://rag-enhanced-api:8000")
    else:
        api_url = os.getenv("API_BASE_URL", "http://localhost:8003")
    
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API服務正常 - 版本: {data.get('api_version', 'N/A')}")
            return True
        else:
            print(f"⚠️ API服務異常 - 狀態碼: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 無法連接API服務: {e}")
        print(f"請確認API服務在 {api_url} 運行")
        return False

def main():
    """主函數"""
    print("🚀 RAG 系統 Dashboard V2.0 啟動中...")
    print("="*50)
    
    # 設置環境變數 - 檢查是否在容器內運行
    in_container = os.path.exists('/.dockerenv')
    if in_container:
        api_base_url = os.getenv("API_BASE_URL", "http://rag-enhanced-api:8000")
    else:
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8003")
    streamlit_port = os.getenv("STREAMLIT_PORT", "8501")
    
    print(f"📡 API服務地址: {api_base_url}")
    print(f"🌐 Streamlit端口: {streamlit_port}")
    
    # 檢查API服務
    print("\n🔍 檢查API服務狀態...")
    if not check_api_availability():
        print("\n💡 請先啟動Enhanced RAG API V2.0:")
        print("   docker-compose up -d enhanced-api")
        print("   或")  
        print("   python run_enhanced_api.py")
        return 1
    
    # 準備Streamlit命令
    app_path = project_root / "apps" / "dashboard_app_v2.py"
    
    streamlit_cmd = [
        "streamlit", "run",
        str(app_path),
        "--server.port", streamlit_port,
        "--server.address", "0.0.0.0",
        "--browser.gatherUsageStats", "false",
        "--theme.primaryColor", "#3b82f6",
        "--theme.backgroundColor", "#ffffff",
        "--theme.secondaryBackgroundColor", "#f8fafc",
        "--theme.textColor", "#1f2937"
    ]
    
    print(f"\n🎯 啟動Dashboard V2.0...")
    print(f"📱 訪問地址: http://localhost:{streamlit_port}")
    print("="*50)
    
    try:
        # 啟動Streamlit應用
        result = subprocess.run(streamlit_cmd, cwd=project_root)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n👋 用戶中斷，正在關閉...")
        return 0
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)