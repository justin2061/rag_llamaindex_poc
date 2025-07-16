import streamlit as st
import os
from enhanced_pdf_downloader import EnhancedPDFDownloader
from rag_system import RAGSystem
from config import PAGE_TITLE, PAGE_ICON, GROQ_API_KEY, WEB_SOURCES

# 頁面配置
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 標題
st.title(f"{PAGE_ICON} {PAGE_TITLE}")
st.markdown("---")

# 初始化session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'system_ready' not in st.session_state:
    st.session_state.system_ready = False

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
    if st.button("🚀 初始化系統", type="primary"):
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
                    rag_system = RAGSystem()
                    
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
    
    # 顯示系統狀態
    st.markdown("---")
    st.header("📊 系統狀態")
    
    if st.session_state.system_ready:
        st.success("🟢 系統已就緒")
        
        # 顯示載入的文件
        if st.session_state.rag_system:
            sources = st.session_state.rag_system.get_source_info()
            if sources:
                st.write("📚 已載入的文件:")
                for source in sources:
                    st.write(f"• {source}")
    else:
        st.warning("🟡 系統尚未初始化")
    
    st.markdown("---")
    st.write("📖 **使用說明:**")
    st.write("1. 首次使用請點擊「初始化系統」")
    st.write("2. 系統會自動從台茶改場網站發現並下載PDF文件")
    st.write("3. 等待系統處理文件並建立知識庫")
    st.write("4. 在主頁面輸入您的問題")
    st.write("5. 系統會基於茶葉知識庫回答")

# 主要內容區域
if st.session_state.system_ready and st.session_state.rag_system:
    # 問答介面
    st.header("💬 智能問答")
    
    # 預設問題
    sample_questions = [
        "台灣茶的主要品種有哪些？",
        "製茶的基本流程是什麼？",
        "如何進行茶葉品質評鑑？",
        "茶園的栽培管理要注意什麼？",
        "台灣茶業的發展歷史如何？"
    ]
    
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
    
    # 快速問題按鈕
    st.write("📝 **快速問題：**")
    cols = st.columns(len(sample_questions))
    for i, sample_q in enumerate(sample_questions):
        if cols[i].button(sample_q, key=f"sample_{i}"):
            question = sample_q
            ask_button = True
    
    # 處理問答
    if ask_button and question:
        with st.container():
            st.markdown("### 💡 回答")
            
            # 執行查詢
            response = st.session_state.rag_system.query(question)
            
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
    st.header("🌟 歡迎使用台灣茶葉知識問答系統")
    
    st.markdown("""
    ### 🍵 關於本系統
    
    這是一個基於人工智慧的茶葉知識問答系統，會**自動從台灣茶及飲料作物改良場網站發現並下載最新的PDF文件**，建立完整的茶葉知識庫。
    
    ### ✨ 主要功能
    - 🤖 **智能問答**：基於專業茶葉文獻的AI問答
    - 🔍 **自動發現**：自動從官方網站發現並下載最新PDF文件
    - 📚 **動態知識庫**：即時更新的台茶改場研究資料
    - 🎯 **精準搜尋**：使用向量搜尋技術找到最相關的資訊
    - 💡 **即時回應**：快速獲得專業的茶葉知識解答
    
    ### 🚀 開始使用
    請在左側邊欄點擊「初始化系統」按鈕，系統會自動發現並下載台茶改場網站上的所有PDF文件。
    
    ### 📖 資料來源
    本系統會自動從以下網站發現並下載PDF文件：
    - 台灣茶業研究彙報摘要頁面
    - 其他茶業相關資料頁面
    - 所有在台茶改場網站上可找到的PDF文件
    
    資料來源：[台灣茶及飲料作物改良場](https://www.tbrs.gov.tw/)
    """)
    
    # 顯示技術架構
    with st.expander("🔧 技術架構", expanded=False):
        st.markdown("""
        - **前端框架**：Streamlit
        - **RAG框架**：LlamaIndex
        - **語言模型**：Groq (Llama3-8B)
        - **嵌入模型**：HuggingFace Sentence Transformers
        - **向量資料庫**：ChromaDB
        - **文件處理**：PyMuPDF
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