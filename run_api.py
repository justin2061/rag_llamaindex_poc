#!/usr/bin/env python3
"""
智能問答 API 啟動腳本
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def main():
    """主啟動函數"""
    try:
        import uvicorn
        from api.chat_api import app
        
        print("🚀 啟動智能問答 FastAPI 服務...")
        print("=" * 50)
        print(f"📁 項目目錄: {project_root}")
        print(f"🌐 API 服務地址: http://localhost:8002")
        print(f"📚 API 文檔: http://localhost:8002/docs")
        print(f"🔍 健康檢查: http://localhost:8002/api/health")
        print("=" * 50)
        print("按 Ctrl+C 停止服務")
        print()
        
        # 啟動 API 服務
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8002,
            reload=False,
            access_log=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ 缺少依賴套件: {e}")
        print("請安裝 FastAPI 和 Uvicorn:")
        print("pip install fastapi uvicorn")
        
    except KeyboardInterrupt:
        print("\n🛑 API 服務已停止")
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()