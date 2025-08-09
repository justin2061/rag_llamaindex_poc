#!/usr/bin/env python3
"""
Graph RAG 智能文檔問答助理 - 快速啟動腳本
優化版本，減少初始載入時間
"""

import streamlit as st
import os
import sys
from datetime import datetime

# 設定頁面配置（必須在最開始）
st.set_page_config(
    page_title="智能文檔問答助理",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_minimal_css():
    """載入最小化CSS樣式"""
    st.markdown("""
    <style>
    /* 基本樣式系統 */
    :root {
        --primary-color: #4f46e5;
        --success-color: #059669;
        --warning-color: #d97706;
        --error-color: #dc2626;
        --background-color: #ffffff;
        --text-primary: #111827;
        --border-color: #e5e7eb;
    }
    
    /* 隱藏Streamlit默認元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* 強制背景為白色 */
    .stApp, .main, .main > div {
        background-color: var(--background-color) !important;
    }
    
    /* 文字顏色 */
    .stApp, .main, p, div, span, label {
        color: var(--text-primary) !important;
    }
    
    /* 側邊欄樣式 */
    .stSidebar {
        background-color: var(--background-color) !important;
    }
    
    .stSidebar * {
        color: var(--text-primary) !important;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

def render_quick_header():
    """渲染快速標題"""
    st.markdown("""
    ## 🤖 智能文檔問答助理
    
    **基於 Graph RAG 的多模態知識問答系統**
    
    ---
    """)

def render_quick_navigation():
    """渲染快速導航"""
    with st.sidebar:
        st.markdown("### 📋 主選單")
        selected = st.radio(
            "選擇功能",
            options=["🏠 系統概述", "📚 快速上傳", "🍵 演示模式", "⚙️ 系統設定"],
            index=0,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # API 狀態檢查
        st.markdown("### 🔐 API 狀態")
        
        try:
            from config import GROQ_API_KEY, GEMINI_API_KEY
            
            if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
                st.success("✅ Groq API")
            else:
                st.error("❌ Groq API 未設定")
            
            if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
                st.success("✅ Gemini API")
            else:
                st.warning("⚠️ Gemini OCR 不可用")
                
        except ImportError:
            st.error("❌ 配置檔案載入失敗")
        
        return selected

def render_system_overview():
    """渲染系統概述"""
    st.markdown("""
    ## 🏠 系統概述
    
    歡迎使用智能文檔問答助理！這是一個基於 Graph RAG 技術的先進問答系統。
    
    ### 🌟 核心功能
    
    - **🕸️ 知識圖譜**: 自動建構文檔間的關係網絡
    - **📄 多格式支援**: PDF、Word、文字檔、圖片 OCR
    - **💬 智能對話**: 具備上下文記憶的問答功能
    - **📊 圖譜可視化**: 互動式知識圖譜展示
    
    ### 🚀 快速開始
    
    1. **檢查 API 配置** - 確保左側顯示 API 已設定
    2. **上傳文檔** - 點擊「快速上傳」開始
    3. **開始問答** - 系統處理完成後即可使用
    
    ### 📋 系統狀態
    """)
    
    # 系統狀態檢查
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            from config import ENABLE_GRAPH_RAG
            if ENABLE_GRAPH_RAG:
                st.info("🕸️ Graph RAG 模式已啟用")
            else:
                st.info("📚 Traditional RAG 模式")
        except:
            st.warning("⚠️ 配置檔案問題")
    
    with col2:
        # 檢查是否有現有資料
        try:
            from config import INDEX_DIR
            if os.path.exists(INDEX_DIR) and os.listdir(INDEX_DIR):
                st.success("📚 發現現有知識庫")
            else:
                st.info("📁 知識庫空白")
        except:
            st.warning("⚠️ 資料目錄問題")

def render_quick_upload():
    """渲染快速上傳"""
    st.markdown("## 📤 快速上傳")
    
    st.info("上傳您的文檔以建立知識庫")
    
    # 文件上傳器
    uploaded_files = st.file_uploader(
        "選擇文檔檔案",
        type=['pdf', 'txt', 'md', 'docx', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="支援 PDF、文字檔、Word 文檔和圖片（OCR）"
    )
    
    if uploaded_files:
        st.markdown("### 📋 上傳檔案清單")
        
        for i, file in enumerate(uploaded_files):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"📄 {file.name}")
            with col2:
                st.write(f"{file.size / 1024:.1f} KB")
            with col3:
                st.write(file.type.split('/')[-1].upper())
        
        st.markdown("---")
        
        if st.button("🚀 開始處理文檔", type="primary", use_container_width=True):
            process_uploaded_files(uploaded_files)

def process_uploaded_files(uploaded_files):
    """處理上傳的檔案"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("正在初始化系統...")
        progress_bar.progress(20)
        
        # 動態導入以減少初始載入時間
        from config import ENABLE_GRAPH_RAG
        
        if ENABLE_GRAPH_RAG:
            from graph_rag_system import GraphRAGSystem
            rag_system = GraphRAGSystem()
        else:
            from enhanced_rag_system import EnhancedRAGSystem
            rag_system = EnhancedRAGSystem()
        
        progress_bar.progress(40)
        status_text.text("正在處理上傳檔案...")
        
        # 處理檔案
        docs = rag_system.process_uploaded_files(uploaded_files)
        
        if docs:
            progress_bar.progress(70)
            status_text.text("正在建立索引...")
            
            # 建立索引
            index = rag_system.create_index(docs)
            
            if index:
                progress_bar.progress(90)
                status_text.text("正在設置查詢引擎...")
                
                if ENABLE_GRAPH_RAG:
                    rag_system.setup_graph_rag_retriever()
                else:
                    rag_system.setup_query_engine()
                
                progress_bar.progress(100)
                status_text.text("處理完成！")
                
                st.balloons()
                st.success(f"✅ 成功處理 {len(docs)} 個檔案！")
                
                # 儲存到 session state
                st.session_state.rag_system = rag_system
                st.session_state.system_ready = True
                
                # 顯示簡單問答界面
                render_simple_chat()
                
            else:
                st.error("❌ 索引建立失敗")
        else:
            st.error("❌ 檔案處理失敗")
            
    except Exception as e:
        st.error(f"❌ 處理過程發生錯誤: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

def render_simple_chat():
    """渲染簡單聊天界面"""
    st.markdown("---")
    st.markdown("## 💬 開始問答")
    
    # 初始化聊天歷史
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 顯示聊天歷史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 聊天輸入
    if prompt := st.chat_input("請輸入您的問題..."):
        # 顯示用戶訊息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成回應
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                try:
                    from config import ENABLE_GRAPH_RAG
                    
                    if ENABLE_GRAPH_RAG and hasattr(st.session_state, 'rag_system'):
                        response = st.session_state.rag_system.query_with_graph_context(prompt)
                    elif hasattr(st.session_state, 'rag_system'):
                        response = st.session_state.rag_system.query_with_context(prompt)
                    else:
                        response = "系統尚未初始化，請先上傳文檔。"
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"處理問題時發生錯誤: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def render_demo_mode():
    """渲染演示模式"""
    st.markdown("## 🍵 演示模式")
    
    st.info("演示模式將使用預設的茶葉知識庫來展示系統功能。")
    
    if st.button("🚀 載入茶葉演示", type="primary"):
        load_demo_system()

def load_demo_system():
    """載入演示系統"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("正在載入演示資料...")
        progress_bar.progress(20)
        
        from enhanced_pdf_downloader import EnhancedPDFDownloader
        from config import WEB_SOURCES, ENABLE_GRAPH_RAG
        
        downloader = EnhancedPDFDownloader()
        progress_bar.progress(40)
        
        # 嘗試載入現有 PDF
        all_pdfs = downloader.get_existing_pdfs()
        
        if not all_pdfs:
            status_text.text("正在下載演示資料...")
            discovered = downloader.discover_pdf_links(WEB_SOURCES)
            if discovered:
                downloaded_files = downloader.download_from_discovered_links()
            all_pdfs = downloader.get_existing_pdfs()
        
        if all_pdfs:
            progress_bar.progress(60)
            status_text.text("正在建立演示系統...")
            
            if ENABLE_GRAPH_RAG:
                from graph_rag_system import GraphRAGSystem
                demo_system = GraphRAGSystem()
            else:
                from enhanced_rag_system import EnhancedRAGSystem
                demo_system = EnhancedRAGSystem()
            
            progress_bar.progress(80)
            documents = demo_system.load_pdfs(all_pdfs)
            
            if documents:
                index = demo_system.create_index(documents)
                if index:
                    if ENABLE_GRAPH_RAG:
                        demo_system.setup_graph_rag_retriever()
                    else:
                        demo_system.setup_query_engine()
                    
                    progress_bar.progress(100)
                    status_text.text("演示系統載入完成！")
                    
                    st.session_state.demo_system = demo_system
                    st.session_state.demo_ready = True
                    
                    st.success("✅ 茶葉演示系統準備就緒！")
                    render_demo_chat()
                else:
                    st.error("❌ 演示系統索引建立失敗")
            else:
                st.error("❌ 演示資料載入失敗")
        else:
            st.error("❌ 沒有找到演示資料")
            
    except Exception as e:
        st.error(f"❌ 演示系統載入失敗: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

def render_demo_chat():
    """渲染演示聊天"""
    st.markdown("### 💬 茶葉知識問答")
    
    # 建議問題
    suggested_questions = [
        "台灣有哪些主要的茶樹品種？",
        "製茶的基本流程是什麼？",
        "如何進行茶葉品質評鑑？"
    ]
    
    st.markdown("**建議問題：**")
    for i, question in enumerate(suggested_questions):
        if st.button(f"💬 {question}", key=f"demo_q_{i}"):
            handle_demo_query(question)
    
    # 自由輸入
    if user_question := st.text_input("或輸入您的問題：", key="demo_input"):
        if st.button("🔍 詢問", key="demo_ask"):
            handle_demo_query(user_question)

def handle_demo_query(question: str):
    """處理演示查詢"""
    if hasattr(st.session_state, 'demo_system'):
        with st.spinner("正在分析茶葉知識..."):
            try:
                from config import ENABLE_GRAPH_RAG
                
                if ENABLE_GRAPH_RAG:
                    response = st.session_state.demo_system.query_with_graph_context(question)
                else:
                    response = st.session_state.demo_system.query_with_context(question)
                
                st.markdown(f"**問題：** {question}")
                st.markdown(f"**回答：** {response}")
                st.markdown("---")
                
            except Exception as e:
                st.error(f"查詢失敗: {str(e)}")

def render_settings():
    """渲染設定頁面"""
    st.markdown("## ⚙️ 系統設定")
    
    # API 設定
    with st.expander("🔐 API 配置", expanded=True):
        st.markdown("""
        ### 配置說明
        
        請在專案目錄的 `.env` 檔案中設定以下 API 金鑰：
        
        ```
        GROQ_API_KEY=your_groq_api_key_here
        GEMINI_API_KEY=your_gemini_api_key_here
        ```
        
        - **Groq API**: 必需，用於 LLM 推理 ([取得金鑰](https://console.groq.com/keys))
        - **Gemini API**: 可選，用於圖片 OCR ([取得金鑰](https://aistudio.google.com/app/apikey))
        """)
    
    # 系統資訊
    with st.expander("📋 系統資訊", expanded=True):
        try:
            from config import ENABLE_GRAPH_RAG, LLM_MODEL, EMBEDDING_MODEL
            
            st.markdown(f"""
            - **RAG 模式**: {'Graph RAG' if ENABLE_GRAPH_RAG else 'Traditional RAG'}
            - **LLM 模型**: {LLM_MODEL}
            - **嵌入模型**: {EMBEDDING_MODEL}
            - **前端框架**: Streamlit
            - **圖資料庫**: NetworkX
            """)
        except ImportError:
            st.warning("無法載入系統配置資訊")

def main():
    """主函數"""
    # 載入最小化樣式
    load_minimal_css()
    
    # 渲染標題
    render_quick_header()
    
    # 渲染導航
    selected_page = render_quick_navigation()
    
    # 根據選擇渲染內容
    if selected_page == "🏠 系統概述":
        render_system_overview()
    elif selected_page == "📚 快速上傳":
        render_quick_upload()
    elif selected_page == "🍵 演示模式":
        render_demo_mode()
    elif selected_page == "⚙️ 系統設定":
        render_settings()

if __name__ == "__main__":
    main()
