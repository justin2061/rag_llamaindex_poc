import streamlit as st
import os
from datetime import datetime

# 導入新的架構組件
from components.layout.main_layout import MainLayout
from components.knowledge_base.upload_zone import UploadZone
from components.chat.chat_interface import ChatInterface

# 導入系統核心
from graph_rag_system import GraphRAGSystem
from enhanced_rag_system import EnhancedRAGSystem
from enhanced_pdf_downloader import EnhancedPDFDownloader

# 導入配置
from config import (
    GROQ_API_KEY, GEMINI_API_KEY, WEB_SOURCES, 
    ENABLE_GRAPH_RAG, PAGE_TITLE, PAGE_ICON
)

# 避免重複設置頁面配置
if not hasattr(st.session_state, 'page_configured'):
    st.session_state.page_configured = True

# 移除不必要的緩存，改為延遲初始化
def init_layout():
    """初始化佈局管理器"""
    if 'layout' not in st.session_state:
        st.session_state.layout = MainLayout()
    return st.session_state.layout

def init_upload_zone():
    """初始化上傳區域"""
    if 'upload_zone' not in st.session_state:
        st.session_state.upload_zone = UploadZone()
    return st.session_state.upload_zone

def init_chat_interface():
    """初始化聊天介面"""
    if 'chat_interface' not in st.session_state:
        st.session_state.chat_interface = ChatInterface()
    return st.session_state.chat_interface

def init_rag_system():
    """初始化 RAG 系統"""
    if 'rag_system' not in st.session_state:
        if ENABLE_GRAPH_RAG:
            st.session_state.rag_system = GraphRAGSystem()
            st.session_state.system_type = "Graph RAG"
        else:
            st.session_state.rag_system = EnhancedRAGSystem()
            st.session_state.system_type = "Enhanced RAG"
        
        st.session_state.system_ready = False

def check_system_status():
    """檢查系統狀態"""
    if 'system_status_checked' not in st.session_state:
        st.session_state.system_status_checked = True
        
        # 檢查是否有現有索引
        from config import INDEX_DIR
        if os.path.exists(INDEX_DIR) and os.listdir(INDEX_DIR):
            st.session_state.has_existing_index = True
        else:
            st.session_state.has_existing_index = False
            
        # 檢查用戶上傳的檔案
        upload_zone = init_upload_zone()
        upload_stats = upload_zone.get_upload_stats()
        st.session_state.has_user_files = upload_stats['total_files'] > 0

