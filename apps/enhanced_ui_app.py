import streamlit as st
import os
from datetime import datetime
from enhanced_pdf_downloader import EnhancedPDFDownloader
from enhanced_rag_system import EnhancedRAGSystem
from config import PAGE_TITLE, PAGE_ICON, GROQ_API_KEY, WEB_SOURCES, GEMINI_API_KEY

# 導入新的 UI 組件
from components.user_experience import UserExperience
from components.onboarding.welcome_flow import WelcomeFlow
from components.upload.drag_drop_zone import DragDropZone
from components.chat.chat_interface import ChatInterface

# 頁面配置
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 UX 組件
@st.cache_resource
def init_ux_components():
    """初始化 UX 組件（緩存以提高性能）"""
    return {
        'user_experience': UserExperience(),
        'welcome_flow': WelcomeFlow(),
        'drag_drop_zone': DragDropZone(),
        'chat_interface': ChatInterface()
    }

# 全域樣式
def load_global_styles():
    """載入全域 CSS 樣式"""
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .custom-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """渲染頁面標題"""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
        <h1 style="
            font-size: 2.5rem; 
            font-weight: 700; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        ">
            🤖 智能文檔問答助理
        </h1>
        <p style="
            font-size: 1.2rem; 
            color: #6b7280; 
            margin: 0;
        ">
            多模態 RAG 問答系統 • 支援文檔、圖片 OCR 與對話記憶
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_mode_selector(ux: UserExperience) -> str:
    """渲染模式選擇器"""
    current_mode = ux.get_preferred_mode()
    
    st.markdown("### 🎯 選擇使用模式")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            "📚 我的知識庫", 
            key="personal_mode",
            use_container_width=True,
            type="primary" if current_mode == "personal" else "secondary"
        ):
            ux.set_preferred_mode("personal")
            st.rerun()
    
    with col2:
        if st.button(
            "🍵 茶葉演示", 
            key="demo_mode",
            use_container_width=True,
            type="primary" if current_mode == "demo" else "secondary"
        ):
            ux.set_preferred_mode("demo")
            st.rerun()
    
    return current_mode

