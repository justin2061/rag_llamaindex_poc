#!/usr/bin/env python3
"""
RAG Dashboard 應用啟動腳本
"""

import subprocess
import sys
from pathlib import Path

def main():
    """啟動 Dashboard 應用"""
    dashboard_app = Path(__file__).parent / "apps" / "dashboard_app.py"
    
    if not dashboard_app.exists():
        print("❌ Dashboard 應用文件不存在")
        return
    
    print("🚀 正在啟動 RAG Dashboard...")
    print("📊 界面包含：Dashboard, 知識庫管理, 智能問答")
    print("🌐 請在瀏覽器中打開: http://localhost:8501")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_app),
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard 已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    main()