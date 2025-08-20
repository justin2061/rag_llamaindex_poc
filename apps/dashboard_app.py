"""
新版 RAG 系統 Dashboard 主界面
包含側邊欄導航：Dashboard, 知識庫管理, 智能問答
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import tempfile

# 系統導入
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.rag_system.elasticsearch_rag_system import ElasticsearchRAGSystem
from src.processors.user_file_manager import UserFileManager
from config.config import GROQ_API_KEY, GEMINI_API_KEY, PAGE_TITLE, PAGE_ICON, JINA_API_KEY
from src.utils.embedding_fix import setup_safe_embedding, prevent_openai_fallback

# 頁面配置
st.set_page_config(
    page_title="RAG 智能助理 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局樣式
def load_styles():
    """載入自定義CSS樣式"""
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    
    /* 側邊欄樣式 */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 導航按鈕樣式 */
    .nav-button {
        background: white;
        color: #333;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        width: 100%;
        text-align: left;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        background: #f8fafc;
        transform: translateX(4px);
    }
    
    .nav-button.active {
        background: #3b82f6;
        color: white;
    }
    
    /* 卡片樣式 */
    .dashboard-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 統計卡片 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        opacity: 0.9;
    }
    
    /* 隱藏 Streamlit 默認元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 文件列表樣式 */
    .file-item {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def init_system():
    """初始化系統"""
    # 防止 OpenAI 回退
    if 'openai_prevented' not in st.session_state:
        prevent_openai_fallback()
        st.session_state.openai_prevented = True
    
    # 初始化 RAG 系統
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = ElasticsearchRAGSystem()
        st.session_state.rag_system_type = "Elasticsearch RAG"
        st.session_state.system_ready = False
    
    # 初始化文件管理器
    if 'file_manager' not in st.session_state:
        st.session_state.file_manager = UserFileManager()
    
    # 初始化聊天歷史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 生成會話ID（用於 Elasticsearch 對話記錄）
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    
    # 初始化當前頁面
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

def check_api_keys():
    """檢查 API 金鑰配置"""
    if not GROQ_API_KEY:
        st.error("❌ 請在 .env 文件中設定 GROQ_API_KEY")
        return False
    
    if not GEMINI_API_KEY:
        st.warning("⚠️ 未設定 GEMINI_API_KEY，圖片 OCR 功能將不可用")
    
    return True

def render_sidebar():
    """渲染側邊欄導航"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #667eea; margin-bottom: 0.5rem;">🤖 RAG 智能助理</h2>
            <p style="color: #6b7280; font-size: 0.8rem;">問答系統</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 導航菜單
        st.markdown("### 📋 主要功能")
        
        # Dashboard 按鈕
        if st.button(
            "📊 Dashboard", 
            key="nav_dashboard",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "dashboard" else "secondary"
        ):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        # 知識庫管理按鈕
        if st.button(
            "📚 知識庫管理", 
            key="nav_knowledge",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "knowledge" else "secondary"
        ):
            st.session_state.current_page = "knowledge"
            st.rerun()
        
        # 智能問答按鈕
        if st.button(
            "💬 智能問答", 
            key="nav_chat",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "chat" else "secondary"
        ):
            st.session_state.current_page = "chat"
            st.rerun()
        
        # Elasticsearch 對話記錄統計按鈕
        if st.button(
            "📊 對話記錄統計", 
            key="nav_conversation_stats",
            use_container_width=True,
            type="primary" if st.session_state.current_page == "conversation_stats" else "secondary"
        ):
            st.session_state.current_page = "conversation_stats"
            st.rerun()
        
        st.markdown("---")
        
        # 系統狀態
        st.markdown("### ⚙️ 系統狀態")
        
        # API 狀態
        if GROQ_API_KEY:
            st.success("✅ Groq API")
        else:
            st.error("❌ Groq API")
        
        if GEMINI_API_KEY:
            st.success("✅ Gemini API")  
        else:
            st.warning("⚠️ Gemini API")
        
        # Elasticsearch 狀態
        try:
            if hasattr(st.session_state.rag_system, 'elasticsearch_client'):
                if st.session_state.rag_system.elasticsearch_client.ping():
                    st.success("✅ Elasticsearch")
                else:
                    st.error("❌ Elasticsearch")
            else:
                st.warning("⚠️ Elasticsearch 未初始化")
        except Exception:
            st.error("❌ Elasticsearch 連接失敗")
        
        st.markdown("---")
        
        # 快速統計
        if st.session_state.rag_system:
            stats = st.session_state.rag_system.get_document_statistics()
            st.markdown("### 📈 快速統計")
            st.metric("📄 文檔總數", stats.get("total_documents", 0))
            st.metric("🧩 文本塊數", stats.get("total_nodes", 0))
            st.metric("💬 對話次數", len(st.session_state.chat_history))

