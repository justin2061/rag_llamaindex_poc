import os
import requests
from typing import List, Dict
import streamlit as st
from utils import extract_pdf_links_from_page, get_file_size
from config import PDF_DIR

class EnhancedPDFDownloader:
    def __init__(self):
        self.pdf_dir = PDF_DIR
        self.discovered_links = {}
        
    def discover_pdf_links(self, urls: List[str]) -> Dict[str, List[str]]:
        """自動發現網頁中的PDF連結"""
        discovered = {}
        
        with st.spinner("正在搜尋PDF連結..."):
            for url in urls:
                st.info(f"正在搜尋: {url}")
                pdf_links = extract_pdf_links_from_page(url)
                
                if pdf_links:
                    discovered[url] = pdf_links
                    st.success(f"找到 {len(pdf_links)} 個PDF檔案")
                else:
                    st.warning(f"未找到PDF檔案: {url}")
        
        self.discovered_links = discovered
        return discovered
    
    def download_pdf(self, url: str, filename: str) -> bool:
        """下載單個PDF檔案"""
        try:
            # 添加請求標頭以避免被阻擋
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()
            
            filepath = os.path.join(self.pdf_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 驗證檔案是否成功下載
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                file_size = get_file_size(filepath)
                st.success(f"✅ 下載成功: {filename} ({file_size})")
                return True
            else:
                st.error(f"❌ 下載失敗: {filename} (檔案大小為0)")
                return False
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 下載 {filename} 時發生網路錯誤: {str(e)}")
            return False
        except Exception as e:
            st.error(f"❌ 下載 {filename} 時發生錯誤: {str(e)}")
            return False
    
    def download_from_discovered_links(self) -> Dict[str, List[str]]:
        """從自動發現的連結下載PDF檔案"""
        downloaded_files = {}
        
        if not self.discovered_links:
            st.warning("尚未發現任何PDF連結，請先執行連結發現")
            return downloaded_files
        
        total_files = sum(len(links) for links in self.discovered_links.values())
        current_file = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for source_url, pdf_links in self.discovered_links.items():
            downloaded_files[source_url] = []
            
            for i, pdf_url in enumerate(pdf_links):
                current_file += 1
                
                # 生成檔案名稱
                filename = f"doc_{current_file:03d}_{os.path.basename(pdf_url)}"
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
                
                filepath = os.path.join(self.pdf_dir, filename)
                
                # 更新進度
                progress = current_file / total_files
                progress_bar.progress(progress)
                status_text.text(f"正在下載: {filename} ({current_file}/{total_files})")
                
                # 檢查檔案是否已存在
                if os.path.exists(filepath):
                    st.info(f"📁 檔案已存在: {filename}")
                    downloaded_files[source_url].append(filepath)
                    continue
                
                # 下載檔案
                if self.download_pdf(pdf_url, filename):
                    downloaded_files[source_url].append(filepath)
        
        progress_bar.progress(1.0)
        status_text.text(f"下載完成! 共處理 {total_files} 個檔案")
        
        return downloaded_files
    
    def get_existing_pdfs(self) -> List[str]:
        """取得已存在的PDF檔案列表"""
        if not os.path.exists(self.pdf_dir):
            return []
        
        pdf_files = []
        for filename in os.listdir(self.pdf_dir):
            if filename.endswith('.pdf'):
                filepath = os.path.join(self.pdf_dir, filename)
                if os.path.getsize(filepath) > 0:  # 確保檔案不是空的
                    pdf_files.append(filepath)
        
        return pdf_files
    
    def get_pdf_info(self) -> Dict[str, Dict]:
        """取得PDF檔案資訊"""
        pdf_files = self.get_existing_pdfs()
        info = {}
        
        for filepath in pdf_files:
            filename = os.path.basename(filepath)
            info[filename] = {
                'path': filepath,
                'size': get_file_size(filepath),
                'modified': os.path.getmtime(filepath)
            }
        
        return info 