def render_personal_mode(components: dict, ux: UserExperience):
    """渲染個人模式"""
    drag_drop_zone = components['drag_drop_zone']
    chat_interface = components['chat_interface']
    
    # 初始化 RAG 系統
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    
    # 檢查是否有已上傳的檔案或現有索引
    has_files = False
    if GROQ_API_KEY and not st.session_state.system_ready:
        try:
            # 延遲初始化 RAG 系統，避免在頁面載入時就初始化模型
            from config import INDEX_DIR
            import os
            if os.path.exists(INDEX_DIR) and os.listdir(INDEX_DIR):
                has_files = True
        except Exception as e:
            st.warning(f"檢查索引時發生錯誤: {str(e)}")
    
    if not has_files and not st.session_state.system_ready:
        # 空狀態 - 顯示大型上傳區域
        st.markdown("## 📤 建立您的專屬知識庫")
        
        # 快速開始指南
        drag_drop_zone.render_quick_start_guide()
        
        # 大型上傳區域
        uploaded_files = drag_drop_zone.render_empty_state()
        
        # 上傳提示
        drag_drop_zone.render_upload_tips()
        
        # 處理上傳的檔案
        if uploaded_files:
            st.markdown("---")
            
            # 顯示上傳進度
            progress_data = drag_drop_zone.render_upload_progress(uploaded_files)
            
            # 處理檔案按鈕
            if st.button("🚀 開始處理檔案", type="primary", use_container_width=True):
                if not st.session_state.rag_system:
                    st.session_state.rag_system = EnhancedRAGSystem()
                
                with st.spinner("正在處理您的檔案..."):
                    # 確保模型已初始化
                    st.session_state.rag_system._ensure_models_initialized()
                    
                    # 處理上傳的檔案
                    docs = st.session_state.rag_system.process_uploaded_files(uploaded_files)
                    
                    if docs:
                        # 建立索引
                        index = st.session_state.rag_system.create_index(docs)
                        
                        if index:
                            st.session_state.rag_system.setup_query_engine()
                            st.session_state.system_ready = True
                            
                            # 記錄上傳歷史
                            for file in uploaded_files:
                                file_type = "image" if drag_drop_zone._get_file_type(file.name) == "image" else "document"
                                ux.add_upload_record(file.name, file_type, file.size)
                            
                            st.balloons()
                            st.success(f"🎉 成功處理 {len(docs)} 個檔案！現在可以開始問答了。")
                            st.rerun()
                        else:
                            st.error("索引建立失敗，請重試。")
                    else:
                        st.error("檔案處理失敗，請檢查檔案格式。")
    
    else:
        # 有檔案狀態 - 顯示問答界面
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("## 💬 智能問答")
            
            # 聊天界面
            user_question = chat_interface.render_chat_container()
            
            # 處理用戶問題
            if user_question and st.session_state.rag_system:
                def handle_query(question):
                    """處理用戶查詢（同步）"""
                    if 'rag_system' not in st.session_state or not st.session_state.rag_system:
                        st.error("請先初始化 RAG 系統")
                        return

                    system = st.session_state.rag_system

                    with st.spinner("🔍 正在查詢..."):
                        try:
                            print(f"🔍 UI層開始查詢: {question}")
                            print(f"🔧 使用系統類型: {type(system)}")

                            # 同步呼叫查詢介面（優先使用帶記憶的查詢）
                            if hasattr(system, 'query_with_context'):
                                response = system.query_with_context(question)
                            else:
                                response = system.query(question)

                            print(f"✅ UI層查詢完成，響應長度: {len(str(response)) if response else 0}")

                            if response:
                                # 顯示回答
                                with st.chat_message("assistant"):
                                    st.write(response)

                                    # 顯示參考來源
                                    st.expander("📚 參考來源").write("• 向量索引\n• 用戶文檔")
                            else:
                                st.warning("未找到相關資訊")

                        except Exception as e:
                            error_msg = str(e)
                            error_type = type(e).__name__

                            print(f"❌ UI層捕獲錯誤:")
                            print(f"   錯誤類型: {error_type}")
                            print(f"   錯誤消息: {error_msg}")

                            # 特別檢查 ObjectApiResponse 錯誤
                            if "ObjectApiResponse" in error_msg or "await" in error_msg:
                                print("🚨 UI層檢測到ObjectApiResponse錯誤！")
                                print(f"   系統類型: {type(system)}")
                                if hasattr(system, 'elasticsearch_client'):
                                    print(f"   ES客戶端類型: {type(system.elasticsearch_client)}")

                            import traceback
                            print(f"🔍 UI層完整錯誤堆疊:")
                            print(traceback.format_exc())

                            st.error(f"查詢時發生錯誤: {error_msg}")
                            st.write("抱歉，處理您的問題時發生錯誤。")
                            st.write(traceback.format_exc())

                # 直接呼叫同步查詢處理
                handle_query(user_question)
                
                # 處理用戶問題
                chat_interface.add_message("assistant", "處理完成")
                
                st.rerun()
        
        with col2:
            st.markdown("## 📊 知識庫狀態")
            
            # 檔案統計
            if st.session_state.rag_system:
                stats = st.session_state.rag_system.get_document_statistics()
                
                # 統計卡片
                st.metric("📄 文檔數量", stats.get("total_documents", 0))
                st.metric("🧩 文本塊數", stats.get("total_nodes", 0))
                
                # 使用統計
                usage_stats = ux.get_usage_stats()
                st.metric("📤 總上傳次數", usage_stats["total_uploads"])
                
                # 聊天統計
                chat_stats = chat_interface.get_chat_stats()
                st.metric("💬 對話次數", chat_stats["total_messages"])
            
            # 操作按鈕
            st.markdown("---")
            
            if st.button("📤 上傳更多檔案", use_container_width=True):
                st.session_state.show_upload = True
                st.rerun()
            
            if st.button("🗑️ 清空聊天", use_container_width=True):
                chat_interface.clear_chat()
                st.rerun()
            
            if st.button("📋 匯出對話", use_container_width=True):
                export_text = chat_interface.export_chat()
                st.download_button(
                    "下載對話記錄",
                    export_text,
                    file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

def render_demo_mode():
    """渲染演示模式（原有的茶葉系統）"""
    st.markdown("## 🍵 茶葉知識演示")
    
    # 初始化 RAG 系統
    if 'demo_rag_system' not in st.session_state:
        st.session_state.demo_rag_system = None
    if 'demo_system_ready' not in st.session_state:
        st.session_state.demo_system_ready = False
    
    # 系統初始化按鈕
    if not st.session_state.demo_system_ready:
        if st.button("🚀 載入茶葉演示資料", type="primary", use_container_width=True):
            with st.spinner("正在載入茶葉知識庫..."):
                # 使用增強版下載器自動發現並下載PDF檔案
                downloader = EnhancedPDFDownloader()
                
                # 自動發現PDF連結
                discovered = downloader.discover_pdf_links(WEB_SOURCES)
                
                # 下載發現的PDF檔案
                if discovered:
                    downloaded_files = downloader.download_from_discovered_links()
                
                # 取得所有PDF檔案
                all_pdfs = downloader.get_existing_pdfs()
                
                if all_pdfs:
                    # 初始化RAG系統
                    rag_system = EnhancedRAGSystem()
                    
                    # 載入PDF檔案
                    documents = rag_system.load_pdfs(all_pdfs)
                    
                    if documents:
                        # 建立索引
                        index = rag_system.create_index(documents)
                        
                        if index:
                            # 設定查詢引擎
                            rag_system.setup_query_engine()
                            
                            # 儲存到session state
                            st.session_state.demo_rag_system = rag_system
                            st.session_state.demo_system_ready = True
                            
                            st.success("✅ 茶葉演示系統初始化完成！")
                            st.balloons()
                            st.rerun()
    
    else:
        # 演示系統已就緒
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 知識庫摘要
            if st.session_state.demo_rag_system:
                summary = st.session_state.demo_rag_system.get_knowledge_base_summary()
                
                if summary:
                    st.markdown("### 📚 茶葉知識庫摘要")
                    
                    # 統計資訊
                    stats = summary.get("statistics", {})
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("📄 文件數量", stats.get("total_documents", 0))
                    with col_b:
                        st.metric("📖 總頁數", stats.get("total_pages", 0))
                    with col_c:
                        st.metric("🧩 文本塊數", stats.get("total_nodes", 0))
                    
                    # 建議問題
                    suggested_questions = summary.get("suggested_questions", [])
                    if suggested_questions:
                        st.markdown("### 💡 建議問題")
                        
                        for i, question in enumerate(suggested_questions[:4]):
                            if st.button(f"💬 {question}", key=f"demo_suggestion_{i}"):
                                # 執行查詢
                                response = st.session_state.demo_rag_system.query_with_context(question)
                                st.markdown(f"**問題：** {question}")
                                st.markdown(f"**回答：** {response}")
                                st.markdown("---")
        
        with col2:
            st.markdown("### 🎯 演示功能")
            
            # 問答輸入
            demo_question = st.text_input("輸入茶葉相關問題：", key="demo_question")
            
            if st.button("🔍 詢問", key="demo_ask"):
                if demo_question and st.session_state.demo_rag_system:
                    with st.spinner("正在思考..."):
                        response = st.session_state.demo_rag_system.query_with_context(demo_question)
                    
                    st.markdown("**回答：**")
                    st.markdown(response)

def main():
    """主函數"""
    # 載入全域樣式
    load_global_styles()
    
    # 初始化組件
    components = init_ux_components()
    ux = components['user_experience']
    welcome_flow = components['welcome_flow']
    
    # 渲染標題
    render_header()
    
    # 檢查是否需要顯示歡迎引導
    if welcome_flow.should_show_onboarding(
        ux.is_first_visit(),
        ux.is_onboarding_completed()
    ):
        # 自動開始引導
        if not st.session_state.get('show_onboarding', False):
            welcome_flow.start_onboarding()
    
    # 顯示歡迎引導
    onboarding_result = welcome_flow.render_welcome_modal()
    
    if onboarding_result == "completed":
        ux.complete_onboarding()
        ux.mark_visited()
        st.rerun()
    elif onboarding_result == "showing":
        return  # 正在顯示引導，不渲染其他內容
    
    # 標記已訪問
    if ux.is_first_visit():
        ux.mark_visited()
    
    # 模式選擇
    current_mode = render_mode_selector(ux)
    
    # 根據模式渲染不同內容
    if current_mode == "personal":
        render_personal_mode(components, ux)
    else:
        render_demo_mode()
    
    # 側邊欄
    with st.sidebar:
        st.markdown("## ⚙️ 設定")
        
        # API 狀態
        if GROQ_API_KEY:
            st.success("✅ Groq API 已設定")
        else:
            st.error("❌ 請設定 GROQ_API_KEY")
        
        if GEMINI_API_KEY:
            st.success("✅ Gemini API 已設定")
        else:
            st.warning("⚠️ Gemini API 未設定（OCR功能不可用）")
        
        st.markdown("---")
        
        # 用戶偏好設定
        st.markdown("### 🎨 個人偏好")
        
        preferences = ux.get_chat_preferences()
        
        # 主題選擇
        theme = st.selectbox(
            "主題",
            ["light", "dark"],
            index=0 if preferences.get("theme", "light") == "light" else 1,
            key="theme_selector"
        )
        
        # 語言選擇
        language = st.selectbox(
            "語言",
            ["zh-TW", "zh-CN", "en"],
            index=0,
            key="language_selector"
        )
        
        # 功能開關
        show_sources = st.checkbox("顯示來源引用", value=preferences.get("show_sources", True))
        enable_memory = st.checkbox("啟用對話記憶", value=preferences.get("enable_memory", True))
        
        # 更新偏好
        if st.button("💾 儲存設定"):
            ux.update_chat_preferences({
                "theme": theme,
                "language": language,
                "show_sources": show_sources,
                "enable_memory": enable_memory
            })
            st.success("設定已儲存！")
        
        st.markdown("---")
        
        # 使用統計
        st.markdown("### 📊 使用統計")
        usage_stats = ux.get_usage_stats()
        
        st.write(f"📤 總上傳: {usage_stats['total_uploads']} 次")
        st.write(f"💾 總大小: {usage_stats['total_size'] / (1024*1024):.1f} MB")
        
        # 重置按鈕
        if st.button("🔄 重置所有資料", type="secondary"):
            if st.button("確認重置", type="secondary"):
                ux.reset_user_data()
                st.success("資料已重置")
                st.rerun()

if __name__ == "__main__":
    main()
