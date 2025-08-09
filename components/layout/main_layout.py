import streamlit as st
from streamlit_option_menu import option_menu

class MainLayout:
    """主應用程式佈局管理器"""
    
    def __init__(self):
        self.current_page = None
        self.setup_page_config()
        
    def setup_page_config(self):
        """設置頁面配置"""
        st.set_page_config(
            page_title="智能文檔問答助理",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def load_custom_css(self):
        """載入自定義CSS樣式"""
        st.markdown("""
        <style>
        /* 主要樣式系統 */
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --border-color: #e5e7eb;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* 隱藏Streamlit默認元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* 主容器樣式 */
        .main > div {
            padding-top: 1rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* 卡片樣式 */
        .custom-card {
            background: var(--card-background);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
            transition: all 0.3s ease;
        }
        
        .custom-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        /* 標題樣式 */
        .page-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        .page-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* 按鈕樣式 */
        .stButton > button {
            border-radius: 0.5rem;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow);
        }
        
        /* 統計卡片樣式 */
        .metric-card {
            background: var(--card-background);
            border-radius: 0.75rem;
            padding: 1rem;
            text-align: center;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
        }
        
        /* 上傳區域樣式 */
        .upload-zone {
            border: 2px dashed var(--border-color);
            border-radius: 1rem;
            padding: 2rem;
            text-align: center;
            background: var(--background-color);
            transition: all 0.3s ease;
        }
        
        .upload-zone:hover {
            border-color: var(--primary-color);
            background: rgba(102, 126, 234, 0.05);
        }
        
        /* 聊天訊息樣式 */
        .chat-message {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 1rem;
            max-width: 80%;
        }
        
        .chat-message.user {
            background: var(--primary-color);
            color: white;
            margin-left: auto;
        }
        
        .chat-message.assistant {
            background: var(--card-background);
            border: 1px solid var(--border-color);
        }
        
        /* 響應式設計 */
        @media (max-width: 768px) {
            .main > div {
                padding: 0.5rem;
            }
            
            .page-title {
                font-size: 2rem;
            }
            
            .custom-card {
                margin: 0.5rem 0;
                padding: 1rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def render_header(self):
        """渲染頁面標題"""
        st.markdown("""
        <div class="custom-card">
            <h1 class="page-title">🤖 智能文檔問答助理</h1>
            <p class="page-subtitle">
                基於 Graph RAG 的多模態知識問答系統 • 支援文檔、圖片 OCR 與知識圖譜
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    def render_navigation(self):
        """渲染主導航選單"""
        with st.sidebar:
            selected = option_menu(
                menu_title="主選單",
                options=["🏠 首頁", "📚 我的知識庫", "🍵 演示模式", "📊 知識圖譜", "⚙️ 設定"],
                icons=["house", "book", "cup-hot", "diagram-3", "gear"],
                menu_icon="list",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#ffffff"},
                    "icon": {"color": "#667eea", "font-size": "18px"}, 
                    "nav-link": {
                        "font-size": "16px", 
                        "text-align": "left", 
                        "margin": "0px",
                        "padding": "0.5rem 1rem",
                        "border-radius": "0.5rem",
                        "margin-bottom": "0.25rem"
                    },
                    "nav-link-selected": {
                        "background-color": "#667eea",
                        "color": "white"
                    },
                }
            )
            return selected
            
    def render_sidebar_info(self):
        """渲染側邊欄資訊"""
        with st.sidebar:
            st.markdown("---")
            
            # API 狀態
            self._render_api_status()
            
            st.markdown("---")
            
            # 系統資訊
            self._render_system_info()
            
    def _render_api_status(self):
        """渲染API狀態"""
        st.markdown("### 🔐 API 狀態")
        
        from config import GROQ_API_KEY, GEMINI_API_KEY
        
        if GROQ_API_KEY:
            st.success("✅ Groq API 已設定")
        else:
            st.error("❌ 請設定 GROQ_API_KEY")
        
        if GEMINI_API_KEY:
            st.success("✅ Gemini API 已設定")
        else:
            st.warning("⚠️ Gemini API 未設定（OCR功能不可用）")
            
    def _render_system_info(self):
        """渲染系統資訊"""
        st.markdown("### 📋 系統資訊")
        
        info_data = {
            "🔧 LlamaIndex": "0.10.25+",
            "🤖 LLM": "Groq LLama 3.3",
            "📊 向量DB": "ChromaDB",
            "🕸️ 圖資料庫": "NetworkX",
            "🎨 前端": "Streamlit"
        }
        
        for key, value in info_data.items():
            st.markdown(f"**{key}**: {value}")
            
    def create_columns(self, ratios):
        """創建響應式列佈局"""
        return st.columns(ratios)
        
    def create_tabs(self, tab_names):
        """創建標籤頁"""
        return st.tabs(tab_names)
        
    def show_success(self, message):
        """顯示成功訊息"""
        st.success(f"✅ {message}")
        
    def show_error(self, message):
        """顯示錯誤訊息"""
        st.error(f"❌ {message}")
        
    def show_warning(self, message):
        """顯示警告訊息"""
        st.warning(f"⚠️ {message}")
        
    def show_info(self, message):
        """顯示資訊訊息"""
        st.info(f"ℹ️ {message}")