def render_home_page(layout: MainLayout):
    """渲染首頁"""
    st.markdown("""
    <div class="custom-card">
        <h2>🏠 歡迎使用智能文檔問答助理</h2>
        <p>這是一個基於 Graph RAG 技術的先進問答系統，能夠理解文檔間的複雜關係並提供精確的答案。</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem;">
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 1rem; color: white;">
                <h3>🕸️ Graph RAG 技術</h3>
                <p>自動建構知識圖譜，發現實體間的深層關係，提供更精確的答案。</p>
            </div>
            
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 1rem; color: white;">
                <h3>📄 多格式支援</h3>
                <p>支援 PDF、Word、文字檔、Markdown 以及圖片 OCR，一站式處理各種文檔。</p>
            </div>
            
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 1rem; color: white;">
                <h3>💬 智能對話</h3>
                <p>具備上下文記憶功能，能夠進行連續對話並理解問題之間的關聯。</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 快速開始部分
    col1, col2 = layout.create_columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h3>🚀 快速開始</h3>
            <ol>
                <li><strong>上傳文檔</strong> - 點擊「我的知識庫」開始上傳</li>
                <li><strong>系統處理</strong> - AI 自動建構知識圖譜</li>
                <li><strong>開始問答</strong> - 基於圖譜進行智能對話</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown("### 📊 系統狀態")
            
            # 系統狀態檢查
            if GROQ_API_KEY:
                st.success("✅ Groq API 已配置")
            else:
                st.error("❌ Groq API 需要配置")
                
            if GEMINI_API_KEY:
                st.success("✅ Gemini API 已配置 (OCR 功能可用)")
            else:
                st.warning("⚠️ Gemini API 未配置 (OCR 功能不可用)")
                
            if st.session_state.get('has_existing_index', False):
                st.info("📚 發現現有知識庫")
            
            if st.session_state.get('has_user_files', False):
                st.info("📁 發現用戶上傳的檔案")

def render_knowledge_base_page(layout: MainLayout, upload_zone: UploadZone, chat_interface: ChatInterface):
    """渲染知識庫頁面"""
    init_rag_system()
    
    # 嘗試載入現有索引
    if not st.session_state.system_ready and st.session_state.get('has_existing_index', False):
        if st.session_state.rag_system.load_existing_index():
            st.session_state.system_ready = True
            layout.show_success("成功載入現有知識庫")
    
    # 檢查是否需要顯示上傳界面
    if not st.session_state.system_ready:
        # 空狀態 - 顯示上傳界面
        st.markdown("## 📤 建立您的知識庫")
        
        # 快速開始指南
        upload_zone.render_quick_start_guide()
        
        # 上傳區域
        uploaded_files = upload_zone.render_empty_state()
        
        # 上傳提示
        upload_zone.render_upload_tips()
        
        # 處理上傳的檔案
        if uploaded_files:
            st.markdown("---")
            
            # 顯示上傳進度
            progress_data = upload_zone.render_upload_progress(uploaded_files)
            
            # 處理檔案按鈕
            if st.button("🚀 開始處理檔案", type="primary", use_container_width=True):
                with st.spinner("正在處理您的檔案並建立知識圖譜..."):
                    try:
                        # 處理上傳的檔案
                        if ENABLE_GRAPH_RAG:
                            docs = st.session_state.rag_system.process_uploaded_files(uploaded_files)
                        else:
                            docs = st.session_state.rag_system.process_uploaded_files(uploaded_files)
                        
                        if docs:
                            # 建立索引（Graph RAG 或傳統 RAG）
                            index = st.session_state.rag_system.create_index(docs)
                            
                            if index:
                                if ENABLE_GRAPH_RAG:
                                    st.session_state.rag_system.setup_graph_rag_retriever()
                                else:
                                    st.session_state.rag_system.setup_query_engine()
                                
                                st.session_state.system_ready = True
                                
                                st.balloons()
                                layout.show_success(f"成功處理 {len(docs)} 個檔案！知識圖譜已建立完成。")
                                st.rerun()
                            else:
                                layout.show_error("索引建立失敗，請重試。")
                        else:
                            layout.show_error("檔案處理失敗，請檢查檔案格式。")
                            
                    except Exception as e:
                        layout.show_error(f"處理過程發生錯誤: {str(e)}")
    
    else:
        # 系統已就緒 - 顯示問答界面
        col1, col2 = layout.create_columns([2, 1])
        
        with col1:
            st.markdown("## 💬 智能問答")
            
            # 聊天界面
            render_chat_interface(chat_interface)
        
        with col2:
            st.markdown("## 📊 知識庫狀態")
            
            # 系統統計
            render_system_statistics()
            
            # 檔案管理
            with st.expander("📁 檔案管理", expanded=False):
                upload_zone.render_file_manager()
            
            # 更多檔案上傳
            additional_files = upload_zone.render_upload_with_files()
            if additional_files:
                if st.button("處理新檔案", type="secondary"):
                    # 處理新檔案邏輯
                    layout.show_info("正在處理新檔案...")

def render_chat_interface(chat_interface: ChatInterface):
    """渲染聊天介面"""
    # 顯示聊天歷史
    messages = chat_interface.get_messages()
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("📚 參考來源"):
                    for source in message["sources"]:
                        st.write(f"- {source}")
    
    # 用戶輸入
    if user_input := st.chat_input("請輸入您的問題..."):
        # 添加用戶訊息
        chat_interface.add_message("user", user_input)
        
        # 顯示用戶訊息
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 生成助手回應
        with st.chat_message("assistant"):
            with st.spinner("正在分析知識圖譜..."):
                try:
                    if ENABLE_GRAPH_RAG:
                        response = st.session_state.rag_system.query_with_graph_context(user_input)
                    else:
                        response = st.session_state.rag_system.query_with_context(user_input)
                    
                    st.markdown(response)
                    
                    # 添加助手訊息
                    sources = ["知識圖譜", "用戶文檔"]
                    chat_interface.add_message("assistant", response, sources)
                    
                except Exception as e:
                    error_msg = f"處理問題時發生錯誤: {str(e)}"
                    st.error(error_msg)
                    chat_interface.add_message("assistant", error_msg)

def render_system_statistics():
    """渲染系統統計資訊"""
    if 'rag_system' in st.session_state and st.session_state.system_ready:
        try:
            if ENABLE_GRAPH_RAG:
                stats = st.session_state.rag_system.get_graph_statistics()
                
                # 基本統計
                if "graph_stats" in stats:
                    graph_stats = stats["graph_stats"]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🕸️ 節點數", graph_stats.get("nodes_count", 0))
                        st.metric("📊 社群數", graph_stats.get("communities_count", 0))
                    
                    with col2:
                        st.metric("🔗 關係數", graph_stats.get("edges_count", 0))
                        st.metric("📈 圖密度", f"{graph_stats.get('density', 0):.3f}")
                
            else:
                stats = st.session_state.rag_system.get_enhanced_statistics()
                base_stats = stats.get("base_statistics", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 文檔數", base_stats.get("total_documents", 0))
                
                with col2:
                    st.metric("🧩 文本塊", base_stats.get("total_nodes", 0))
                    
        except Exception as e:
            st.warning(f"無法獲取統計資訊: {str(e)}")

def render_demo_page(layout: MainLayout):
    """渲染演示頁面"""
    st.markdown("## 🍵 茶葉知識演示")
    
    # 演示模式說明
    st.info("這是一個預建的茶葉知識庫演示，展示系統在專業領域的應用效果。")
    
    # 初始化演示系統
    if 'demo_system' not in st.session_state:
        st.session_state.demo_system = None
        st.session_state.demo_ready = False
    
    if not st.session_state.demo_ready:
        if st.button("🚀 載入茶葉演示資料", type="primary"):
            with st.spinner("正在載入茶葉知識庫..."):
                try:
                    # 使用增強版下載器
                    downloader = EnhancedPDFDownloader()
                    discovered = downloader.discover_pdf_links(WEB_SOURCES)
                    
                    if discovered:
                        downloaded_files = downloader.download_from_discovered_links()
                    
                    all_pdfs = downloader.get_existing_pdfs()
                    
                    if all_pdfs:
                        # 初始化系統
                        if ENABLE_GRAPH_RAG:
                            demo_system = GraphRAGSystem()
                        else:
                            demo_system = EnhancedRAGSystem()
                        
                        documents = demo_system.load_pdfs(all_pdfs)
                        
                        if documents:
                            index = demo_system.create_index(documents)
                            
                            if index:
                                if ENABLE_GRAPH_RAG:
                                    demo_system.setup_graph_rag_retriever()
                                else:
                                    demo_system.setup_query_engine()
                                
                                st.session_state.demo_system = demo_system
                                st.session_state.demo_ready = True
                                
                                layout.show_success("茶葉演示系統載入成功！")
                                st.rerun()
                    else:
                        layout.show_warning("沒有找到茶葉相關文檔")
                        
                except Exception as e:
                    layout.show_error(f"載入演示資料失敗: {str(e)}")
    
    else:
        # 演示系統已就緒
        col1, col2 = layout.create_columns([2, 1])
        
        with col1:
            st.markdown("### 💬 茶葉問答")
            render_demo_chat()
        
        with col2:
            st.markdown("### 📊 知識庫資訊") 
            render_demo_stats()

def render_demo_chat():
    """渲染演示聊天界面"""
    # 建議問題
    suggested_questions = [
        "台灣有哪些主要的茶樹品種？",
        "製茶的基本流程是什麼？",
        "如何進行茶葉品質評鑑？",
        "茶園管理的重點有哪些？"
    ]
    
    st.markdown("**建議問題：**")
    for i, question in enumerate(suggested_questions):
        if st.button(f"💬 {question}", key=f"demo_q_{i}"):
            handle_demo_query(question)
    
    # 自由輸入
    if user_question := st.text_input("或輸入您的問題："):
        if st.button("🔍 詢問"):
            handle_demo_query(user_question)

def handle_demo_query(question: str):
    """處理演示查詢"""
    if st.session_state.demo_system:
        with st.spinner("正在分析茶葉知識..."):
            try:
                if ENABLE_GRAPH_RAG:
                    response = st.session_state.demo_system.query_with_graph_context(question)
                else:
                    response = st.session_state.demo_system.query_with_context(question)
                
                st.markdown(f"**問題：** {question}")
                st.markdown(f"**回答：** {response}")
                st.markdown("---")
                
            except Exception as e:
                st.error(f"查詢失敗: {str(e)}")

def render_demo_stats():
    """渲染演示統計"""
    if st.session_state.demo_ready and st.session_state.demo_system:
        try:
            if ENABLE_GRAPH_RAG:
                stats = st.session_state.demo_system.get_graph_statistics()
                if "graph_stats" in stats:
                    graph_stats = stats["graph_stats"]
                    st.metric("🕸️ 知識節點", graph_stats.get("nodes_count", 0))
                    st.metric("🔗 知識關係", graph_stats.get("edges_count", 0))
                    st.metric("📊 知識社群", graph_stats.get("communities_count", 0))
            else:
                stats = st.session_state.demo_system.get_document_statistics()
                st.metric("📄 文檔數量", stats.get("total_documents", 0))
                st.metric("📖 總頁數", stats.get("total_pages", 0))
                
        except Exception as e:
            st.warning(f"無法獲取統計資訊: {str(e)}")

def render_graph_page(layout: MainLayout):
    """渲染知識圖譜頁面"""
    st.markdown("## 📊 知識圖譜可視化")
    
    if not st.session_state.get('system_ready', False):
        st.info("請先在「我的知識庫」中上傳文檔並建立知識圖譜。")
        return
    
    if not ENABLE_GRAPH_RAG:
        st.warning("需要啟用 Graph RAG 功能才能查看知識圖譜。")
        return
    
    # 圖譜可視化
    try:
        if 'rag_system' in st.session_state:
            with st.spinner("正在生成知識圖譜可視化..."):
                graph_html = st.session_state.rag_system.visualize_knowledge_graph()
                
                if graph_html:
                    # 顯示圖譜
                    with open(graph_html, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    st.components.v1.html(html_content, height=650)
                    
                    # 圖譜統計
                    col1, col2 = layout.create_columns([1, 1])
                    
                    with col1:
                        st.markdown("### 📈 圖譜統計")
                        stats = st.session_state.rag_system.get_graph_statistics()
                        if "graph_stats" in stats:
                            graph_stats = stats["graph_stats"]
                            
                            st.metric("節點總數", graph_stats.get("nodes_count", 0))
                            st.metric("關係總數", graph_stats.get("edges_count", 0))
                            st.metric("知識社群", graph_stats.get("communities_count", 0))
                            st.metric("平均連接度", f"{graph_stats.get('average_degree', 0):.2f}")
                    
                    with col2:
                        st.markdown("### 🔍 實體探索")
                        entity_name = st.text_input("輸入實體名稱：")
                        
                        if entity_name:
                            related = st.session_state.rag_system.get_related_entities(entity_name)
                            
                            if related:
                                for rel in related:
                                    st.write(f"**{rel['entity']}** - {rel['relationship']} ({rel['type']})")
                            else:
                                st.info("沒有找到相關實體")
                else:
                    st.error("無法生成知識圖譜可視化")
                    
    except Exception as e:
        st.error(f"圖譜可視化失敗: {str(e)}")

def render_settings_page(layout: MainLayout):
    """渲染設定頁面"""
    st.markdown("## ⚙️ 系統設定")
    
    # API 設定區域
    with st.expander("🔐 API 設定", expanded=True):
        st.markdown("### Groq API")
        groq_status = "✅ 已設定" if GROQ_API_KEY else "❌ 未設定"
        st.write(f"狀態: {groq_status}")
        
        st.markdown("### Gemini API")
        gemini_status = "✅ 已設定" if GEMINI_API_KEY else "❌ 未設定"
        st.write(f"狀態: {gemini_status}")
        
        if not GROQ_API_KEY:
            st.warning("請在 .env 檔案中設定 GROQ_API_KEY")
            
        if not GEMINI_API_KEY:
            st.info("可選：在 .env 檔案中設定 GEMINI_API_KEY 以啟用 OCR 功能")
    
    # 系統設定
    with st.expander("🔧 系統設定", expanded=True):
        st.markdown("### RAG 模式")
        current_mode = "Graph RAG" if ENABLE_GRAPH_RAG else "Traditional RAG"
        st.info(f"當前模式: {current_mode}")
        
        if ENABLE_GRAPH_RAG:
            st.success("✅ Graph RAG 已啟用 - 支援知識圖譜建構與推理")
        else:
            st.info("ℹ️ Traditional RAG 模式 - 基於向量相似度檢索")
    
    # 資料管理
    with st.expander("📁 資料管理", expanded=False):
        st.markdown("### 清理資料")
        
        col1, col2 = layout.create_columns([1, 1])
        
        with col1:
            if st.button("🗑️ 清除知識庫", type="secondary"):
                if st.button("確認清除知識庫", type="secondary", key="confirm_clear_kb"):
                    # 實作清除邏輯
                    layout.show_success("知識庫已清除")
        
        with col2:
            if st.button("🔄 重建索引", type="secondary"):
                # 實作重建邏輯
                layout.show_info("正在重建索引...")

def main():
    """主函數"""
    # 初始化組件
    layout = init_layout()
    upload_zone = init_upload_zone()  
    chat_interface = init_chat_interface()
    
    # 載入樣式
    layout.load_custom_css()
    
    # 渲染標題
    layout.render_header()
    
    # 檢查系統狀態
    check_system_status()
    
    # 渲染導航並獲取選擇的頁面
    selected_page = layout.render_navigation()
    
    # 根據選擇的頁面渲染內容
    if selected_page == "🏠 首頁":
        render_home_page(layout)
        
    elif selected_page == "📚 我的知識庫":
        render_knowledge_base_page(layout, upload_zone, chat_interface)
        
    elif selected_page == "🍵 演示模式":
        render_demo_page(layout)
        
    elif selected_page == "📊 知識圖譜":
        render_graph_page(layout)
        
    elif selected_page == "⚙️ 設定":
        render_settings_page(layout)
    
    # 渲染側邊欄資訊
    layout.render_sidebar_info()

if __name__ == "__main__":
    main()
