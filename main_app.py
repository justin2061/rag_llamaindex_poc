import streamlit as st
import os
import inspect
from datetime import datetime

# 導入新的架構組件
from components.layout.main_layout import MainLayout
from components.knowledge_base.upload_zone import UploadZone
from components.chat.chat_interface import ChatInterface

# 導入系統核心
from utils import get_rag_system  # 使用工廠函式
from enhanced_pdf_downloader import EnhancedPDFDownloader

# 導入配置
from config import (
    GROQ_API_KEY, GEMINI_API_KEY, WEB_SOURCES, 
    ENABLE_GRAPH_RAG,
    PAGE_TITLE, PAGE_ICON, APP_MODE
)

# 避免重複設置頁面配置
if not hasattr(st.session_state, 'page_configured'):
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
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
    if 'rag_system' not in st.session_state or st.session_state.rag_system is None:
        # 使用工廠函式來獲取 RAG 系統實例
        st.session_state.rag_system = get_rag_system()
        st.session_state.system_ready = False

def check_system_status():
    """檢查系統狀態"""
    if 'system_status_checked' not in st.session_state:
        st.session_state.system_status_checked = True
        
        # 檢查是否有現有索引
        from config import INDEX_DIR, RAG_SYSTEM_TYPE
        # 根據不同的RAG系統檢查不同的持久化路徑
        if RAG_SYSTEM_TYPE == 'enhanced':
             persist_dir = INDEX_DIR
        elif RAG_SYSTEM_TYPE == 'graph':
             persist_dir = os.path.join("data", "graph_storage") # 假設圖存儲路徑
        else:
             persist_dir = INDEX_DIR # 預設

        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            st.session_state.has_existing_index = True
        else:
            st.session_state.has_existing_index = False
            
        # 檢查用戶上傳的檔案
        upload_zone = init_upload_zone()
        upload_stats = upload_zone.get_upload_stats()
        st.session_state.has_user_files = upload_stats['total_files'] > 0

def render_full_ui():
    """渲染完整的UI介面"""
    layout = init_layout()
    upload_zone = init_upload_zone()  
    chat_interface = init_chat_interface()
    
    layout.load_custom_css()
    layout.render_header()
    check_system_status()
    
    selected_page = layout.render_navigation()
    
    page_renderers = {
        "🏠 首頁": render_home_page,
        "📚 我的知識庫": lambda: render_knowledge_base_page(layout, upload_zone, chat_interface),
        "🍵 演示模式": render_demo_page,
        "📊 知識圖譜": render_graph_page,
        "⚙️ 設定": render_settings_page,
    }
    
    # 根據選擇的頁面渲染內容
    renderer = page_renderers.get(selected_page)
    if renderer:
        sig = inspect.signature(renderer)
        if 'layout' in sig.parameters:
            renderer(layout)
        else:
            renderer()

    layout.render_sidebar_info()

