import os
import requests
from typing import List, Dict
import streamlit as st
from config import PDF_SOURCES, PDF_DIR

class PDFDownloader:
    def __init__(self):
        self.pdf_dir = PDF_DIR
        
    def download_pdf(self, url: str, filename: str) -> bool:
        """下載單個PDF檔案"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.pdf_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            st.error(f"下載 {filename} 時發生錯誤: {str(e)}")
            return False
    
    def download_all_pdfs(self) -> Dict[str, List[str]]:
        """下載所有PDF檔案"""
        downloaded_files = {}
        
        with st.spinner("正在下載PDF檔案..."):
            for category, urls in PDF_SOURCES.items():
                downloaded_files[category] = []
                
                for i, url in enumerate(urls):
                    filename = f"{category}_{i+1}.pdf"
                    filepath = os.path.join(self.pdf_dir, filename)
                    
                    # 檢查檔案是否已存在
                    if os.path.exists(filepath):
                        st.info(f"檔案已存在: {filename}")
                        downloaded_files[category].append(filepath)
                        continue
                    
                    # 下載檔案
                    if self.download_pdf(url, filename):
                        st.success(f"成功下載: {filename}")
                        downloaded_files[category].append(filepath)
                    else:
                        st.error(f"下載失敗: {filename}")
        
        return downloaded_files
    
    def get_existing_pdfs(self) -> List[str]:
        """取得已存在的PDF檔案列表"""
        if not os.path.exists(self.pdf_dir):
            return []
        
        pdf_files = []
        for filename in os.listdir(self.pdf_dir):
            if filename.endswith('.pdf'):
                pdf_files.append(os.path.join(self.pdf_dir, filename))
        
        return pdf_files 