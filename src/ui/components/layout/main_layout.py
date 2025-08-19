import streamlit as st
try:
    from streamlit_option_menu import option_menu
    HAS_OPTION_MENU = True
except ImportError:
    HAS_OPTION_MENU = False

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
        """載入基本樣式（保持 Streamlit 原始外觀）"""
        st.markdown("""
        <style>
        /* 僅保留基本的隱藏元素樣式 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* 簡單的卡片樣式，不改變顏色 */
        .custom-card {
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 0.5rem;
            border: 1px solid #e0e0e0;
        }
        </style>
        """, unsafe_allow_html=True)
        
    def render_header(self):
        """渲染頁面標題"""
        st.markdown("""
        <div class="custom-card">
            <h1 style="text-align: center; color: #262730;">🤖 智能文檔問答助理</h1>
            <p style="text-align: center; color: #666; margin-bottom: 0;">
                基於 Graph RAG 的多模態知識問答系統 • 支援文檔、圖片 OCR 與知識圖譜
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    def render_navigation(self):
        """渲染主導航選單"""
        with st.sidebar:
            if HAS_OPTION_MENU:
                # 使用 streamlit-option-menu（如果可用）
                selected = option_menu(
                    menu_title="主選單",
                    options=["🏠 首頁", "📚 我的知識庫", "🍵 演示模式", "📊 知識圖譜", "⚙️ 設定"],
                    icons=["house", "book", "cup-hot", "diagram-3", "gear"],
                    menu_icon="list",
                    default_index=0,
                    styles={
                        "container": {"padding": "0!important", "background-color": "transparent"},
                        "icon": {"color": "#ff6347", "font-size": "18px"}, 
                        "nav-link": {
                            "font-size": "16px", 
                            "text-align": "left", 
                            "margin": "0px",
                            "padding": "0.5rem 1rem",
                            "border-radius": "0.5rem",
                            "margin-bottom": "0.25rem"
                        },
                        "nav-link-selected": {
                            "background-color": "#ff6347",
                            "color": "white"
                        },
                    }
                )
            else:
                # 回退到內建選擇器
                st.markdown("### 📋 主選單")
                selected = st.radio(
                    "選擇頁面",
                    options=["🏠 首頁", "📚 我的知識庫", "🍵 演示模式", "📊 知識圖譜", "⚙️ 設定"],
                    index=0,
                    label_visibility="collapsed"
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
            "📊 向量DB": "Elasticsearch + SimpleVectorStore",
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
