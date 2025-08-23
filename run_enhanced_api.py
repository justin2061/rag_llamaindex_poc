#!/usr/bin/env python3
"""
Enhanced RAG API 啟動腳本
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    # 環境配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    print(f"🚀 啟動 Enhanced RAG API")
    print(f"📍 地址: http://{host}:{port}")
    print(f"📖 API 文檔: http://{host}:{port}/docs")
    print(f"🔄 自動重載: {'開啟' if reload else '關閉'}")
    
    # 啟動 API 服務
    uvicorn.run(
        "api.enhanced_api:app",
        host=host,
        port=port,
        reload=reload,
        access_log=True,
        log_level="info"
    )