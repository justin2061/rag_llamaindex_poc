import streamlit as st
import os
from datetime import datetime
from enhanced_pdf_downloader import EnhancedPDFDownloader
from enhanced_rag_system import EnhancedRAGSystem
from config import PAGE_TITLE, PAGE_ICON, GROQ_API_KEY, WEB_SOURCES, GEMINI_API_KEY

# 頁面配置
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 更新系統名稱和描述
SYSTEM_TITLE = "🤖 智能文檔問答助理"
SYSTEM_SUBTITLE = "多模態RAG問答系統 | 支援文檔、圖片OCR與對話記憶"

# 標題
st.title(SYSTEM_TITLE)
st.markdown(f"*{SYSTEM_SUBTITLE}*")
st.markdown("---")

# 初始化session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'system_ready' not in st.session_state:
    st.session_state.system_ready = False

# 設定當前時間到session state
st.session_state.current_time = datetime.now().isoformat()

# 自動載入現有索引（如果存在）
if not st.session_state.system_ready and GROQ_API_KEY:
    if os.path.exists(os.path.join("data", "index")) and os.listdir(os.path.join("data", "index")):
        with st.spinner("正在載入現有索引..."):
            try:
                rag_system = EnhancedRAGSystem()
                if rag_system.load_existing_index():
                    st.session_state.rag_system = rag_system
                    st.session_state.system_ready = True
                    st.success("🚀 系統已自動載入現有索引，可以直接開始查詢！")
            except Exception as e:
                st.warning(f"自動載入索引時發生錯誤: {str(e)}")

