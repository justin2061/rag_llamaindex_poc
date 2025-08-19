import os
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict
import streamlit as st

# RAG System Imports - for factory function
from config import RAG_SYSTEM_TYPE
from enhanced_rag_system import EnhancedRAGSystem
from elasticsearch_rag_system import ElasticsearchRAGSystem

# 嘗試導入 Graph RAG 系統，如果失敗則設為 None
try:
    from graph_rag_system import GraphRAGSystem
    GRAPH_RAG_AVAILABLE = True
except ImportError as e:
    GraphRAGSystem = None
    GRAPH_RAG_AVAILABLE = False
    # Graph RAG 依賴不可用，這是正常的（已禁用 Graph RAG 功能）

def get_rag_system():
    """
    工廠函式：根據設定回傳對應的 RAG 系統實例。
    """
    st.info(f"🚀 正在根據設定 '{RAG_SYSTEM_TYPE}' 初始化 RAG 系統...")
    
    if RAG_SYSTEM_TYPE == "graph":
        if GRAPH_RAG_AVAILABLE:
            st.session_state.rag_system_type = "Graph RAG"
            return GraphRAGSystem()
        else:
            st.warning("⚠️ Graph RAG 系統不可用（缺少 pyvis 依賴），回退到 Enhanced RAG")
            st.session_state.rag_system_type = "Enhanced RAG (Graph RAG Fallback)"
            return EnhancedRAGSystem()
    elif RAG_SYSTEM_TYPE == "elasticsearch":
        st.session_state.rag_system_type = "Elasticsearch RAG"
        return ElasticsearchRAGSystem()
    elif RAG_SYSTEM_TYPE == "enhanced":
        st.session_state.rag_system_type = "Enhanced RAG"
        return EnhancedRAGSystem()
    else:
        # 預設或錯誤情況
        st.warning(f"⚠️ 設定的 RAG_SYSTEM_TYPE ('{RAG_SYSTEM_TYPE}') 無效，將使用預設的 'enhanced' 系統。")
        st.session_state.rag_system_type = "Enhanced RAG (Default)"
        return EnhancedRAGSystem()

def extract_pdf_links_from_page(url: str) -> List[str]:
    """從網頁中提取PDF連結"""
    try:
        # 添加請求標頭避免被阻擋
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 尋找所有PDF連結 - 使用多種方式
        pdf_links = set()  # 使用set避免重複
        
        # 方法1: 檢查href屬性中包含.pdf的連結
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if '.pdf' in href:
                full_url = _make_absolute_url(link['href'], url)
                if full_url:
                    pdf_links.add(full_url)
        
        # 方法2: 檢查連結文字中包含PDF的連結
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().lower()
            if 'pdf' in link_text or '檔案' in link_text or '下載' in link_text:
                href = link['href']
                # 檢查是否可能是PDF文件連結
                if any(keyword in href.lower() for keyword in ['.pdf', 'download', 'file', 'doc']):
                    full_url = _make_absolute_url(href, url)
                    if full_url:
                        pdf_links.add(full_url)
        
        # 方法3: 查找特定的台茶改場PDF連結模式
        for link in soup.find_all('a', href=True):
            href = link['href']
            # 台茶改場的文件通常在 /files/ 路徑下
            if '/files/' in href and any(ext in href.lower() for ext in ['.pdf', 'a01_']):
                full_url = _make_absolute_url(href, url)
                if full_url:
                    pdf_links.add(full_url)
        
        pdf_list = list(pdf_links)
        
        # 除錯資訊
        st.write(f"🔍 在 {url} 找到 {len(pdf_list)} 個PDF連結")
        if pdf_list:
            st.write("📄 發現的PDF連結:")
            for i, link in enumerate(pdf_list[:5]):  # 只顯示前5個
                st.write(f"  {i+1}. {link}")
            if len(pdf_list) > 5:
                st.write(f"  ... 還有 {len(pdf_list)-5} 個連結")
        
        return pdf_list
        
    except Exception as e:
        st.error(f"❌ 從 {url} 提取PDF連結時發生錯誤: {str(e)}")
        return []

def _make_absolute_url(href: str, base_url: str) -> str:
    """將相對路徑轉換為絕對路徑"""
    try:
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            # 取得網站根域名
            base_domain = "https://www.tbrs.gov.tw"
            return base_domain + href
        elif href.startswith('../'):
            # 處理相對路徑
            base_parts = base_url.split('/')
            href_parts = href.split('/')
            
            # 移除 '../' 並調整路徑
            for part in href_parts:
                if part == '..':
                    if len(base_parts) > 3:  # 保留協議和域名
                        base_parts.pop()
                elif part:
                    base_parts.append(part)
            
            return '/'.join(base_parts)
        else:
            # 其他相對路徑
            base_path = base_url.rsplit('/', 1)[0]
            return f"{base_path}/{href}"
    except:
        return ""

def clean_text(text: str) -> str:
    """清理文本內容"""
    # 移除多餘的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    return text.strip()

def validate_groq_api_key(api_key: str) -> bool:
    """驗證Groq API Key"""
    if not api_key or api_key == "your_groq_api_key_here":
        return False
    
    # 基本格式檢查
    if len(api_key) < 20:
        return False
    
    return True

def format_response(response: str) -> str:
    """格式化回應文本"""
    # 確保回應以適當的標點符號結尾
    if response and not response.endswith(('.', '!', '?', '。', '！', '？')):
        response += '。'
    
    return response

def get_file_size(filepath: str) -> str:
    """取得檔案大小的友善顯示"""
    try:
        size = os.path.getsize(filepath)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "未知"

def create_progress_callback():
    """創建進度回調函數"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(current: int, total: int, message: str = ""):
        progress = current / total if total > 0 else 0
        progress_bar.progress(progress)
        status_text.text(f"{message} ({current}/{total})")
    
    return update_progress
 