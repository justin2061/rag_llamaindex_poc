#!/usr/bin/env python3
"""
簡化版 RAG 知識問答系統
只包含核心功能：文件上傳、管理和問答
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import tempfile

# 系統導入
from elasticsearch_rag_system import ElasticsearchRAGSystem
from user_file_manager import UserFileManager
from config import GROQ_API_KEY, GEMINI_API_KEY, PAGE_TITLE, PAGE_ICON, JINA_API_KEY
from embedding_fix import setup_safe_embedding, prevent_openai_fallback

# 頁面配置
st.set_page_config(
    page_title="簡易知識問答",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
def init_system():
    """初始化系統"""
    # 防止 OpenAI 回退並設置嵌入模型
    if 'openai_prevented' not in st.session_state:
        from embedding_fix import prevent_openai_fallback
        prevent_openai_fallback()
        st.session_state.openai_prevented = True
    
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = ElasticsearchRAGSystem()
        st.session_state.rag_system_type = "Elasticsearch RAG"
        st.session_state.system_ready = False
    
    if 'file_manager' not in st.session_state:
        st.session_state.file_manager = UserFileManager()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def check_api_keys():
    """檢查 API 金鑰配置"""
    if not GROQ_API_KEY:
        st.error("❌ 請在 .env 文件中設定 GROQ_API_KEY")
        st.stop()
    
    if not GEMINI_API_KEY:
        st.warning("⚠️ 未設定 GEMINI_API_KEY，圖片 OCR 功能將不可用")

def render_file_upload():
    """文件上傳區域"""
    st.subheader("📤 上傳文檔")
    
    uploaded_files = st.file_uploader(
        "選擇要上傳的文檔",
        type=['pdf', 'txt', 'docx', 'md', 'png', 'jpg', 'jpeg', 'webp', 'bmp'],
        accept_multiple_files=True,
        help="支援 PDF、Word、文字檔、Markdown 和圖片格式"
    )
    
    if uploaded_files:
        st.write(f"已選擇 {len(uploaded_files)} 個文件：")
        
        # 顯示文件列表
        for i, file in enumerate(uploaded_files):
            file_size_mb = file.size / (1024 * 1024)
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                file_ext = Path(file.name).suffix.lower()
                icon = get_file_icon(file_ext)
                st.write(f"{icon} {file.name}")
            
            with col2:
                st.write(f"{file_size_mb:.1f} MB")
            
            with col3:
                # 文件驗證
                if st.session_state.file_manager.validate_file(file):
                    st.success("✅")
                else:
                    st.error("❌")
        
        # 處理文件按鈕
        if st.button("🚀 處理文檔並建立知識庫", type="primary", use_container_width=True):
            process_uploaded_files(uploaded_files)

def process_uploaded_files(uploaded_files):
    """處理上傳的文件"""
    with st.spinner("正在處理文檔..."):
        try:
            # 處理文件
            docs = st.session_state.rag_system.process_uploaded_files(uploaded_files)
            
            if docs:
                # 創建索引
                index = st.session_state.rag_system.create_index(docs)
                
                if index:
                    # 設置查詢引擎
                    st.session_state.rag_system.setup_query_engine()
                    st.session_state.system_ready = True
                    
                    st.success(f"✅ 成功處理 {len(docs)} 個文檔！知識庫已建立。")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ 知識庫建立失敗")
            else:
                st.error("❌ 文檔處理失敗，請檢查文件格式")
                
        except Exception as e:
            st.error(f"❌ 處理過程中發生錯誤: {str(e)}")

def render_file_manager():
    """文件管理區域"""
    st.subheader("📁 知識庫管理")
    
    if not st.session_state.system_ready:
        # 檢查是否有現有索引
        if st.session_state.rag_system.load_existing_index():
            st.session_state.system_ready = True
            st.success("✅ 載入現有知識庫")
            st.rerun()
        else:
            st.info("📝 尚未建立知識庫，請先上傳文檔")
            return
    
    try:
        # 獲取統計資訊 - 使用 Elasticsearch 專用方法
        stats = st.session_state.rag_system.get_enhanced_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 從 Elasticsearch 統計中獲取文檔數
            base_stats = stats.get("base_statistics", {})
            es_stats = stats.get("elasticsearch_stats", {})
            doc_count = base_stats.get("total_documents", 0) or es_stats.get("document_count", 0)
            st.metric("📄 文檔數量", doc_count)
        
        with col2:
            # 文本塊數等於文檔數（在 Elasticsearch 中）
            node_count = base_stats.get("total_nodes", 0) or es_stats.get("document_count", 0)
            st.metric("🧩 文本塊數", node_count)
        
        with col3:
            # 顯示 Elasticsearch 索引大小
            index_size_mb = es_stats.get("index_size_mb", 0)
            if index_size_mb > 0:
                st.metric("💾 索引大小", f"{index_size_mb} MB")
            else:
                st.metric("🕸️ 系統類型", "Elasticsearch RAG")
        
        # 用戶上傳文件管理
        if hasattr(st.session_state, 'file_manager'):
            upload_stats = st.session_state.file_manager.get_file_stats()
            
            if upload_stats['total_files'] > 0:
                st.markdown("---")
                st.markdown("### 📋 已上傳文件")
                
                # 文件列表
                upload_dir = st.session_state.file_manager.upload_dir
                if os.path.exists(upload_dir):
                    files = os.listdir(upload_dir)
                    
                    for file in files:
                        file_path = os.path.join(upload_dir, file)
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path) / (1024 * 1024)
                            
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                file_ext = Path(file).suffix.lower()
                                icon = get_file_icon(file_ext)
                                st.write(f"{icon} {file}")
                            
                            with col2:
                                st.write(f"{file_size:.1f} MB")
                            
                            with col3:
                                if st.button("🗑️", key=f"delete_{file}", help=f"刪除 {file}"):
                                    delete_file(file_path)
        
        # 清空知識庫選項
        st.markdown("---")
        if st.button("🗑️ 清空整個知識庫", type="secondary", help="這將刪除所有文檔和索引"):
            clear_knowledge_base()
            
    except Exception as e:
        st.error(f"❌ 無法獲取知識庫資訊: {str(e)}")

def delete_file(file_path):
    """刪除單個文件（包括本地文件和 Elasticsearch 中的對應文檔）"""
    try:
        filename = os.path.basename(file_path)
        
        # 1. 從 Elasticsearch 中刪除相關文檔
        if st.session_state.system_ready and hasattr(st.session_state.rag_system, 'delete_documents_by_source'):
            with st.spinner(f"正在從知識庫中移除 {filename} 的相關文檔..."):
                es_deleted = st.session_state.rag_system.delete_documents_by_source(filename)
                if es_deleted:
                    # 刷新索引
                    st.session_state.rag_system.refresh_index_after_deletion()
        
        # 2. 刪除本地文件
        if os.path.exists(file_path):
            os.remove(file_path)
            st.success(f"✅ 本地文件 {filename} 已刪除")
        
        # 3. 檢查是否還有其他文檔，如果沒有則重置系統狀態
        upload_stats = st.session_state.file_manager.get_file_stats()
        if upload_stats['total_files'] == 0:
            # 沒有文件了，檢查知識庫是否也空了
            stats = st.session_state.rag_system.get_enhanced_statistics()
            es_stats = stats.get("elasticsearch_stats", {})
            doc_count = es_stats.get("document_count", 0)
            
            if doc_count == 0:
                st.session_state.system_ready = False
                st.info("📝 所有文檔已刪除，知識庫已清空")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 刪除失敗: {str(e)}")
        import traceback
        st.error(f"詳細錯誤: {traceback.format_exc()}")

def clear_knowledge_base():
    """完全清空知識庫（包括 Elasticsearch 和 SimpleVectorStore）"""
    try:
        # 1. 清除 SimpleVectorStore 索引
        from config import INDEX_DIR
        if os.path.exists(INDEX_DIR):
            import shutil
            shutil.rmtree(INDEX_DIR)
            os.makedirs(INDEX_DIR, exist_ok=True)
            st.info("✅ SimpleVectorStore 已清空")
        
        # 2. 清除 Elasticsearch 索引
        rag_system = st.session_state.rag_system
        if hasattr(rag_system, 'elasticsearch_client') and rag_system.elasticsearch_client:
            try:
                from config import ELASTICSEARCH_INDEX_NAME
                index_name = ELASTICSEARCH_INDEX_NAME or 'rag_intelligent_assistant'
                
                if rag_system.elasticsearch_client.indices.exists(index=index_name):
                    rag_system.elasticsearch_client.indices.delete(index=index_name)
                    st.info(f"✅ Elasticsearch 索引 {index_name} 已刪除")
                
            except Exception as es_e:
                st.warning(f"清空 Elasticsearch 時遇到問題: {str(es_e)}")
        
        # 3. 清除上傳文件
        upload_dir = st.session_state.file_manager.upload_dir
        if os.path.exists(upload_dir):
            import shutil
            shutil.rmtree(upload_dir)
            os.makedirs(upload_dir, exist_ok=True)
            st.info("✅ 用戶上傳檔案已清空")
        
        # 4. 重置 RAG 系統狀態
        if hasattr(st.session_state.rag_system, 'index'):
            st.session_state.rag_system.index = None
        if hasattr(st.session_state.rag_system, 'query_engine'):
            st.session_state.rag_system.query_engine = None
        
        # 5. 重置界面狀態
        st.session_state.system_ready = False
        st.session_state.chat_history = []
        
        st.success("🎉 所有知識庫數據已完全清空")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 清空失敗: {str(e)}")

def render_chat_interface():
    """問答界面"""
    st.subheader("💬 智能問答")
    
    if not st.session_state.system_ready:
        st.info("📚 請先上傳文檔建立知識庫")
        return
    
    # 顯示聊天歷史
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.write(chat["content"])
            if chat["role"] == "assistant" and "sources" in chat:
                with st.expander("📚 參考來源", expanded=False):
                    for source in chat["sources"]:
                        st.write(f"• {source}")
    
    # 用戶輸入
    if prompt := st.chat_input("請輸入您的問題..."):
        # 添加用戶訊息
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                try:
                    # 根據系統類型選擇查詢方法
                    system_type = st.session_state.get('rag_system_type', '')
                    
                    if "Graph" in system_type:
                        response = st.session_state.rag_system.query_with_graph_context(prompt)
                        sources = ["知識圖譜", "用戶文檔"]
                    else:
                        response = st.session_state.rag_system.query_with_context(prompt)
                        sources = ["向量索引", "用戶文檔"]
                    
                    st.write(response)
                    
                    # 顯示來源
                    with st.expander("📚 參考來源", expanded=False):
                        for source in sources:
                            st.write(f"• {source}")
                    
                    # 添加助手訊息到歷史
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response,
                        "sources": sources
                    })
                    
                except Exception as e:
                    error_msg = f"❌ 處理問題時發生錯誤: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

def get_file_icon(file_ext):
    """根據文件擴展名返回圖示"""
    icons = {
        '.pdf': '📄',
        '.txt': '📝', 
        '.docx': '📘',
        '.doc': '📘',
        '.md': '📑',
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.webp': '🖼️',
        '.bmp': '🖼️'
    }
    return icons.get(file_ext, '📎')

def render_sidebar():
    """側邊欄"""
    with st.sidebar:
        st.title("🤖 智能助理")
        
        # API 狀態
        st.markdown("### 🔐 系統狀態")
        if GROQ_API_KEY:
            st.success("✅ Groq API 已配置")
        else:
            st.error("❌ Groq API 未配置")
            
        if GEMINI_API_KEY:
            st.success("✅ Gemini API 已配置")
        else:
            st.warning("⚠️ Gemini API 未配置")
        
        # 系統資訊
        if st.session_state.system_ready:
            st.markdown("### 📊 知識庫狀態")
            system_type = st.session_state.get('rag_system_type', 'Unknown')
            st.info(f"🕸️ 當前系統: {system_type}")
            
            try:
                stats = st.session_state.rag_system.get_enhanced_statistics()
                base_stats = stats.get("base_statistics", {})
                es_stats = stats.get("elasticsearch_stats", {})
                doc_count = base_stats.get("total_documents", 0) or es_stats.get("document_count", 0)
                st.metric("📄 文檔數", doc_count)
            except:
                pass
        
        st.markdown("---")
        
        # 清空對話歷史
        if st.button("🧹 清空對話", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        # 系統資訊
        st.markdown("---")
        st.markdown("### ℹ️ 關於")
        st.info("簡化版 RAG 問答系統\n\n僅包含核心功能：\n• 文檔上傳\n• 知識庫管理\n• 智能問答")

def main():
    """主程序"""
    # 檢查 API 配置
    check_api_keys()
    
    # 初始化系統
    init_system()
    
    # 渲染側邊欄
    render_sidebar()
    
    # 主頁面標題
    st.title("🤖 簡易知識問答系統")
    st.markdown("上傳文檔，建立專屬知識庫，開始智能問答")
    
    # 主內容區域
    tab1, tab2, tab3 = st.tabs(["📤 上傳文檔", "📁 管理知識庫", "💬 智能問答"])
    
    with tab1:
        render_file_upload()
    
    with tab2:
        render_file_manager()
    
    with tab3:
        render_chat_interface()

if __name__ == "__main__":
    main()