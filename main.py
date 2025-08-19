#!/usr/bin/env python3
"""
RAG LlamaIndex POC - 主入口點
提供多種應用程式模式的統一啟動方式
"""

import sys
import os
import argparse
from pathlib import Path

# 添加項目根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_simple_app():
    """運行簡化版應用程式"""
    os.system(f"streamlit run {PROJECT_ROOT}/apps/simple_app.py")

def run_main_app():
    """運行主要應用程式"""
    os.system(f"streamlit run {PROJECT_ROOT}/apps/main_app.py")

def run_enhanced_app():
    """運行增強版應用程式"""
    os.system(f"streamlit run {PROJECT_ROOT}/apps/enhanced_ui_app.py")

def run_graph_rag():
    """運行 Graph RAG 應用程式"""
    os.system(f"python {PROJECT_ROOT}/apps/run_graphrag.py")

def main():
    parser = argparse.ArgumentParser(description="RAG LlamaIndex POC 啟動器")
    parser.add_argument(
        "app", 
        choices=["simple", "main", "enhanced", "graphrag"],
        help="選擇要運行的應用程式"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 啟動 {args.app} 應用程式...")
    
    if args.app == "simple":
        run_simple_app()
    elif args.app == "main":
        run_main_app()
    elif args.app == "enhanced":
        run_enhanced_app()
    elif args.app == "graphrag":
        run_graph_rag()

if __name__ == "__main__":
    main()