# 側邊欄
with st.sidebar:
    st.header("🔧 系統設定")
    
    # API Key檢查
    if GROQ_API_KEY:
        st.success("✅ Groq API Key 已設定")
    else:
        st.error("❌ 請設定 GROQ_API_KEY 環境變數")
        st.info("請在 .env 檔案中設定您的 Groq API Key")
    
    st.markdown("---")
    
    # 系統初始化按鈕
    init_button_text = "🔄 重建索引" if st.session_state.system_ready else "🚀 初始化系統"
    if st.button(init_button_text, type="primary"):
        if GROQ_API_KEY:
            with st.spinner("正在初始化系統..."):
                # 使用增強版下載器自動發現並下載PDF檔案
                downloader = EnhancedPDFDownloader()
                
                # 步驟1: 自動發現PDF連結
                st.info("🔍 步驟1: 自動發現PDF連結...")
                discovered = downloader.discover_pdf_links(WEB_SOURCES)
                
                # 步驟2: 下載發現的PDF檔案
                if discovered:
                    st.info("📥 步驟2: 下載發現的PDF檔案...")
                    downloaded_files = downloader.download_from_discovered_links()
                else:
                    st.warning("未發現新的PDF連結，將使用現有檔案")
                
                # 取得所有PDF檔案
                all_pdfs = downloader.get_existing_pdfs()
                
                if all_pdfs:
                    # 步驟3: 初始化RAG系統
                    st.info("🔧 步驟3: 初始化RAG系統...")
                    rag_system = EnhancedRAGSystem()
                    
                    # 步驟4: 載入PDF檔案
                    st.info("📖 步驟4: 載入PDF檔案...")
                    documents = rag_system.load_pdfs(all_pdfs)
                    
                    if documents:
                        # 步驟5: 建立索引
                        st.info("🔍 步驟5: 建立向量索引...")
                        index = rag_system.create_index(documents)
                        
                        if index:
                            # 步驟6: 設定查詢引擎
                            st.info("⚙️ 步驟6: 設定查詢引擎...")
                            rag_system.setup_query_engine()
                            
                            # 儲存到session state
                            st.session_state.rag_system = rag_system
                            st.session_state.system_ready = True
                            
                            st.success("✅ 系統初始化完成！可以開始使用問答功能")
                            st.info(f"📚 已載入 {len(all_pdfs)} 個PDF檔案")
                        else:
                            st.error("❌ 建立索引失敗")
                    else:
                        st.error("❌ 載入文件失敗")
                else:
                    st.error("❌ 找不到PDF檔案，請檢查網路連線或PDF來源")
        else:
            st.error("請先設定 Groq API Key")
    
    # 檔案上傳區塊
    st.markdown("---")
    st.header("📤 檔案上傳")
    
    if st.session_state.system_ready and st.session_state.rag_system:
        # 檔案上傳界面
        tab1, tab2 = st.tabs(["📄 文檔", "🖼️ 圖片"])
        
        with tab1:
            doc_files = st.file_uploader(
                "上傳文檔檔案",
                type=['pdf', 'txt', 'docx', 'md'],
                accept_multiple_files=True,
                key="doc_uploader",
                help="支援 PDF、TXT、DOCX、MD 格式"
            )
            
            if doc_files:
                if st.button("📝 處理文檔", key="process_docs"):
                    with st.spinner("正在處理文檔..."):
                        docs = st.session_state.rag_system.process_uploaded_files(doc_files)
                        if docs:
                            # 重建索引
                            if st.session_state.rag_system.rebuild_index_with_user_files():
                                st.success(f"✅ 成功處理 {len(docs)} 個文檔!")
                                st.rerun()
                            else:
                                st.error("重建索引失敗")
        
        with tab2:
            # 檢查OCR是否可用
            if st.session_state.rag_system.ocr_processor.is_available():
                image_files = st.file_uploader(
                    "上傳圖片檔案",
                    type=['png', 'jpg', 'jpeg', 'webp', 'bmp'],
                    accept_multiple_files=True,
                    key="image_uploader",
                    help="支援 PNG、JPG、JPEG、WEBP、BMP 格式，將使用 Google Gemini 進行OCR"
                )
                
                if image_files:
                    if st.button("🔍 OCR處理", key="process_images"):
                        with st.spinner("正在進行OCR處理..."):
                            docs = st.session_state.rag_system.process_uploaded_files(image_files)
                            if docs:
                                # 重建索引
                                if st.session_state.rag_system.rebuild_index_with_user_files():
                                    st.success(f"✅ 成功OCR處理 {len(docs)} 張圖片!")
                                    st.rerun()
                                else:
                                    st.error("重建索引失敗")
            else:
                st.warning("⚠️ OCR功能不可用")
                st.write("請檢查 GEMINI_API_KEY 是否已正確設定")
        
        # 已上傳檔案管理
        if hasattr(st.session_state.rag_system, 'file_manager'):
            file_stats = st.session_state.rag_system.file_manager.get_file_stats()
            if file_stats['total_files'] > 0:
                st.write("📁 **已上傳檔案:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 文檔", file_stats['document_count'])
                with col2:
                    st.metric("🖼️ 圖片", file_stats['image_count'])
                
                # 檔案清理按鈕
                if st.button("🗑️ 清除所有上傳檔案", key="clear_files"):
                    # 這裡需要實作清除功能
                    st.warning("檔案清除功能開發中...")
    
    else:
        st.info("請先初始化系統才能上傳檔案")
    
    # 對話記憶控制
    st.markdown("---")
    st.header("🧠 對話記憶")
    
    if st.session_state.system_ready and st.session_state.rag_system:
        # 記憶統計
        memory_stats = st.session_state.rag_system.memory.get_memory_stats()
        
        if memory_stats['enabled']:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("記憶步數", f"{memory_stats['current_count']}/{memory_stats['max_steps']}")
            with col2:
                if st.button("🗑️ 清除記憶"):
                    st.session_state.rag_system.clear_conversation_memory()
                    st.success("記憶已清除")
                    st.rerun()
            
            # 顯示記憶內容
            memory_content = st.session_state.rag_system.get_memory_for_display()
            if memory_content:
                with st.expander("👁️ 查看記憶內容", expanded=False):
                    for mem in memory_content:
                        st.write(f"**Q{mem['id']}:** {mem['question'][:50]}...")
                        st.write(f"**A{mem['id']}:** {mem['answer'][:100]}...")
                        st.write("---")
        else:
            st.info("對話記憶功能未啟用")
    
    # 顯示系統狀態
    st.markdown("---")
    st.header("📊 系統狀態")
    
    if st.session_state.system_ready:
        st.success("🟢 系統已就緒")
        
        # API狀態檢查
        api_status_col1, api_status_col2 = st.columns(2)
        
        with api_status_col1:
            if GROQ_API_KEY:
                st.success("✅ Groq API")
            else:
                st.error("❌ Groq API")
        
        with api_status_col2:
            if GEMINI_API_KEY:
                st.success("✅ Gemini API")
            else:
                st.warning("⚠️ Gemini API")
        
        # 顯示載入的文件
        if st.session_state.rag_system:
            sources = st.session_state.rag_system.get_source_info()
            if sources:
                st.write("📚 **已載入的文件:**")
                for source in sources[:5]:  # 只顯示前5個
                    st.write(f"• {source}")
                if len(sources) > 5:
                    st.write(f"... 還有 {len(sources) - 5} 個檔案")
    else:
        st.warning("🟡 系統尚未初始化")
    
    st.markdown("---")
    st.write("📖 **使用說明:**")
    st.write("1. 🔄 **自動載入**：如有現有索引，系統會自動載入")
    st.write("2. 🆕 **首次使用**：點擊「初始化系統」建立知識庫")
    st.write("3. 📥 **自動下載**：系統會從台茶改場網站下載PDF文件")
    st.write("4. 💬 **開始查詢**：在主頁面輸入您的問題")
    st.write("5. 🤖 **智能回答**：系統會基於茶葉知識庫回答")