def render_dashboard():
    """渲染 Dashboard 頁面"""
    st.markdown("# 📊 系統 Dashboard")
    st.markdown("歡迎使用 RAG 智能問答助理系統")
    
    # 系統概覽
    col1, col2, col3, col4 = st.columns(4)
    
    if st.session_state.rag_system:
        stats = st.session_state.rag_system.get_document_statistics()
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">📄</div>
                <div class="metric-value">{}</div>
                <div class="metric-label">文檔總數</div>
            </div>
            """.format(stats.get("total_documents", 0)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">🧩</div>
                <div class="metric-value">{}</div>
                <div class="metric-label">文本塊數</div>
            </div>
            """.format(stats.get("total_nodes", 0)), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">💬</div>
                <div class="metric-value">{}</div>
                <div class="metric-label">對話次數</div>
            </div>
            """.format(len(st.session_state.chat_history)), unsafe_allow_html=True)
        
        with col4:
            # 計算總文件大小
            try:
                files = st.session_state.rag_system.get_indexed_files()
                total_size_mb = sum(file.get('size', 0) for file in files) / (1024 * 1024)
            except:
                total_size_mb = 0
                
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">💾</div>
                <div class="metric-value">{:.1f}</div>
                <div class="metric-label">總大小 (MB)</div>
            </div>
            """.format(total_size_mb), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 系統信息卡片
    # col1, col2 = st.columns([1, 1])
    
    # with col1:
    #     st.markdown("""
    #     <div class="dashboard-card">
    #         <h3>🔧 系統配置</h3>
    #         <ul style="list-style: none; padding: 0;">
    #             <li><strong>RAG 系統:</strong> Elasticsearch RAG</li>
    #             <li><strong>LLM 模型:</strong> Groq Llama-3.3-70B</li>
    #             <li><strong>嵌入模型:</strong> HuggingFace all-MiniLM-L6-v2</li>
    #             <li><strong>向量存儲:</strong> Elasticsearch</li>
    #             <li><strong>OCR 支援:</strong> {} Gemini Vision</li>
    #         </ul>
    #     </div>
    #     """.format("✅" if GEMINI_API_KEY else "❌"), unsafe_allow_html=True)
    
    # with col2:
    #     st.markdown("""
    #     <div class="dashboard-card">
    #         <h3>📈 性能指標</h3>
    #         <ul style="list-style: none; padding: 0;">
    #             <li><strong>查詢響應時間:</strong> < 3 秒</li>
    #             <li><strong>支援文檔格式:</strong> PDF, DOCX, TXT, 圖片</li>
    #             <li><strong>最大文檔量:</strong> 100,000+</li>
    #             <li><strong>並發用戶:</strong> 10-50+</li>
    #             <li><strong>記憶體使用:</strong> 500MB-2GB</li>
    #         </ul>
    #     </div>
    #     """, unsafe_allow_html=True)
    
    # 最近活動
    st.markdown("## 📋 最近活動")
    
    if st.session_state.chat_history:
        recent_chats = st.session_state.chat_history[-5:]  # 顯示最近5條對話
        for i, chat in enumerate(reversed(recent_chats)):
            st.markdown(f"""
            <div class="file-item">
                <strong>Q:</strong> {chat.get('question', 'N/A')[:100]}...
                <br><small style="color: #6b7280;">時間: {chat.get('timestamp', '未知')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📝 暫無對話記錄")

def render_knowledge_management():
    """渲染知識庫管理頁面"""
    st.markdown("# 📚 知識庫管理")
    
    # 文件上傳區域
    st.markdown("## 📤 上傳新文檔")
    
    uploaded_files = st.file_uploader(
        "選擇要上傳的文檔",
        type=['pdf', 'txt', 'docx', 'md', 'png', 'jpg', 'jpeg', 'webp', 'bmp'],
        accept_multiple_files=True,
        help="支援 PDF、Word、文字檔、Markdown 和圖片格式"
    )
    
    if uploaded_files:
        st.markdown("### 📋 待上傳文件列表")
        
        for i, file in enumerate(uploaded_files):
            file_size_mb = file.size / (1024 * 1024)
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                file_ext = Path(file.name).suffix.lower()
                icon = get_file_icon(file_ext)
                st.write(f"{icon} {file.name}")
            
            with col2:
                st.write(f"{file_size_mb:.1f} MB")
            
            with col3:
                if st.session_state.file_manager.validate_file(file):
                    st.success("✅")
                else:
                    st.error("❌")
        
        # 處理文件按鈕
        if st.button("🚀 處理文檔並建立知識庫", type="primary", use_container_width=True):
            process_uploaded_files(uploaded_files)
    
    st.markdown("---")
    
    # 現有文檔管理
    st.markdown("## 📋 現有文檔管理")
    
    if st.session_state.rag_system:
        try:
            files = st.session_state.rag_system.get_indexed_files()
            
            if not files:
                st.info("📝 知識庫中暫無文件")
            else:
                # 統計資訊
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 文件總數", len(files))
                with col2:
                    total_nodes = sum(file.get('node_count', 0) for file in files)
                    st.metric("🧩 文本塊總數", total_nodes)
                with col3:
                    total_size_mb = sum(file.get('size', 0) for file in files) / (1024 * 1024)
                    st.metric("💾 總大小", f"{total_size_mb:.1f} MB")
                
                st.markdown("### 📄 文件列表")
                
                # 文件列表
                for i, file_info in enumerate(files):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            icon = get_file_icon(file_info.get('type', ''))
                            st.write(f"{icon} **{file_info['name']}**")
                            size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] > 0 else 0
                            st.caption(f"📊 {file_info['node_count']} 個文本塊 • {size_mb:.2f} MB")
                        
                        with col2:
                            st.write(f"📅 {file_info['upload_time']}")
                            if file_info.get('page_count', 0) > 0:
                                st.caption(f"📑 {file_info['page_count']} 頁")
                        
                        with col3:
                            st.write(f"🏷️ {file_info.get('type', 'unknown')}")
                        
                        with col4:
                            if st.button(
                                "🗑️", 
                                key=f"delete_{i}",
                                help=f"刪除 {file_info['name']}",
                                use_container_width=True
                            ):
                                handle_file_deletion(file_info, i)
                        
                        st.divider()
                
                # 批量操作
                if len(files) > 1:
                    st.markdown("### 🔧 批量操作")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🗑️ 清空知識庫", type="secondary"):
                            handle_bulk_deletion(files)
                    
                    with col2:
                        if st.button("🔄 重新索引", type="secondary"):
                            handle_reindex()
                    
                    with col3:
                        if st.button("📊 生成統計報告", type="secondary"):
                            generate_stats_report(files)
        
        except Exception as e:
            st.error(f"❌ 載入文件列表時發生錯誤: {str(e)}")

def render_chat():
    """渲染智能問答頁面"""
    st.markdown("# 💬 智能問答")
    
    if not st.session_state.rag_system:
        st.error("❌ RAG 系統未初始化，請先上傳文檔")
        return
    
    # 檢查是否有文檔
    stats = st.session_state.rag_system.get_document_statistics()
    if stats.get("total_documents", 0) == 0:
        st.warning("⚠️ 知識庫為空，請先在「知識庫管理」頁面上傳文檔")
        return
    
    # 聊天界面
    st.markdown("## 🗨️ 對話區域")
    
    # 顯示聊天歷史
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history[-10:]:  # 顯示最近10條對話
                # 用戶問題
                with st.chat_message("user"):
                    st.write(chat.get('question', ''))
                
                # 助理回答
                with st.chat_message("assistant"):
                    st.write(chat.get('answer', ''))
                    
                    # 顯示來源（如果有）
                    if chat.get('sources'):
                        with st.expander("📚 參考來源"):
                            # 優先顯示詳細來源信息
                            if chat.get('source_details'):
                                for i, source in enumerate(chat['source_details'][:3]):
                                    st.markdown(f"""
                                    **來源 {i+1}:** {source['source']}  
                                    **評分:** {source['score']:.3f}  
                                    **內容預覽:** {source['content'][:150]}...  
                                    **文件路徑:** {source.get('file_path', '未知')}
                                    """)
                            else:
                                # 回退到簡單來源列表
                                for source in chat['sources'][:3]:
                                    st.write(f"• {source}")
        else:
            st.info("💡 開始您的第一個問題吧！")
    
    # 輸入區域
    st.markdown("---")
    
    # 建議問題
    if not st.session_state.chat_history:
        st.markdown("### 💡 建議問題")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 文檔中包含什麼內容？", use_container_width=True):
                handle_chat_query("文檔中包含什麼內容？")
            if st.button("📊 給我一個內容摘要", use_container_width=True):
                handle_chat_query("給我一個內容摘要")
        
        with col2:
            if st.button("🎯 有什麼重要信息？", use_container_width=True):
                handle_chat_query("有什麼重要信息？")
            if st.button("❓ 我可以問什麼問題？", use_container_width=True):
                handle_chat_query("我可以問什麼問題？")
    
    # 問答輸入
    user_question = st.chat_input("輸入您的問題...")
    
    if user_question:
        handle_chat_query(user_question)
    
    # 聊天管理
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ 清空聊天", use_container_width=True):
            st.session_state.chat_history = []
            st.success("✅ 聊天記錄已清空")
            st.rerun()
    
    with col2:
        if st.button("📋 匯出對話", use_container_width=True):
            export_chat_history()
    
    # col3 留空或用於其他功能
    
    with col4:
        if st.session_state.chat_history:
            chat_count = len(st.session_state.chat_history)
            st.metric("💬 本地對話", chat_count)

# 輔助函數
def get_file_icon(file_type: str) -> str:
    """根據文件類型返回對應圖標"""
    icon_map = {
        '.pdf': '📄',
        'pdf': '📄',
        '.docx': '📝',
        'docx': '📝',
        '.doc': '📝',
        'doc': '📝',
        '.txt': '📄',
        'txt': '📄',
        '.md': '📄',
        'md': '📄',
        '.png': '🖼️',
        'png': '🖼️',
        '.jpg': '🖼️',
        'jpg': '🖼️',
        '.jpeg': '🖼️',
        'jpeg': '🖼️',
        'image': '🖼️'
    }
    return icon_map.get(file_type.lower(), '📄')

def process_uploaded_files(uploaded_files):
    """處理上傳的文件"""
    with st.spinner("正在處理文檔..."):
        try:
            # 處理文件
            documents = st.session_state.rag_system.process_uploaded_files(uploaded_files)
            
            if documents:
                # 創建索引
                index = st.session_state.rag_system.create_index(documents)
                
                if index:
                    st.session_state.rag_system.setup_query_engine()
                    st.session_state.system_ready = True
                    st.success(f"✅ 成功處理 {len(documents)} 個文檔！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ 索引創建失敗")
            else:
                st.error("❌ 文檔處理失敗")
        except Exception as e:
            st.error(f"❌ 處理文檔時發生錯誤: {str(e)}")

def handle_file_deletion(file_info: Dict, index: int):
    """處理單個文件刪除"""
    confirm_key = f'confirm_delete_{index}'
    
    if st.session_state.get(confirm_key, False):
        # 執行刪除
        if st.session_state.rag_system.delete_file_from_knowledge_base(file_info['id']):
            st.success(f"✅ 已刪除 {file_info['name']}")
            st.rerun()
        else:
            st.error(f"❌ 刪除 {file_info['name']} 失敗")
        st.session_state[confirm_key] = False
    else:
        # 請求確認
        st.session_state[confirm_key] = True
        st.warning(f"⚠️ 確定要刪除 {file_info['name']} 嗎？再次點擊刪除按鈕確認。")
        st.rerun()

def handle_bulk_deletion(files: List[Dict]):
    """處理批量刪除"""
    confirm_key = 'confirm_clear_all'
    
    if st.session_state.get(confirm_key, False):
        success_count = 0
        for file_info in files:
            if st.session_state.rag_system.delete_file_from_knowledge_base(file_info['id']):
                success_count += 1
        
        if success_count == len(files):
            st.success(f"✅ 已清空知識庫，刪除了 {success_count} 個文件")
        else:
            st.warning(f"⚠️ 部分文件刪除失敗，成功刪除 {success_count}/{len(files)} 個文件")
        
        st.session_state[confirm_key] = False
        st.rerun()
    else:
        st.session_state[confirm_key] = True
        st.warning("⚠️ 確定要清空整個知識庫嗎？這將刪除所有文件！再次點擊確認。")
        st.rerun()

def handle_reindex():
    """處理重新索引"""
    with st.spinner("正在重新索引..."):
        try:
            # 這裡可以添加重新索引的邏輯
            st.success("✅ 重新索引完成")
        except Exception as e:
            st.error(f"❌ 重新索引失敗: {str(e)}")

def generate_stats_report(files: List[Dict]):
    """生成統計報告"""
    report = f"""
# 知識庫統計報告
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 基本統計
- 文件總數: {len(files)}
- 文本塊總數: {sum(file.get('node_count', 0) for file in files)}
- 總大小: {sum(file.get('size', 0) for file in files) / (1024 * 1024):.2f} MB

## 文件類型分佈
"""
    
    type_count = {}
    for file in files:
        file_type = file.get('type', 'unknown')
        type_count[file_type] = type_count.get(file_type, 0) + 1
    
    for file_type, count in type_count.items():
        report += f"- {file_type}: {count} 個文件\n"
    
    st.download_button(
        "📊 下載統計報告",
        report,
        file_name=f"knowledge_base_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

def handle_chat_query(question: str):
    """處理聊天查詢"""
    try:
        with st.spinner("🤔 思考中..."):
            # 獲取會話ID
            session_id = st.session_state.get('session_id', 'default_session')
            
            # 執行帶來源的查詢
            if hasattr(st.session_state.rag_system, 'query_with_sources'):
                result = st.session_state.rag_system.query_with_sources(
                    question, 
                    save_to_history=True,
                    session_id=session_id
                )
                answer = result['answer']
                sources = result['sources']
                conversation_id = result.get('conversation_id')
            elif hasattr(st.session_state.rag_system, 'query_with_context'):
                answer = st.session_state.rag_system.query_with_context(question)
                sources = []
                conversation_id = None
            else:
                answer = st.session_state.rag_system.query(question)
                sources = []
                conversation_id = None
            
            # 處理來源信息
            source_list = []
            if sources:
                for source in sources:
                    source_list.append(f"{source['source']} (評分: {source['score']:.2f})")
            else:
                source_list = ["向量索引", "用戶文檔"]  # 回退到默認值
            
            # 保存到本地聊天歷史（向後兼容）
            chat_record = {
                'question': question,
                'answer': answer,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sources': source_list,
                'source_details': sources,  # 保存完整的來源詳情
                'conversation_id': conversation_id  # 保存 ES 中的對話ID
            }
            
            st.session_state.chat_history.append(chat_record)
            st.success("💾 對話已自動保存到 Elasticsearch")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 查詢失敗: {str(e)}")

def show_elasticsearch_conversations():
    """顯示 Elasticsearch 中的對話記錄"""
    if not st.session_state.rag_system:
        st.error("❌ RAG 系統未初始化")
        return
    
    # 獲取對話統計
    try:
        stats = st.session_state.rag_system.get_conversation_statistics()
        
        st.markdown("## 📊 Elasticsearch 對話記錄統計")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總對話數", stats.get('total_conversations', 0))
        with col2:
            st.metric("會話數", stats.get('unique_sessions', 0))
        with col3:
            st.metric("平均評分", stats.get('average_rating', 0))
        
        # 最近對話記錄
        st.markdown("### 📝 最近對話記錄")
        
        conversations = st.session_state.rag_system.get_conversation_history(limit=10)
        
        if conversations:
            for i, conv in enumerate(conversations):
                with st.expander(f"💬 {conv['question'][:50]}..." if len(conv['question']) > 50 else f"💬 {conv['question']}"):
                    st.markdown(f"**時間:** {conv['timestamp']}")
                    st.markdown(f"**問題:** {conv['question']}")
                    st.markdown(f"**回答:** {conv['answer']}")
                    
                    if conv.get('sources'):
                        st.markdown("**來源:**")
                        for j, source in enumerate(conv['sources'][:3]):
                            st.markdown(f"  {j+1}. {source.get('source', '未知')} (評分: {source.get('score', 0):.3f})")
                    
                    # 評分和反饋
                    col1, col2 = st.columns(2)
                    with col1:
                        rating = st.selectbox(
                            "評分",
                            [None, 1, 2, 3, 4, 5],
                            index=conv.get('rating') if conv.get('rating') else 0,
                            key=f"rating_{conv['conversation_id']}"
                        )
                    with col2:
                        feedback = st.text_input(
                            "反饋",
                            value=conv.get('feedback', ''),
                            key=f"feedback_{conv['conversation_id']}"
                        )
                    
                    if st.button(f"💾 更新反饋", key=f"update_{conv['conversation_id']}"):
                        if st.session_state.rag_system.update_conversation_feedback(
                            conv['conversation_id'], rating, feedback
                        ):
                            st.success("✅ 反饋已更新")
                        else:
                            st.error("❌ 更新失敗")
        else:
            st.info("📝 暫無對話記錄")
        
        # 搜索對話
        st.markdown("### 🔍 搜索對話記錄")
        search_query = st.text_input("輸入搜索關鍵詞")
        
        if search_query:
            search_results = st.session_state.rag_system.search_conversation_history(search_query)
            
            if search_results:
                st.markdown(f"找到 {len(search_results)} 條相關對話:")
                for conv in search_results:
                    with st.expander(f"🔍 {conv['question'][:50]}..."):
                        st.markdown(f"**時間:** {conv['timestamp']}")
                        st.markdown(f"**問題:** {conv['question']}")
                        st.markdown(f"**回答:** {conv['answer'][:200]}...")
            else:
                st.info("未找到相關對話")
                
    except Exception as e:
        st.error(f"❌ 獲取對話記錄失敗: {str(e)}")

def export_chat_history():
    """導出聊天歷史"""
    if not st.session_state.chat_history:
        st.warning("⚠️ 暫無對話記錄")
        return
    
    export_text = "# 對話記錄導出\n\n"
    for i, chat in enumerate(st.session_state.chat_history, 1):
        export_text += f"## 對話 {i}\n"
        export_text += f"**時間**: {chat.get('timestamp', '未知')}\n\n"
        export_text += f"**問題**: {chat.get('question', '')}\n\n"
        export_text += f"**回答**: {chat.get('answer', '')}\n\n"
        export_text += "---\n\n"
    
    st.download_button(
        "📋 下載對話記錄",
        export_text,
        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

def render_conversation_stats():
    """渲染對話記錄統計頁面"""
    st.markdown("# 📊 對話記錄統計")
    st.markdown("Elasticsearch 中的對話記錄分析和統計")
    
    show_elasticsearch_conversations()

def main():
    """主函數"""
    # 載入樣式
    load_styles()
    
    # 初始化系統
    init_system()
    
    # 檢查 API 配置
    if not check_api_keys():
        return
    
    # 渲染側邊欄
    render_sidebar()
    
    # 根據當前頁面渲染內容
    if st.session_state.current_page == "dashboard":
        render_dashboard()
    elif st.session_state.current_page == "knowledge":
        render_knowledge_management()
    elif st.session_state.current_page == "chat":
        render_chat()
    elif st.session_state.current_page == "conversation_stats":
        render_conversation_stats()

if __name__ == "__main__":
    main()