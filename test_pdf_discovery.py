#!/usr/bin/env python3
"""
測試PDF連結發現功能
"""

import sys
sys.path.append('.')

from utils import extract_pdf_links_from_page
from config import WEB_SOURCES

def test_pdf_discovery():
    """測試PDF連結發現功能"""
    print("🔍 測試台灣茶改場網站PDF連結發現功能\n")
    
    for i, url in enumerate(WEB_SOURCES, 1):
        print(f"📍 測試來源 {i}: {url}")
        print("-" * 60)
        
        try:
            pdf_links = extract_pdf_links_from_page(url)
            
            if pdf_links:
                print(f"✅ 成功找到 {len(pdf_links)} 個PDF連結:")
                for j, link in enumerate(pdf_links, 1):
                    print(f"  {j:2d}. {link}")
            else:
                print("❌ 未找到PDF連結")
                
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    test_pdf_discovery() 