# 主要內容區域
if st.session_state.system_ready and st.session_state.rag_system:
    # 知識庫摘要區塊
    st.header("📚 知識庫摘要")
    
    try:
        summary = st.session_state.rag_system.get_knowledge_base_summary()
        
        if summary:
            # 統計資訊
            stats = summary.get("statistics", {})
            topics = summary.get("topics", [])
            suggested_questions = summary.get("suggested_questions", [])
            
            # 顯示統計資訊
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 文件數量", stats.get("total_documents", 0))
            
            with col2:
                st.metric("📖 總頁數", stats.get("total_pages", 0))
            
            with col3:
                st.metric("🧩 文本塊數", stats.get("total_nodes", 0))
            
            with col4:
                if stats.get("total_documents", 0) > 0:
                    avg_pages = stats.get("total_pages", 0) / stats.get("total_documents", 1)
                    st.metric("📊 平均頁數", f"{avg_pages:.1f}")
                else:
                    st.metric("📊 平均頁數", "0")
            
            # 主題分類
            if topics:
                st.subheader("🏷️ 主要主題")
                
                # 使用列來顯示主題
                topic_cols = st.columns(min(len(topics), 4))  # 最多4列
                
                for i, topic in enumerate(topics):
                    col_idx = i % 4
                    with topic_cols[col_idx]:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                            padding: 1rem;
                            border-radius: 10px;
                            margin-bottom: 1rem;
                            border-left: 4px solid #4CAF50;
                        ">
                            <h4 style="margin: 0; color: #2c3e50;">
                                {topic.get('icon', '📋')} {topic.get('name', '未知主題')}
                            </h4>
                            <p style="margin: 0.5rem 0; color: #34495e; font-size: 0.9em;">
                                {topic.get('description', '無描述')}
                            </p>
                            <div style="margin-top: 0.5rem;">
                                {''.join([f'<span style="background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 12px; font-size: 0.8em; margin-right: 4px;">{keyword}</span>' for keyword in topic.get('keywords', [])])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # 文件詳情
            if stats.get("document_details"):
                with st.expander("📋 文件詳細資訊", expanded=False):
                    for doc in stats["document_details"]:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📄 **{doc.get('name', '未知')}**")
                        with col2:
                            st.write(f"📖 {doc.get('pages', 0)} 頁")
                        with col3:
                            st.write(f"🧩 {doc.get('node_count', 0)} 塊")
            
            # 建議問題
            if suggested_questions:
                st.subheader("💡 建議問題")
                st.write("以下是一些您可能感興趣的問題，點擊即可填入下方輸入框：")
                
                # 將建議問題分成兩列顯示
                question_cols = st.columns(2)
                
                for i, question in enumerate(suggested_questions):
                    col_idx = i % 2
                    with question_cols[col_idx]:
                        if st.button(f"💬 {question}", key=f"suggested_{i}", use_container_width=True):
                            # 將問題填入輸入框
                            st.session_state.question_input = question
                            st.rerun()
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"載入知識庫摘要時發生錯誤: {str(e)}")
    
    # 問答介面
    st.header("💬 智能問答")
    
    # 問題輸入
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_input(
            "請輸入您的問題：",
            placeholder="例如：台灣茶的特色是什麼？",
            key="question_input"
        )
    
    with col2:
        ask_button = st.button("🔍 詢問", type="primary")
    
    # 處理問答
    if ask_button and question:
        with st.container():
            st.markdown("### 💡 回答")
            
            # 執行查詢 (使用帶上下文記憶的查詢)
            response = st.session_state.rag_system.query_with_context(question)
            
            # 顯示回答
            st.markdown(response)
            
            # 添加分隔線
            st.markdown("---")
    
    # 歷史記錄
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if ask_button and question:
        st.session_state.chat_history.append({
            "question": question,
            "answer": response
        })
    
    # 顯示歷史記錄
    if st.session_state.chat_history:
        with st.expander("📜 問答歷史", expanded=False):
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # 顯示最近5筆
                st.write(f"**問題 {len(st.session_state.chat_history)-i}:** {chat['question']}")
                st.write(f"**回答:** {chat['answer']}")
                st.markdown("---")

