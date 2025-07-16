import streamlit as st
import os
from enhanced_pdf_downloader import EnhancedPDFDownloader
from rag_system import RAGSystem
from config import PAGE_TITLE, PAGE_ICON, GROQ_API_KEY, WEB_SOURCES
from utils import validate_groq_api_key

# 頁面配置
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 10px;
    }
    .status-card {
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1e3c72;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .question-card {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        background-color: #e3f2fd;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .question-card:hover {
        background-color: #bbdefb;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# 主標題
st.markdown(f"""
<div class="main-header">
    <h1>{PAGE_ICON} {PAGE_TITLE}</h1>
    <p>基於AI的智能茶葉知識問答系統</p>
</div>
""", unsafe_allow_html=True)

# 初始化session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'system_ready' not in st.session_state:
    st.session_state.system_ready = False
if 'downloader' not in st.session_state:
    st.session_state.downloader = EnhancedPDFDownloader()

# 側邊欄
with st.sidebar:
    st.header("🛠️ 系統控制台")
    
    # API Key檢查
    api_status = validate_groq_api_key(GROQ_API_KEY)
    if api_status:
        st.success("✅ Groq API Key 已正確設定")
    else:
        st.error("❌ Groq API Key 未設定或格式不正確")
        st.info("請在 .env 檔案中設定您的 Groq API Key")
        st.code('GROQ_API_KEY=your_actual_api_key_here')
    
    st.markdown("---")
    
    # 系統設定選項
    st.subheader("📋 初始化選項")
    
    auto_discover = st.checkbox("🔍 自動發現PDF連結", value=True, 
                               help="從網頁自動搜尋並下載PDF檔案")
    
    use_existing = st.checkbox("📁 使用現有檔案", value=True,
                              help="使用已下載的PDF檔案")
    
    # 系統初始化
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 完整初始化", type="primary"):
            if api_status:
                with st.spinner("正在執行完整初始化..."):
                    success = perform_full_initialization(auto_discover, use_existing)
                    if success:
                        st.balloons()
            else:
                st.error("請先設定正確的API Key")
    
    with col2:
        if st.button("🔄 重新載入"):
            st.session_state.system_ready = False
            st.session_state.rag_system = None
            st.rerun()
    
    # 快速操作
    st.markdown("---")
    st.subheader("⚡ 快速操作")
    
    if st.button("📥 僅下載PDF"):
        download_pdfs_only(auto_discover)
    
    if st.button("🔧 僅建立索引"):
        build_index_only()
    
    # 系統狀態
    st.markdown("---")
    st.subheader("📊 系統狀態")
    
    status_color = "🟢" if st.session_state.system_ready else "🟡"
    status_text = "就緒" if st.session_state.system_ready else "待初始化"
    
    st.markdown(f"""
    <div class="status-card">
        <strong>{status_color} 系統狀態:</strong> {status_text}
    </div>
    """, unsafe_allow_html=True)
    
    # 顯示已載入的文件
    if st.session_state.system_ready and st.session_state.rag_system:
        sources = st.session_state.rag_system.get_source_info()
        if sources:
            st.write("📚 **已載入的文件:**")
            for i, source in enumerate(sources, 1):
                st.write(f"{i}. {source}")
    
    # 檔案資訊
    pdf_info = st.session_state.downloader.get_pdf_info()
    if pdf_info:
        with st.expander("📄 檔案詳情", expanded=False):
            for filename, info in pdf_info.items():
                st.write(f"**{filename}**")
                st.write(f"大小: {info['size']}")

def perform_full_initialization(auto_discover: bool, use_existing: bool) -> bool:
    """執行完整的系統初始化"""
    try:
        downloader = st.session_state.downloader
        
        # 步驟1: 處理PDF檔案
        if auto_discover:
            st.info("🔍 步驟1: 自動發現PDF連結")
            discovered = downloader.discover_pdf_links(WEB_SOURCES)
            st.write(f"🔍 發現的連結: {discovered}")  # 除錯用
            
            if discovered:
                st.info("📥 步驟2: 下載發現的PDF檔案")
                downloaded = downloader.download_from_discovered_links()
                st.write(f"📥 下載結果: {len(downloaded) if downloaded else 0} 個來源")
            else:
                st.warning("⚠️ 未從網頁自動發現PDF連結")
                st.info("📥 步驟2: 使用預設PDF連結")
                # 使用預設的PDF來源
                from pdf_downloader import PDFDownloader
                basic_downloader = PDFDownloader()
                downloaded = basic_downloader.download_all_pdfs()
        else:
            st.info("📥 步驟1: 使用預設PDF連結 (未啟用自動發現)")
            from pdf_downloader import PDFDownloader
            basic_downloader = PDFDownloader()
            downloaded = basic_downloader.download_all_pdfs()
        
        # 獲取所有PDF檔案
        all_pdfs = downloader.get_existing_pdfs()
        
        if not all_pdfs:
            st.error("❌ 未找到任何PDF檔案")
            return False
        
        st.info(f"📚 步驟3: 初始化RAG系統 (共 {len(all_pdfs)} 個檔案)")
        
        # 初始化RAG系統
        rag_system = RAGSystem()
        
        # 載入文件
        documents = rag_system.load_pdfs(all_pdfs)
        
        if not documents:
            st.error("❌ 載入文件失敗")
            return False
        
        st.info("🔨 步驟4: 建立向量索引")
        
        # 建立索引
        index = rag_system.create_index(documents)
        
        if not index:
            st.error("❌ 建立索引失敗")
            return False
        
        st.info("⚙️ 步驟5: 設定查詢引擎")
        
        # 設定查詢引擎
        rag_system.setup_query_engine()
        
        # 儲存到session state
        st.session_state.rag_system = rag_system
        st.session_state.system_ready = True
        
        st.success("✅ 系統初始化完成！")
        return True
        
    except Exception as e:
        st.error(f"❌ 初始化過程中發生錯誤: {str(e)}")
        return False

def download_pdfs_only(auto_discover: bool):
    """僅下載PDF檔案"""
    downloader = st.session_state.downloader
    
    if auto_discover:
        discovered = downloader.discover_pdf_links(WEB_SOURCES)
        if discovered:
            downloader.download_from_discovered_links()
    else:
        from pdf_downloader import PDFDownloader
        basic_downloader = PDFDownloader()
        basic_downloader.download_all_pdfs()

def build_index_only():
    """僅建立索引"""
    all_pdfs = st.session_state.downloader.get_existing_pdfs()
    
    if not all_pdfs:
        st.error("❌ 未找到PDF檔案，請先下載")
        return
    
    rag_system = RAGSystem()
    documents = rag_system.load_pdfs(all_pdfs)
    
    if documents:
        index = rag_system.create_index(documents)
        if index:
            rag_system.setup_query_engine()
            st.session_state.rag_system = rag_system
            st.session_state.system_ready = True

# 主要內容區域
if st.session_state.system_ready and st.session_state.rag_system:
    # 智能問答介面
    st.header("💬 智能問答系統")
    
    # 預設問題
    sample_questions = [
        "台灣有哪些主要的茶葉品種？各有什麼特色？",
        "製茶的完整流程包括哪些步驟？",
        "如何進行專業的茶葉感官品評？",
        "茶園栽培管理的關鍵要點是什麼？",
        "台灣茶業的發展歷史和現況如何？",
        "不同發酵程度的茶葉有什麼差異？",
        "茶葉的品質評鑑標準是什麼？",
        "如何選擇適合的茶葉品種進行種植？"
    ]
    
    # 問題輸入區域
    col1, col2 = st.columns([4, 1])
    
    with col1:
        question = st.text_input(
            "🤔 請輸入您的問題：",
            placeholder="例如：台灣烏龍茶的製作工藝有什麼特色？",
            key="question_input",
            help="您可以詢問關於茶葉種植、製作、品評等各方面的問題"
        )
    
    with col2:
        ask_button = st.button("🔍 提問", type="primary", use_container_width=True)
    
    # 快速問題選擇
    st.write("💡 **熱門問題 (點擊快速提問):**")
    
    # 將問題分為兩行顯示
    cols1 = st.columns(4)
    cols2 = st.columns(4)
    
    for i, sample_q in enumerate(sample_questions[:4]):
        if cols1[i].button(sample_q, key=f"sample_{i}", use_container_width=True):
            question = sample_q
            ask_button = True
    
    for i, sample_q in enumerate(sample_questions[4:], 4):
        if cols2[i-4].button(sample_q, key=f"sample_{i}", use_container_width=True):
            question = sample_q
            ask_button = True
    
    # 處理問答
    if ask_button and question:
        st.markdown("### 🎯 智能回答")
        
        with st.container():
            # 執行查詢
            response = st.session_state.rag_system.query(question)
            
            # 顯示回答
            st.markdown(f"""
            <div style="background-color: #f0f8ff; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #1e88e5;">
                {response}
            </div>
            """, unsafe_allow_html=True)
            
            # 添加評價按鈕
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("👍 有幫助"):
                    st.success("感謝您的回饋！")
            with col2:
                if st.button("👎 需改進"):
                    st.info("我們會持續改進系統")
    
    # 問答歷史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if ask_button and question:
        st.session_state.chat_history.append({
            "question": question,
            "answer": response
        })
    
    # 顯示歷史記錄
    if st.session_state.chat_history:
        with st.expander("📜 問答歷史 (最近5筆)", expanded=False):
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
                st.markdown(f"**Q{len(st.session_state.chat_history)-i}:** {chat['question']}")
                st.markdown(f"**A:** {chat['answer']}")
                st.markdown("---")

else:
    # 歡迎頁面
    st.markdown("""
    ## 🌟 歡迎使用台灣茶葉知識問答系統
    
    ### 🍵 系統簡介
    本系統整合了台灣茶及飲料作物改良場的專業研究資料，運用先進的AI技術為您提供準確的茶葉知識解答。
    
    ### ✨ 核心功能
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🤖 智能問答**
        - 基於專業文獻的AI回答
        - 支援中文自然語言查詢
        - 即時精準的知識檢索
        
        **📚 豐富知識庫**
        - 台灣茶業研究彙報
        - 專業製茶技術文獻
        - 品種培育研究資料
        """)
    
    with col2:
        st.markdown("""
        **🔍 智能搜尋**
        - 向量化語義搜尋
        - 多文檔內容整合
        - 相關度排序回答
        
        **⚡ 高效體驗**
        - 響應式網頁設計
        - 問答歷史記錄
        - 快速問題模板
        """)
    
    st.markdown("""
    ### 🚀 開始使用
    請點擊左側邊欄的「**🚀 完整初始化**」按鈕來啟動系統。首次使用需要下載並處理PDF文件，請耐心等待。
    
    ### 📖 資料來源
    """)
    
    st.info("本系統知識庫來源：[台灣茶及飲料作物改良場](https://www.tbrs.gov.tw/) 官方研究文獻")
    
    # 技術規格
    with st.expander("🔧 技術架構詳情", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **前端技術**
            - Streamlit 網頁框架
            - 響應式UI設計
            - 即時狀態更新
            
            **AI模型**
            - Groq Llama3-8B語言模型
            - HuggingFace嵌入模型
            - 向量相似度搜尋
            """)
        
        with col2:
            st.markdown("""
            **後端架構**
            - LlamaIndex RAG框架
            - ChromaDB向量資料庫
            - PyMuPDF文檔處理
            
            **數據處理**
            - 自動PDF下載
            - 智能文本分塊
            - 語義索引建立
            """)

# 頁腳
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🍵 <strong>台灣茶葉知識問答系統</strong> | 
    資料來源：<a href='https://www.tbrs.gov.tw/' target='_blank' style='color: #1e88e5;'>台灣茶及飲料作物改良場</a> | 
    技術支援：LlamaIndex + Groq + HuggingFace
</div>
""", unsafe_allow_html=True) 