def render_home_page(layout: MainLayout):
    """渲染首頁"""
    st.markdown("""
    <div class="custom-card">
        <h2>🏠 歡迎使用智能文檔問答助理</h2>
        <p>這是一個基於 Graph RAG 技術的先進問答系統，能夠理解文檔間的複雜關係並提供精確的答案。</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem;">
            <div style="padding: 1.5rem; background-color: #f0f2f6; border-radius: 0.5rem; border: 1px solid #e0e0e0;">
                <h3>🕸️ Graph RAG 技術</h3>
                <p>自動建構知識圖譜，發現實體間的深層關係���提供更精確的答案。</p>
            </div>
            
            <div style="padding: 1.5rem; background-color: #f0f2f6; border-radius: 0.5rem; border: 1px solid #e0e0e0;">
                <h3>📄 多格式支援</h3>
                <p>支援 PDF、Word、文字檔、Markdown 以及圖片 OCR，一站式處理各種文檔。</p>
            </div>
            
            <div style="padding: 1.5rem; background-color: #f0f2f6; border-radius: 0.5rem; border: 1px solid #e0e0e0;">
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
                        docs = st.session_state.rag_system.process_uploaded_files(uploaded_files)
                        
                        if docs:
                            # 建立索引（Graph RAG 或傳統 RAG）
                            index = st.session_state.rag_system.create_index(docs)
                            
                            if index:
                                # 根據實際系統類型設置查詢引擎
                                if hasattr(st.session_state.rag_system, 'setup_graph_rag_retriever'):
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
    # 使用 ChatInterface 的內建渲染方法
    user_input = chat_interface.render_chat_container()
    
    # 處理用戶輸入
    if user_input:
        # 添加用戶訊息
        chat_interface.add_message("user", user_input)
        
        # 設定思考狀態
        chat_interface.set_thinking(True)
        
        # 生成助手回應
        try:
            # 根據實際系統類型選擇查詢方法
            system_type = st.session_state.get('rag_system_type', 'Unknown')
            
            if system_type == "Graph RAG":
                response = st.session_state.rag_system.query_with_graph_context(user_input)
                sources = ["知識圖譜", "用戶文檔"]
            else: # Enhanced and Elasticsearch
                response = st.session_state.rag_system.query_with_context(user_input)
                sources = ["向量索引", "用戶文檔"]
            
            # 添加助手訊息
            chat_interface.add_message("assistant", response, sources)
            
        except Exception as e:
            error_msg = f"處理問題時發生錯誤: {str(e)}"
            chat_interface.add_message("assistant", error_msg)
        
        finally:
            # 取消思考狀態
            chat_interface.set_thinking(False)
            st.rerun()

def render_system_statistics():
    """渲染系統統計資訊"""
    if 'rag_system' in st.session_state and st.session_state.system_ready:
        try:
            # 檢查實際使用的系統類型
            system_type = st.session_state.get('rag_system_type', 'Unknown')
            
            if system_type == "Graph RAG":
                stats = st.session_state.rag_system.get_graph_statistics()
                if "graph_stats" in stats:
                    graph_stats = stats["graph_stats"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🕸️ 節點數", graph_stats.get("nodes_count", 0))
                        st.metric("📊 社群數", graph_stats.get("communities_count", 0))
                    with col2:
                        st.metric("🔗 關係數", graph_stats.get("edges_count", 0))
                        st.metric("📈 圖密度", f"{graph_stats.get('density', 0):.3f}")
                        
            elif system_type == "Elasticsearch RAG":
                stats = st.session_state.rag_system.get_elasticsearch_statistics()
                es_stats = stats.get("elasticsearch_stats", {})
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 文檔數", es_stats.get("total_documents", 0))
                with col2:
                    st.metric("💾 索引大小", f"{es_stats.get('index_size_bytes', 0) / 1024**2:.2f} MB")
                        
            else: # Enhanced RAG
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
    st.info("這是一個預建的茶葉知識庫演示，展示系統在專業領域的應用效果。")
    
    if 'demo_system' not in st.session_state:
        st.session_state.demo_system = None
        st.session_state.demo_ready = False
    
    if not st.session_state.demo_ready:
        if st.button("🚀 載入茶葉演示資料", type="primary"):
            with st.spinner("正在載入茶葉知識庫..."):
                try:
                    downloader = EnhancedPDFDownloader()
                    downloader.discover_pdf_links(WEB_SOURCES)
                    downloader.download_from_discovered_links()
                    all_pdfs = downloader.get_existing_pdfs()
                    
                    if all_pdfs:
                        # 演示模式固定使用 EnhancedRAGSystem
                        from enhanced_rag_system import EnhancedRAGSystem
                        demo_system = EnhancedRAGSystem()
                        documents = demo_system.load_pdfs(all_pdfs)
                        
                        if documents:
                            index = demo_system.create_index(documents)
                            if index:
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
        col1, col2 = layout.create_columns([2, 1])
        with col1:
            st.markdown("### 💬 茶葉問答")
            render_demo_chat()
        with col2:
            st.markdown("### 📊 知識庫資訊") 
            render_demo_stats()

def render_demo_chat():
    """渲染演示聊天界面"""
    suggested_questions = [
        "台灣有哪些主要的茶樹品種？", "製茶的基本流程是什麼？",
        "如何進行茶葉品質評鑑？", "茶園管理的重點有哪些？"
    ]
    
    st.markdown("**建議問題：**")
    for i, question in enumerate(suggested_questions):
        if st.button(f"💬 {question}", key=f"demo_q_{i}"):
            handle_demo_query(question)
    
    if user_question := st.text_input("或輸入您的問題："):
        if st.button("🔍 詢問"):
            handle_demo_query(user_question)

def handle_demo_query(question: str):
    """處理演示查詢"""
    if st.session_state.demo_system:
        with st.spinner("正在分析茶葉知識..."):
            try:
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
            if hasattr(st.session_state.demo_system, 'get_document_statistics'):
                stats = st.session_state.demo_system.get_document_statistics()
                st.metric("📄 文檔數量", stats.get("total_documents", 0))
                st.metric("📖 總頁數", stats.get("total_pages", 0))
            else:
                st.info("統計資訊不可用")
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
    
    try:
        if 'rag_system' in st.session_state:
            with st.spinner("正在生成知識圖譜可視化..."):
                graph_html = st.session_state.rag_system.visualize_knowledge_graph()
                if graph_html:
                    with open(graph_html, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=650)
                    
                    col1, col2 = layout.create_columns([1, 1])
                    with col1:
                        st.markdown("### 📈 圖譜統計")
                        stats = st.session_state.rag_system.get_graph_statistics()["graph_stats"]
                        st.metric("節點總數", stats.get("nodes_count", 0))
                        st.metric("關係總數", stats.get("edges_count", 0))
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
    """渲染設���頁面"""
    st.markdown("## ⚙️ 系統設定")
    
    with st.expander("🔐 API 設定", expanded=True):
        st.markdown("### Groq API")
        st.write(f"狀態: {'✅ 已設定' if GROQ_API_KEY else '❌ 未設定'}")
        st.markdown("### Gemini API")
        st.write(f"狀態: {'✅ 已設定' if GEMINI_API_KEY else '❌ 未設定'}")
        if not GROQ_API_KEY: st.warning("請在 .env 檔案中設定 GROQ_API_KEY")
        if not GEMINI_API_KEY: st.info("可選：設定 GEMINI_API_KEY 以啟用 OCR 功能")
    
    with st.expander("🔧 系統設定", expanded=True):
        st.markdown("### RAG 模式")
        st.info(f"當前模式: {st.session_state.get('rag_system_type', '未初始化')}")
    
    with st.expander("📁 資料管理", expanded=False):
        st.markdown("### 清理資料")
        if st.button("🗑️ 清除知識庫", type="secondary"):
            # 實作清除邏輯
            layout.show_success("知識庫已清除")

def render_quick_start_ui():
    """渲染快速啟動的簡化版UI"""
    st.title("🤖 智能問答助理 (快速模式)")
    
    if 'rag_system' not in st.session_state or st.session_state.rag_system is None:
        st.warning("正在初始化系統...")
        init_rag_system()

    rag_system = st.session_state.rag_system
    
    # 自動載入現有索引
    if not st.session_state.get('system_ready', False):
        with st.spinner("正在載入現有索引..."):
            if rag_system.load_existing_index():
                st.session_state.system_ready = True
                st.success("✅ 系統已就緒，可以開始提問。")
            else:
                st.error("❌ 未找到現有索引。請使用完整模式上傳文件以建立索引。")
                return

    if st.session_state.get('system_ready', False):
        question = st.text_input("請輸入您的問題：", placeholder="例如：台灣茶的特色是什麼？")
        
        if st.button("🔍 詢問", type="primary"):
            if question:
                with st.spinner("正在思考..."):
                    response = rag_system.query(question)
                    st.markdown(response)
            else:
                st.warning("請輸入問題。")

def main():
    """主函數：根據APP_MODE選擇渲染哪個UI"""
    init_rag_system() # 確保系統總是被初始化

    if APP_MODE == "full":
        render_full_ui()
    else: # quick or ultra_fast
        render_quick_start_ui()

if __name__ == "__main__":
    main()