else:
    # 歡迎頁面
    st.header("🌟 歡迎使用智能文檔問答助理")
    
    st.markdown("""
    ### 🤖 關於本系統
    
    這是一個**多模態RAG問答系統**，支援文檔、圖片OCR與對話記憶功能。系統預設載入台灣茶葉相關資料作為演示，
    同時支援使用者上傳任何類型的文檔和圖片，建立個人專屬的智能問答助理。
    
    ### ✨ 核心功能
    
    #### 📄 多格式文檔支援
    - **PDF文檔**：自動解析PDF內容並建立索引
    - **文字檔案**：支援TXT、MD格式
    - **Office文檔**：支援DOCX格式（開發中）
    
    #### 🖼️ 智能OCR識別
    - **圖片文字識別**：使用Google Gemini 2.5 Pro進行高精度OCR
    - **多語言支援**：中文、英文混合內容識別
    - **格式保持**：保留原始排版、表格、列表結構
    
    #### 🧠 對話記憶功能
    - **上下文感知**：記住前N步對話內容
    - **智能問答**：結合歷史對話提供更精準的回答
    - **記憶管理**：可查看、清除對話記憶
    
    #### 🔍 高效向量搜尋
    - **ChromaDB儲存**：高效能向量資料庫
    - **語義搜尋**：基於內容語義而非關鍵詞匹配
    - **多資料源整合**：統一搜尋所有上傳的資料
    
    ### 🚀 使用流程
    
    1. **🔧 系統初始化**：點擊左側「初始化系統」載入預設茶葉資料
    2. **📤 檔案上傳**：上傳您的文檔或圖片到系統
    3. **🔍 OCR處理**：圖片自動進行文字識別
    4. **💬 智能問答**：開始與您的文檔進行對話
    5. **🧠 記憶對話**：系統會記住對話歷史，提供連續對話體驗
    
    ### 📊 預設演示資料
    
    系統預設包含**台灣茶葉相關資料**作為功能展示：
    - 🍵 台灣茶業研究彙報
    - 📋 茶樹品種與栽培技術
    - 🏭 製茶工藝與品質評鑑
    - 📈 茶業發展與市場分析
    
    *資料來源：[台灣茶及飲料作物改良場](https://www.tbrs.gov.tw/)*
    
    ### 💡 使用建議
    
    - **首次使用**：先體驗預設茶葉資料，了解系統能力
    - **個人化使用**：上傳您的工作文檔、學習資料或研究資料
    - **圖片文字**：上傳包含文字的圖片，系統會自動識別並加入知識庫
    - **連續對話**：善用對話記憶功能，進行深度討論和分析
    """)
    
    # 功能特色展示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 🎯 精準問答
        - 語義理解查詢
        - 上下文感知回答
        - 多資料源整合
        """)
    
    with col2:
        st.markdown("""
        #### 🚀 高效處理
        - ChromaDB向量儲存
        - 批次檔案處理
        - 增量索引更新
        """)
    
    with col3:
        st.markdown("""
        #### 🔒 資料安全
        - 本地向量儲存
        - 檔案持久化保存
        - API安全調用
        """)
    
    # 顯示技術架構
    with st.expander("🔧 技術架構", expanded=False):
        st.markdown("""
        ### 核心技術棧
        
        #### 🎨 前端界面
        - **Streamlit**: 響應式Web界面
        - **多頁面佈局**: 檔案上傳、記憶管理、系統狀態
        
        #### 🧠 AI模型
        - **語言模型**: Groq (Llama3-70B) - RAG問答
        - **OCR模型**: Google Gemini 2.5 Pro - 圖片文字識別
        - **嵌入模型**: HuggingFace Sentence Transformers
        
        #### 💾 資料儲存
        - **向量資料庫**: ChromaDB (持久化儲存)
        - **檔案系統**: 本地檔案管理與備份
        - **記憶管理**: 對話歷史暫存
        
        #### 🔧 處理引擎
        - **RAG框架**: LlamaIndex
        - **文檔解析**: PyMuPDF, python-docx, 等
        - **圖片處理**: Pillow, OpenCV
        
        #### 🌐 API整合
        - **Groq API**: 高速LLM推理
        - **Google Gemini API**: 多模態AI能力
        - **RESTful設計**: 模組化API架構
        """)

# 頁腳
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    🍵 台灣茶葉知識問答系統 | 
    資料來源：<a href='https://www.tbrs.gov.tw/' target='_blank'>台灣茶及飲料作物改良場</a>
    </div>
    """, 
    unsafe_allow_html=True
)
