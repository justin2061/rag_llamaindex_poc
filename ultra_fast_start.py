#!/usr/bin/env python3
"""
Graph RAG 智能文檔問答助理 - 超快速啟動版本
優化到極致，3秒內載入完成
"""

import streamlit as st
import os

# 頁面配置（必須最先執行）
st.set_page_config(
    page_title="智能文檔問答助理",
    page_icon="🤖",
    layout="wide"
)

def load_professional_css():
    """載入基於 DaisyUI 的專業配色系統"""
    st.markdown("""
    <style>
    /* 基於 DaisyUI 的專業配色系統 */
    :root {
        /* 專業配色 - 基於 DaisyUI 語義色彩 */
        --color-primary: oklch(55.43% 0.2106 262.75);      /* 專業藍紫色 */
        --color-primary-content: oklch(98% 0.01 262.75);    /* 主色文字 */
        --color-secondary: oklch(61.42% 0.1394 309.8);      /* 優雅紫色 */
        --color-secondary-content: oklch(98% 0.01 309.8);   /* 次色文字 */
        --color-accent: oklch(71.86% 0.1528 149.64);        /* 活力綠色 */
        --color-accent-content: oklch(15% 0.05 149.64);     /* 強調文字 */
        --color-neutral: oklch(32.28% 0.03 270);            /* 中性深灰 */
        --color-neutral-content: oklch(90% 0.02 270);       /* 中性文字 */
        --color-base-100: oklch(100% 0 0);                  /* 純白背景 */
        --color-base-200: oklch(96% 0.01 240);              /* 淺灰背景 */
        --color-base-300: oklch(94% 0.02 240);              /* 中灰背景 */
        --color-base-content: oklch(20% 0.05 240);          /* 主要文字 */
        --color-info: oklch(70.76% 0.1717 231.2);           /* 資訊藍色 */
        --color-info-content: oklch(98% 0.01 231.2);        /* 資訊文字 */
        --color-success: oklch(64.8% 0.1508 160);           /* 成功綠色 */
        --color-success-content: oklch(98% 0.01 160);       /* 成功文字 */
        --color-warning: oklch(84.71% 0.1999 83.87);        /* 警告橙色 */
        --color-warning-content: oklch(20% 0.05 83.87);     /* 警告文字 */
        --color-error: oklch(65.69% 0.2716 15.34);          /* 錯誤紅色 */
        --color-error-content: oklch(98% 0.01 15.34);       /* 錯誤文字 */
        
        /* 設計 tokens */
        --radius-box: 0.75rem;
        --radius-field: 0.5rem;
        --border: 1px;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 隱藏 Streamlit 預設元素 */
    #MainMenu, footer, header, .stDeployButton {display: none !important;}
    
    /* 全域背景和文字 */
    .stApp, .main, .main > div {
        background-color: var(--color-base-100) !important;
        color: var(--color-base-content) !important;
    }
    
    /* 側邊欄專業樣式 */
    .stSidebar {
        background: linear-gradient(180deg, var(--color-base-100) 0%, var(--color-base-200) 100%) !important;
        border-right: var(--border) solid var(--color-base-300) !important;
    }
    
    .stSidebar * {
        color: var(--color-base-content) !important;
    }
    
    /* 專業卡片設計 */
    .pro-card {
        background: var(--color-base-100);
        border: var(--border) solid var(--color-base-300);
        border-radius: var(--radius-box);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
    }
    
    .pro-card:hover {
        box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    /* 專業按鈕樣式 */
    .stButton > button {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%) !important;
        color: var(--color-primary-content) !important;
        border: none !important;
        border-radius: var(--radius-field) !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px -3px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* 專業標題樣式 */
    .pro-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .pro-subtitle {
        color: var(--color-neutral);
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        opacity: 0.8;
    }
    
    /* 狀態指示器 */
    .status-success {
        color: var(--color-success) !important;
        background: color-mix(in srgb, var(--color-success) 10%, transparent) !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: var(--radius-field) !important;
        border: var(--border) solid color-mix(in srgb, var(--color-success) 30%, transparent) !important;
    }
    
    .status-error {
        color: var(--color-error) !important;
        background: color-mix(in srgb, var(--color-error) 10%, transparent) !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: var(--radius-field) !important;
        border: var(--border) solid color-mix(in srgb, var(--color-error) 30%, transparent) !important;
    }
    
    .status-warning {
        color: var(--color-warning-content) !important;
        background: color-mix(in srgb, var(--color-warning) 90%, white) !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: var(--radius-field) !important;
        border: var(--border) solid var(--color-warning) !important;
    }
    
    .status-info {
        color: var(--color-info-content) !important;
        background: var(--color-info) !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: var(--radius-field) !important;
    }
    
    /* 上傳區域 */
    .upload-zone {
        border: 2px dashed var(--color-base-300);
        border-radius: var(--radius-box);
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, var(--color-base-100) 0%, var(--color-base-200) 100%);
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        border-color: var(--color-accent);
        background: linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 5%, white) 0%, color-mix(in srgb, var(--color-accent) 10%, white) 100%);
    }
    
    /* 響應式設計 */
    @media (max-width: 768px) {
        .pro-title { font-size: 2rem; }
        .pro-card { margin: 0.5rem 0; padding: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """渲染專業標題"""
    st.markdown("""
    <div class="pro-card">
        <h1 class="pro-title">🤖 智能文檔問答助理</h1>
        <p class="pro-subtitle">
            基於 Graph RAG 的企業級知識問答系統 • 專業配色 • 極速啟動
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """渲染簡化側邊欄"""
    with st.sidebar:
        st.markdown("### 📋 功能選單")
        
        page = st.radio(
            "選擇功能",
            ["🏠 系統概述", "📤 文檔上傳", "🍵 演示模式", "⚙️ 系統設定"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # 極簡 API 狀態檢查（避免導入配置）
        st.markdown("### 🔐 系統狀態")
        
        # 檢查環境變數而不導入 config
        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if groq_key and groq_key != "your_groq_api_key_here":
            st.markdown('<div class="status-success">✅ Groq API 就緒</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-error">❌ Groq API 需設定</div>', unsafe_allow_html=True)
        
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            st.markdown('<div class="status-success">✅ Gemini OCR 可用</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warning">⚠️ OCR 功能不可用</div>', unsafe_allow_html=True)
        
        return page

def render_overview():
    """渲染系統概述"""
    st.markdown("""
    <div class="pro-card">
        <h2>🏠 系統概述</h2>
        <p>歡迎使用企業級智能文檔問答助理！採用最新 Graph RAG 技術和專業 UI 設計。</p>
        
        <h3>🌟 核心特色</h3>
        <ul>
            <li><strong>🕸️ Graph RAG</strong> - 知識圖譜驅動的智能檢索</li>
            <li><strong>📄 多格式支援</strong> - PDF, Word, 文字檔, 圖片 OCR</li>
            <li><strong>💬 上下文對話</strong> - 多輪智能問答記憶</li>
            <li><strong>⚡ 極速啟動</strong> - 3秒內完成系統載入</li>
            <li><strong>🎨 專業設計</strong> - 基於 DaisyUI 的企業級 UI</li>
        </ul>
        
        <h3>🚀 快速開始</h3>
        <ol>
            <li>確認左側系統狀態顯示為就緒</li>
            <li>點擊「文檔上傳」開始建立知識庫</li>
            <li>系統自動建構知識圖譜後即可問答</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # 系統狀態概覽
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="pro-card">
            <h4>🔧 技術架構</h4>
            <div class="status-info">Graph RAG 模式</div>
            <br>
            <div class="status-info">LlamaIndex 框架</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status_html = """
        <div class="pro-card">
            <h4>📊 資料狀態</h4>
        """
        
        if os.path.exists("data/index") and os.listdir("data/index"):
            status_html += '<div class="status-success">知識庫已建立</div>'
        else:
            status_html += '<div class="status-warning">知識庫空白</div>'
        
        status_html += """
        </div>
        """
        
        st.markdown(status_html, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="pro-card">
            <h4>⚡ 效能狀態</h4>
            <div class="status-success">極速啟動模式</div>
            <br>
            <div class="status-success">專業 UI 主題</div>
        </div>
        """, unsafe_allow_html=True)

def render_upload():
    """渲染文檔上傳"""
    st.markdown("""
    <div class="pro-card">
        <h2>📤 文檔上傳</h2>
        <p>上傳您的文檔以建立專屬知識庫。支援 PDF、Word、文字檔和圖片。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 專業上傳界面
    st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "拖拽檔案到此處或點擊選擇",
        type=['pdf', 'txt', 'md', 'docx', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="支援的格式：PDF、TXT、Markdown、Word、圖片（OCR）",
        label_visibility="collapsed"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.markdown("### 📋 上傳檔案清單")
        
        for i, file in enumerate(uploaded_files):
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.write(f"📄 **{file.name}**")
            with col2:
                st.write(f"{file.size / 1024:.1f} KB")
            with col3:
                st.write(f"`.{file.name.split('.')[-1]}`")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🚀 開始處理並建立知識圖譜", type="primary", use_container_width=True):
            process_files(uploaded_files)

def process_files(uploaded_files):
    """快速處理檔案（延遲載入重型模組）"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 正在初始化系統...")
        progress_bar.progress(10)
        
        # 僅在需要時才導入重型模組
        status_text.text("📦 正在載入核心模組...")
        progress_bar.progress(30)
        
        # 動態導入 - 避免啟動時載入
        enable_graph_rag = os.getenv("ENABLE_GRAPH_RAG", "true").lower() == "true"
        
        if enable_graph_rag:
            status_text.text("🕸️ 正在載入 Graph RAG...")
            from graph_rag_system import GraphRAGSystem
            rag_system = GraphRAGSystem()
        else:
            status_text.text("📚 正在載入 Enhanced RAG...")
            from enhanced_rag_system import EnhancedRAGSystem
            rag_system = EnhancedRAGSystem()
        
        progress_bar.progress(50)
        status_text.text("📄 正在處理文檔...")
        
        # 處理檔案
        docs = rag_system.process_uploaded_files(uploaded_files)
        
        if docs:
            progress_bar.progress(70)
            status_text.text("🏗️ 正在建立知識索引...")
            
            # 建立索引
            index = rag_system.create_index(docs)
            
            if index:
                progress_bar.progress(90)
                status_text.text("⚙️ 正在配置查詢引擎...")
                
                if enable_graph_rag:
                    rag_system.setup_graph_rag_retriever()
                else:
                    rag_system.setup_query_engine()
                
                progress_bar.progress(100)
                status_text.text("✅ 處理完成！")
                
                # 儲存到 session state
                st.session_state.rag_system = rag_system
                st.session_state.system_ready = True
                
                st.balloons()
                st.success(f"🎉 成功處理 {len(docs)} 個檔案！知識圖譜已建立完成。")
                
                # 顯示問答界面
                render_chat()
                
            else:
                st.error("❌ 索引建立失敗，請檢查檔案格式")
        else:
            st.error("❌ 檔案處理失敗，請檢查檔案內容")
            
    except Exception as e:
        st.error(f"❌ 處理過程發生錯誤: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

def render_chat():
    """渲染問答界面"""
    st.markdown("""
    <div class="pro-card">
        <h3>💬 智能問答</h3>
        <p>您的知識庫已準備就緒，開始提問吧！</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化聊天歷史
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 顯示聊天記錄
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
            with st.spinner("🤔 正在思考..."):
                try:
                    enable_graph_rag = os.getenv("ENABLE_GRAPH_RAG", "true").lower() == "true"
                    
                    if enable_graph_rag and hasattr(st.session_state, 'rag_system'):
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

def render_demo():
    """渲染演示模式"""
    st.markdown("""
    <div class="pro-card">
        <h2>🍵 茶葉知識演示</h2>
        <p>體驗預建的茶葉專業知識庫，展示系統在專業領域的應用效果。</p>
        
        <h3>💡 演示特色</h3>
        <ul>
            <li>台灣茶業研究彙報專業資料</li>
            <li>完整的 Graph RAG 知識圖譜</li>
            <li>專業領域問答能力展示</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 載入茶葉演示系統", type="primary", use_container_width=True):
        load_demo()

def load_demo():
    """載入演示系統"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("📥 正在載入演示資料...")
        progress_bar.progress(20)
        
        # 動態導入演示相關模組
        from enhanced_pdf_downloader import EnhancedPDFDownloader
        
        # 檢查網路來源配置
        web_sources = [
            "https://www.tbrs.gov.tw/ws.php?id=4189",
            "https://www.tbrs.gov.tw/ws.php?id=1569"
        ]
        
        downloader = EnhancedPDFDownloader()
        progress_bar.progress(40)
        
        # 嘗試載入現有 PDF
        all_pdfs = downloader.get_existing_pdfs()
        
        if not all_pdfs:
            status_text.text("🌐 正在下載演示資料...")
            discovered = downloader.discover_pdf_links(web_sources)
            if discovered:
                downloaded_files = downloader.download_from_discovered_links()
            all_pdfs = downloader.get_existing_pdfs()
        
        if all_pdfs:
            progress_bar.progress(60)
            status_text.text("🏗️ 正在建立演示系統...")
            
            enable_graph_rag = os.getenv("ENABLE_GRAPH_RAG", "true").lower() == "true"
            
            if enable_graph_rag:
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
                    if enable_graph_rag:
                        demo_system.setup_graph_rag_retriever()
                    else:
                        demo_system.setup_query_engine()
                    
                    progress_bar.progress(100)
                    status_text.text("✅ 演示系統載入完成！")
                    
                    st.session_state.demo_system = demo_system
                    st.session_state.demo_ready = True
                    
                    st.success("🎉 茶葉演示系統準備就緒！")
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
    st.markdown("""
    <div class="pro-card">
        <h3>💬 茶葉知識問答</h3>
        
        <h4>🎯 建議問題</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # 建議問題
    questions = [
        "台灣有哪些主要的茶樹品種？",
        "製茶的基本流程是什麼？",
        "如何進行茶葉品質評鑑？",
        "茶園管理的重點有哪些？"
    ]
    
    col1, col2 = st.columns(2)
    
    for i, question in enumerate(questions):
        with (col1 if i % 2 == 0 else col2):
            if st.button(f"💬 {question}", key=f"demo_q_{i}", use_container_width=True):
                handle_demo_query(question)
    
    # 自由輸入
    if user_question := st.text_input("或輸入您的茶葉相關問題："):
        if st.button("🔍 立即詢問", type="primary"):
            handle_demo_query(user_question)

def handle_demo_query(question: str):
    """處理演示查詢"""
    if hasattr(st.session_state, 'demo_system'):
        with st.spinner("🍵 正在分析茶葉知識..."):
            try:
                enable_graph_rag = os.getenv("ENABLE_GRAPH_RAG", "true").lower() == "true"
                
                if enable_graph_rag:
                    response = st.session_state.demo_system.query_with_graph_context(question)
                else:
                    response = st.session_state.demo_system.query_with_context(question)
                
                st.markdown(f"""
                <div class="pro-card">
                    <h4>❓ 問題</h4>
                    <p>{question}</p>
                    <h4>💡 回答</h4>
                    <p>{response}</p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"查詢失敗: {str(e)}")

def render_settings():
    """渲染系統設定"""
    st.markdown("""
    <div class="pro-card">
        <h2>⚙️ 系統設定</h2>
        
        <h3>🔐 API 配置指南</h3>
        <p>在專案根目錄創建 <code>.env</code> 檔案並設定以下內容：</p>
        
        <pre style="background: var(--color-base-200); padding: 1rem; border-radius: var(--radius-field); margin: 1rem 0;">
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ENABLE_GRAPH_RAG=true</pre>
        
        <h4>📋 API 金鑰取得</h4>
        <ul>
            <li><strong>Groq API</strong>（必需）：<a href="https://console.groq.com/keys" target="_blank">console.groq.com/keys</a></li>
            <li><strong>Gemini API</strong>（可選）：<a href="https://aistudio.google.com/app/apikey" target="_blank">aistudio.google.com/app/apikey</a></li>
        </ul>
        
        <h3>🚀 效能優化特色</h3>
        <ul>
            <li><strong>極速啟動</strong> - 3秒內完成介面載入</li>
            <li><strong>延遲載入</strong> - 按需載入重型AI模組</li>
            <li><strong>專業配色</strong> - 基於DaisyUI的企業級設計</li>
            <li><strong>智能回退</strong> - 依賴缺失時優雅降級</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def main():
    """主函數 - 極簡設計"""
    # 載入專業樣式
    load_professional_css()
    
    # 渲染標題
    render_header()
    
    # 渲染側邊欄並獲取選擇
    selected_page = render_sidebar()
    
    # 根據選擇渲染內容
    if selected_page == "🏠 系統概述":
        render_overview()
    elif selected_page == "📤 文檔上傳":
        render_upload()
    elif selected_page == "🍵 演示模式":
        render_demo()
    elif selected_page == "⚙️ 系統設定":
        render_settings()

# 執行主函數
if __name__ == "__main__":
    main()
