"""
RAG 系統 Dashboard V2.0 - API串接版本
使用Enhanced RAG API V2.0的Streamlit應用
"""

import streamlit as st
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import time

# 系統導入
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.api_clients.enhanced_api_client import EnhancedAPIClient
from config.config import PAGE_TITLE, PAGE_ICON

# 配置logging
logger = logging.getLogger(__name__)

# 頁面配置
st.set_page_config(
    page_title="RAG 智能助理 Dashboard V2.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API配置 - 容器間通信使用服務名稱
API_BASE_URL = os.getenv("API_BASE_URL", "http://rag-enhanced-api:8000")
API_KEY = os.getenv("STREAMLIT_API_KEY", "demo-api-key-123")

def load_styles():
    """載入自定義CSS樣式"""
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    
    /* V2.0 特色樣式 */
    .v2-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .api-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .api-status.healthy {
        background: #10b981;
        color: white;
    }
    
    .api-status.unhealthy {
        background: #ef4444;
        color: white;
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
    
    /* 性能指標卡片 */
    .performance-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border-radius: 1rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .optimization-badge {
        background: #3b82f6;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.5rem;
        font-size: 0.7rem;
        margin: 0.1rem;
        display: inline-block;
    }
    
    /* 聊天消息樣式 */
    .chat-message {
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    .user-message {
        background: #eff6ff;
        border-left-color: #3b82f6;
    }
    
    .assistant-message {
        background: #f0fdf4;
        border-left-color: #10b981;
    }
    
    /* 文件上傳區域 */
    .upload-zone {
        border: 2px dashed #cbd5e1;
        border-radius: 1rem;
        padding: 2rem;
        text-align: center;
        background: #f8fafc;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    
    /* 隱藏 Streamlit 默認元素 */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stApp > header {background-color: transparent;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_api_client():
    """獲取API客戶端實例（使用快取）"""
    return EnhancedAPIClient(base_url=API_BASE_URL, api_key=API_KEY)

def initialize_session_state():
    """初始化session state"""
    
    # V2.0 新增狀態
    if 'api_client' not in st.session_state:
        st.session_state.api_client = get_api_client()
    
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "checking"
    
    if 'system_info' not in st.session_state:
        st.session_state.system_info = {}
    
    # 保留原有狀態
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit_{int(time.time())}"
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "streamlit_user"
    
    if 'conversation_context' not in st.session_state:
        st.session_state.conversation_context = None

def check_api_status():
    """檢查API狀態"""
    try:
        health_info = st.session_state.api_client.health_check()
        if health_info.get("status") == "healthy":
            st.session_state.api_status = "healthy"
            st.session_state.system_info = health_info
        else:
            st.session_state.api_status = "unhealthy"
    except Exception as e:
        st.session_state.api_status = "unhealthy"
        st.session_state.system_info = {"error": str(e)}

def render_header():
    """渲染頁面頭部"""
    # V2.0 Banner
    status_class = "healthy" if st.session_state.api_status == "healthy" else "unhealthy"
    status_text = "✅ API連線正常" if st.session_state.api_status == "healthy" else "❌ API連線異常"
    
    st.markdown(f"""
    <div class="v2-banner">
        <h1>🚀 RAG 智能助理 Dashboard V2.0</h1>
        <p>Enhanced RAG API 串接版本</p>
        <span class="api-status {status_class}">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 系統信息
    if st.session_state.api_status == "healthy" and st.session_state.system_info:
        info = st.session_state.system_info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("API版本", info.get("api_version", "N/A"))
        with col2:
            st.metric("總文檔", info.get("total_documents", 0))
        with col3:
            st.metric("對話數", info.get("total_conversations", 0))
        with col4:
            es_status = "✅" if info.get("elasticsearch_connected") else "❌"
            st.metric("ES狀態", es_status)

def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.markdown("# 🧭 導航")
        
        # API狀態檢查按鈕
        if st.button("🔄 檢查API狀態", use_container_width=True):
            with st.spinner("檢查API狀態中..."):
                check_api_status()
            if st.session_state.api_status == "healthy":
                st.success("✅ API狀態檢查完成")
            else:
                st.error("❌ API連接檢查失敗")
            st.rerun()
        
        # 導航選項
        pages = {
            "📊 Dashboard": "Dashboard",
            "💬 智能問答": "Chat",  
            "📚 知識庫管理": "Knowledge",
            "📈 API監控": "Monitoring"
        }
        
        for label, page_key in pages.items():
            if st.button(label, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # API信息
        st.markdown("### 🔗 API信息")
        st.text(f"Base URL: {API_BASE_URL}")
        
        if st.session_state.api_status == "healthy":
            st.success("✅ API連線正常")
        else:
            st.error("❌ API連線異常")
        
        # V2.0 功能說明
        st.markdown("---")
        st.markdown("### 🚀 V2.0 新功能")
        st.markdown("""
        - **混合檢索**: 向量+關鍵字+語義
        - **智能重排序**: 上下文感知
        - **多模型策略**: 512維向量
        - **階層索引**: 多粒度切割
        - **性能監控**: 詳細指標
        """)

def render_dashboard():
    """渲染Dashboard頁面"""
    st.markdown("# 📊 系統監控面板")
    
    if st.session_state.api_status != "healthy":
        st.error("⚠️ API服務不可用，請檢查連接")
        return
    
    # 獲取知識庫狀態
    kb_status = get_knowledge_base_status_with_feedback()
    
    if "error" not in kb_status:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="📄 知識庫文件", 
                value=kb_status.get("total_files", 0)
            )
        
        with col2:
            st.metric(
                label="🧩 文本塊數量", 
                value=kb_status.get("total_chunks", 0)
            )
        
        with col3:
            st.metric(
                label="💾 存儲大小", 
                value=f"{kb_status.get('total_size_mb', 0):.2f} MB"
            )
    
    # 獲取對話統計
    conv_stats = st.session_state.api_client.get_conversation_stats()
    
    if "error" not in conv_stats:
        st.markdown("## 📈 對話統計")
        
        # 格式化顯示統計數據
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="💬 總對話數",
                value=conv_stats.get("total_conversations", 0)
            )
        
        with col2:
            st.metric(
                label="🔗 唯一會話",
                value=conv_stats.get("unique_sessions", 0)
            )
        
        with col3:
            # 計算今日對話數（從 conversations_by_date 數據中）
            today_convs = 0
            conversations_by_date = conv_stats.get("conversations_by_date", [])
            if conversations_by_date:
                # 取最近的日期數據
                today_convs = conversations_by_date[0].get("doc_count", 0)
            
            st.metric(
                label="📊 最近對話",
                value=today_convs
            )
        
        # 詳細統計信息
        with st.expander("🔍 詳細統計信息"):
            st.json(conv_stats)
    else:
        st.error(f"❌ 獲取對話統計失敗: {conv_stats['error']}")
    
    # 最近對話
    st.markdown("## 💬 最近對話")
    
    try:
        recent_conversations = st.session_state.api_client.get_conversations(page_size=5)
        
        if "error" not in recent_conversations:
            conversations = recent_conversations.get("conversations", [])
            
            if conversations:
                for i, conv in enumerate(conversations):
                    # 安全處理時間戳
                    timestamp = conv.get('created_at', conv.get('timestamp', 'N/A'))
                    if timestamp != 'N/A' and len(timestamp) > 19:
                        timestamp = timestamp[:19]
                    
                    with st.expander(f"對話 {i+1} - {timestamp}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**👤 用戶ID:**")
                            st.text(conv.get('user_id', 'N/A'))
                            
                            st.markdown("**📅 創建時間:**")
                            st.text(conv.get('created_at', conv.get('timestamp', 'N/A')))
                        
                        with col2:
                            st.markdown("**🆔 對話ID:**")
                            st.text(conv.get('conversation_id', 'N/A'))
                            
                            st.markdown("**💬 消息數:**")
                            messages = conv.get('messages', [])
                            st.text(f"{len(messages)} 條消息")
                        
                        # 顯示最後幾條消息
                        if messages:
                            st.markdown("**📝 最近消息:**")
                            for msg_idx, message in enumerate(messages[-2:]):  # 只顯示最後2條
                                msg_type = "🙋 用戶" if message.get('role') == 'user' else "🤖 助理"
                                content = message.get('content', '').strip()
                                if len(content) > 100:
                                    content = content[:100] + "..."
                                st.markdown(f"**{msg_type}:** {content}")
                        
                        # 完整數據（可選查看）
                        with st.expander("🔍 完整數據"):
                            st.json(conv)
            else:
                st.info("📝 暫無對話記錄")
                
                # 提供一些可能的原因說明
                st.markdown("**可能的原因:**")
                st.markdown("- 尚未有用戶進行對話")
                st.markdown("- API服務剛啟動，對話記錄為空")
                st.markdown("- 資料庫連接問題")
        else:
            # API 返回錯誤
            st.warning("⚠️ 獲取對話記錄時發生問題")
            st.error(f"錯誤詳情: {recent_conversations['error']}")
            
            # 顯示統計數據作為替代信息
            if conv_stats and "error" not in conv_stats:
                st.info("📊 根據統計數據顯示:")
                st.metric("總對話數", conv_stats.get("total_conversations", 0))
                
                # 顯示按日期分佈的對話
                conversations_by_date = conv_stats.get("conversations_by_date", [])
                if conversations_by_date:
                    st.markdown("**📅 最近對話分佈:**")
                    for date_data in conversations_by_date[:5]:
                        date_str = date_data.get("key_as_string", "")[:10]  # 只取日期部分
                        count = date_data.get("doc_count", 0)
                        st.markdown(f"- {date_str}: {count} 條對話")
                
    except Exception as e:
        st.error(f"❌ 獲取對話記錄時發生未預期錯誤: {str(e)}")
        
        # 顯示統計數據作為替代
        if conv_stats and "error" not in conv_stats:
            st.info("📊 顯示可用的統計數據:")
            st.metric("總對話數", conv_stats.get("total_conversations", 0))
            st.metric("唯一會話數", conv_stats.get("unique_sessions", 0))

def render_chat():
    """渲染智能問答頁面"""
    st.markdown("# 💬 智能問答 V2.0")
    
    if st.session_state.api_status != "healthy":
        st.error("⚠️ API服務不可用，請檢查連接")
        return
    
    # 顯示聊天歷史
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(st.session_state.chat_history[-10:]):
                # 用戶問題
                with st.chat_message("user"):
                    st.write(chat.get('question', ''))
                
                # 助理回答
                with st.chat_message("assistant"):
                    st.write(chat.get('answer', ''))
                    
                    # V2.0 增強信息顯示
                    metadata = chat.get('metadata', {})
                    
                    # 優化功能使用
                    optimization_used = metadata.get('optimization_used', [])
                    if optimization_used:
                        st.markdown("**🎯 使用的優化功能:**")
                        for opt in optimization_used:
                            st.markdown(f'<span class="optimization-badge">{opt}</span>', 
                                      unsafe_allow_html=True)
                    
                    # 性能指標
                    performance = metadata.get('performance', {})
                    if performance.get('total_stages', 0) > 0:
                        with st.expander("📊 性能詳情"):
                            st.markdown(f"**總耗時:** {performance.get('total_time', 0):.3f}秒")
                            st.markdown(f"**處理階段:** {performance.get('total_stages', 0)}個")
                            
                            for stage in performance.get('stages', []):
                                st.caption(f"🔧 {stage['stage']}: {stage['duration']:.3f}秒")
                    
                    # 顯示來源
                    sources = chat.get('sources', [])
                    if sources:
                        with st.expander("📚 參考來源"):
                            for j, source in enumerate(sources[:3]):
                                st.markdown(f"""
                                **來源 {j+1}:** {source['source']}  
                                **類型:** {source.get('type', 'document')}  
                                **評分:** {source['score']:.3f}  
                                **內容預覽:** {source['content'][:150]}...
                                """)
        else:
            st.info("💡 開始您的第一個問題吧！")
    
    # 建議問題（如果沒有聊天歷史）
    if not st.session_state.chat_history:
        st.markdown("### 💡 與知識庫內容相關的建議問題")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 快速整理內容重點", use_container_width=True):
                handle_chat_query_v2("快速整理內容重點")
            if st.button("📊 關鍵字分析", use_container_width=True):
                handle_chat_query_v2("請分析關鍵字")
        
        with col2:
            if st.button("🎯 有什麼重要信息？", use_container_width=True):
                handle_chat_query_v2("有什麼重要信息？")
            if st.button("❓ 我可以問什麼問題？", use_container_width=True):
                handle_chat_query_v2("我可以問什麼問題？")
    
    # 問答輸入
    user_question = st.chat_input("輸入您的問題...")
    
    if user_question:
        handle_chat_query_v2(user_question)
    
    # 聊天管理
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ 清空聊天", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.conversation_context = None
            st.success("✅ 聊天記錄已清空")
            st.rerun()
    
    with col2:
        if st.button("📋 匯出對話", use_container_width=True):
            export_chat_history_v2()
    
    with col4:
        if st.session_state.chat_history:
            st.metric("💬 對話數", len(st.session_state.chat_history))

def handle_chat_query_v2(question: str):
    """處理V2.0聊天查詢"""
    try:
        start_time = time.time()
        
        with st.spinner("🤔 AI正在思考中..."):
            # 調用API
            result = st.session_state.api_client.chat_query(
                question=question,
                conversation_context=st.session_state.conversation_context,
                include_sources=True,
                max_sources=3
            )
            
            # 更新對話上下文
            if result.get('context'):
                st.session_state.conversation_context = result['context']
            
            # 計算總耗時
            total_time = time.time() - start_time
            
            # 添加到聊天歷史
            chat_record = {
                'question': question,
                'answer': result['answer'],
                'sources': result.get('sources', []),
                'metadata': result.get('metadata', {}),
                'conversation_id': result.get('conversation_id'),
                'response_time': f"{total_time:.2f}s",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.session_state.chat_history.append(chat_record)
            
            # 顯示成功信息
            optimization_used = result.get('metadata', {}).get('optimization_used', [])
            if optimization_used:
                st.success(f"✅ 查詢完成！使用優化: {', '.join(optimization_used)}")
            else:
                st.success(f"✅ 查詢完成！耗時: {total_time:.2f}s")
            
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 查詢失敗: {str(e)}")
        
        # 添加錯誤記錄到歷史
        error_record = {
            'question': question,
            'answer': f"抱歉，查詢過程中發生錯誤: {str(e)}",
            'sources': [],
            'metadata': {'error': str(e)},
            'response_time': "N/A",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        st.session_state.chat_history.append(error_record)

def render_knowledge_management():
    """渲染知識庫管理頁面"""
    st.markdown("# 📚 知識庫管理 V2.0")
    
    if st.session_state.api_status != "healthy":
        st.error("⚠️ API服務不可用，請檢查連接")
        return
    
    # 文件上傳區域
    st.markdown("## 📤 上傳新文檔")
    
    uploaded_files = st.file_uploader(
        "選擇要上傳的文檔",
        type=['pdf', 'txt', 'docx', 'md', 'png', 'jpg', 'jpeg', 'webp', 'bmp'],
        accept_multiple_files=True,
        help="支援 PDF、Word、文字檔、Markdown 和圖片格式 | 使用V2.0 API處理"
    )
    
    if uploaded_files:
        st.markdown("### 📋 待上傳文件列表")
        
        for file in uploaded_files:
            file_size_mb = file.size / (1024 * 1024)
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                file_ext = Path(file.name).suffix.lower()
                icon = get_file_icon(file_ext)
                st.write(f"{icon} {file.name}")
            
            with col2:
                st.write(f"{file_size_mb:.1f} MB")
            
            with col3:
                st.success("✅ 就緒")
        
        # 處理文件按鈕
        if st.button("🚀 處理文檔並建立知識庫", type="primary", use_container_width=True):
            process_uploaded_files_v2(uploaded_files)
    
    st.markdown("---")
    
    # 現有文檔管理
    st.markdown("## 📋 現有文檔管理")
    
    # 獲取知識庫狀態
    kb_status = get_knowledge_base_status_with_feedback()
    
    if "error" in kb_status:
        st.error(f"❌ 無法獲取知識庫狀態: {kb_status['error']}")
        return
    
    files = kb_status.get("files", [])
    
    if not files:
        st.info("📝 知識庫中暫無文件")
    else:
        # 統計資訊
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 文件總數", kb_status.get("total_files", 0))
        with col2:
            st.metric("🧩 文本塊總數", kb_status.get("total_chunks", 0))
        with col3:
            st.metric("💾 總大小", f"{kb_status.get('total_size_mb', 0):.1f} MB")
        
        # 批量操作
        col1, col2 = st.columns(2)
        with col1:
            # 檢查是否處於清空確認模式
            if st.session_state.get("show_confirm_clear", False):
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    if st.button("取消", key="cancel_clear_kb", use_container_width=True):
                        st.session_state["show_confirm_clear"] = False
                        st.rerun()
                with sub_col2:
                    if st.button("確認清空", key="confirm_clear_kb_btn", type="primary", use_container_width=True):
                        execute_clear_knowledge_base()
            else:
                if st.button("🗑️ 清空知識庫", use_container_width=True):
                    st.session_state["show_confirm_clear"] = True
                    st.rerun()
                    
        with col2:
            if st.button("📊 生成統計報告", use_container_width=True):
                generate_stats_report_v2(files)
        
        st.markdown("### 📄 文件列表")
        
        # 文件列表
        for i, file_info in enumerate(files):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    icon = get_file_icon(file_info.get('type', ''))
                    st.write(f"{icon} **{file_info['name']}**")
                    st.caption(f"🧩 {file_info.get('chunk_count', 0)} chunks • {file_info.get('size_mb', 0):.2f} MB")
                
                with col2:
                    st.write(f"📅 {file_info.get('upload_time', 'N/A')}")
                
                with col3:
                    st.write(f"🔗 ID: {file_info.get('id', 'N/A')[:8]}...")
                
                with col4:
                    delete_key = f"delete_file_{file_info.get('id', i)}"
                    
                    # 檢查是否處於確認模式
                    if st.session_state.get(f"{delete_key}_confirm", False):
                        col_cancel, col_confirm = st.columns(2)
                        with col_cancel:
                            if st.button("取消", key=f"cancel_{i}", use_container_width=True):
                                st.session_state[f"{delete_key}_confirm"] = False
                                st.rerun()
                        with col_confirm:
                            if st.button("確認刪除", key=f"confirm_{i}", type="primary", use_container_width=True):
                                execute_file_deletion(file_info, delete_key)
                    else:
                        if st.button("🗑️", key=f"delete_{i}", help="刪除文件", use_container_width=True):
                            st.session_state[f"{delete_key}_confirm"] = True
                            st.rerun()

def process_uploaded_files_v2(uploaded_files):
    """V2.0處理上傳文件"""
    try:
        # 顯示處理概述
        total_size_mb = sum(f.size for f in uploaded_files) / (1024 * 1024)
        st.info(f"📋 準備處理 {len(uploaded_files)} 個文件 (總大小: {total_size_mb:.2f} MB)")
        st.info("⏳ 文件處理可能需要較長時間，特別是大文件或PDF文件。請耐心等待...")
        
        # 創建處理狀態容器
        status_container = st.container()
        
        with status_container:
            st.markdown("### 📊 處理進度")
            # API客戶端會在這個區域顯示詳細進度
            results = st.session_state.api_client.batch_upload_files(uploaded_files)
            
            successful = [r for r in results if r.get('status') != 'failed']
            failed = [r for r in results if r.get('status') == 'failed']
            
            # 清除進度顯示區域
            st.markdown("---")
            
            if successful:
                total_chunks = sum(r.get('chunks_created', 0) for r in successful)
                processing_times = [r.get('processing_time_ms', 0) for r in successful if r.get('processing_time_ms')]
                avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
                
                st.success(f"✅ 成功處理 {len(successful)} 個文檔，創建了 {total_chunks} 個文本塊！")
                
                # 顯示處理統計
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("成功文件", len(successful))
                with col2:
                    st.metric("文本塊數", total_chunks)
                with col3:
                    st.metric("平均處理時間", f"{avg_time/1000:.1f}s" if avg_time > 0 else "N/A")
                
                # 顯示處理詳情
                with st.expander("📊 詳細處理結果"):
                    for result in successful:
                        processing_time = result.get('processing_time_ms', 0)
                        time_str = f" ({processing_time/1000:.1f}s)" if processing_time > 0 else ""
                        st.write(f"📄 **{result['filename']}**: {result.get('chunks_created', 0)} chunks{time_str}")
                
                st.balloons()
            
            if failed:
                st.error(f"❌ {len(failed)} 個文檔處理失敗")
                with st.expander("❌ 失敗詳情"):
                    for result in failed:
                        st.write(f"📄 **{result['filename']}**: {result.get('error', 'Unknown error')}")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 批量處理失敗: {str(e)}")
        logger.error(f"批量處理異常: {e}")

def execute_clear_knowledge_base():
    """執行清空知識庫操作"""
    try:
        with st.spinner("正在清空知識庫..."):
            success = st.session_state.api_client.clear_knowledge_base()
            
        if success:
            st.success("✅ 知識庫已成功清空")
            st.balloons()  # 添加慶祝動畫
            # 清除確認狀態
            st.session_state["show_confirm_clear"] = False
            # 延遲後重新載入頁面
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ 清空知識庫失敗")
            st.session_state["confirm_clear_kb"] = False
            
    except Exception as e:
        st.error(f"❌ 清空知識庫時發生錯誤: {str(e)}")
        st.session_state["confirm_clear_kb"] = False

def get_knowledge_base_status_with_feedback():
    """獲取知識庫狀態並提供用戶反饋"""
    try:
        with st.spinner("正在獲取知識庫狀態...（可能需要幾秒鐘）"):
            return st.session_state.api_client.get_knowledge_base_status()
    except Exception as e:
        logger.error(f"獲取知識庫狀態失敗: {e}")
        return {"error": str(e)}

def execute_file_deletion(file_info: Dict, delete_key: str):
    """執行文件刪除操作"""
    file_id = file_info.get('id')
    if not file_id:
        st.error("❌ 無效的文件ID")
        return
    
    try:
        with st.spinner(f"正在刪除 {file_info.get('name', '文件')}..."):
            success = st.session_state.api_client.delete_file_from_knowledge_base(file_id)
            
        if success:
            st.success(f"✅ 已成功刪除 {file_info.get('name', '文件')}")
            # 清除確認狀態
            st.session_state[f"{delete_key}_confirm"] = False
            # 延遲後重新載入頁面
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ 刪除 {file_info.get('name', '文件')} 失敗")
            st.session_state[f"{delete_key}_confirm"] = False
            
    except Exception as e:
        st.error(f"❌ 刪除文件時發生錯誤: {str(e)}")
        st.session_state[f"{delete_key}_confirm"] = False

def delete_file_v2(file_info: Dict, index: int):
    """V2.0刪除文件"""
    confirm_key = f'confirm_delete_v2_{index}'
    
    if st.session_state.get(confirm_key, False):
        # 執行刪除
        file_id = file_info.get('id')
        try:
            if file_id and st.session_state.api_client.delete_file_from_knowledge_base(file_id):
                st.success(f"✅ 已刪除 {file_info['name']}")
                # 清除確認狀態
                st.session_state[confirm_key] = False
                # 延遲一秒後重新載入
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ 刪除 {file_info['name']} 失敗")
                st.session_state[confirm_key] = False
        except Exception as e:
            st.error(f"❌ 刪除 {file_info['name']} 時發生錯誤: {str(e)}")
            st.session_state[confirm_key] = False
    else:
        # 請求確認
        st.session_state[confirm_key] = True
        st.warning(f"⚠️ 確定要刪除 {file_info['name']} 嗎？再次點擊刪除按鈕確認。")
        st.rerun()

def clear_knowledge_base_v2():
    """V2.0清空知識庫"""
    confirm_key = 'confirm_clear_all_v2'
    
    if st.session_state.get(confirm_key, False):
        try:
            with st.spinner("正在清空知識庫..."):
                if st.session_state.api_client.clear_knowledge_base():
                    st.success("✅ 知識庫已清空")
                    # 清除確認狀態
                    st.session_state[confirm_key] = False
                    # 延遲一秒後重新載入
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 清空知識庫失敗")
                    st.session_state[confirm_key] = False
        except Exception as e:
            st.error(f"❌ 清空知識庫時發生錯誤: {str(e)}")
            st.session_state[confirm_key] = False
    else:
        st.session_state[confirm_key] = True
        st.warning("⚠️ 確定要清空整個知識庫嗎？這將刪除所有文件！再次點擊確認。")
        st.rerun()

def render_monitoring():
    """渲染API監控頁面"""
    st.markdown("# 📈 API監控")
    
    if st.session_state.api_status != "healthy":
        st.error("⚠️ API服務不可用，請檢查連接")
        return
    
    # API連接測試
    if st.button("🔄 測試API連接"):
        with st.spinner("測試中..."):
            if st.session_state.api_client.test_connection():
                st.success("✅ API連接正常")
            else:
                st.error("❌ API連接失敗")
    
    # 系統信息
    st.markdown("## 📊 系統信息")
    
    if st.session_state.system_info:
        info = st.session_state.system_info
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 基本信息")
            st.json({
                "api_version": info.get("api_version"),
                "elasticsearch_connected": info.get("elasticsearch_connected"),
                "uptime_seconds": info.get("uptime_seconds"),
                "timestamp": info.get("timestamp")
            })
        
        with col2:
            st.markdown("### 統計數據")
            st.json({
                "total_documents": info.get("total_documents"),
                "total_conversations": info.get("total_conversations"),
                "system_info": info.get("system_info")
            })
    
    # API配置信息
    st.markdown("## ⚙️ API配置")
    st.json({
        "base_url": API_BASE_URL,
        "api_key": API_KEY[:10] + "***" if len(API_KEY) > 10 else "***",
        "session_id": st.session_state.session_id,
        "user_id": st.session_state.user_id
    })

def export_chat_history_v2():
    """V2.0匯出對話記錄"""
    if not st.session_state.chat_history:
        st.warning("📝 沒有對話記錄可以匯出")
        return
    
    # 準備匯出數據
    export_data = {
        "export_time": datetime.now().isoformat(),
        "api_version": "V2.0",
        "session_id": st.session_state.session_id,
        "user_id": st.session_state.user_id,
        "total_conversations": len(st.session_state.chat_history),
        "conversations": st.session_state.chat_history
    }
    
    # 生成JSON文件
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 下載對話記錄 (JSON)",
        data=json_str,
        file_name=f"chat_history_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.success("✅ 對話記錄已準備好下載")

def generate_stats_report_v2(files: List[Dict]):
    """V2.0生成統計報告"""
    report = f"""
# 知識庫統計報告 V2.0
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
API版本: V2.0

## 基本統計
- 文件總數: {len(files)}
- 文本塊總數: {sum(file.get('chunk_count', 0) for file in files)}
- 總大小: {sum(file.get('size_mb', 0) for file in files):.2f} MB

## 文件類型分佈
"""
    
    type_count = {}
    for file in files:
        file_type = file.get('type', 'unknown')
        type_count[file_type] = type_count.get(file_type, 0) + 1
    
    for file_type, count in type_count.items():
        report += f"- {file_type}: {count} 個文件\n"
    
    report += f"""

## 詳細文件列表
"""
    
    for file in files:
        report += f"- {file['name']} ({file.get('size_mb', 0):.2f} MB, {file.get('chunk_count', 0)} chunks)\n"
    
    st.download_button(
        "📊 下載統計報告 V2.0",
        report,
        file_name=f"knowledge_base_stats_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True
    )

def get_file_icon(file_type: str) -> str:
    """獲取文件圖標"""
    icon_map = {
        '.pdf': '📑',
        'pdf': '📑',
        '.txt': '📄',
        'txt': '📄',
        '.docx': '📘',
        'docx': '📘',
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

# 主程序
def main():
    """主程序"""
    load_styles()
    initialize_session_state()
    
    # 啟動時檢查API狀態
    if st.session_state.api_status == "checking":
        check_api_status()
    
    render_header()
    render_sidebar()
    
    # 根據當前頁面渲染內容
    if st.session_state.current_page == "Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "Chat":
        render_chat()
    elif st.session_state.current_page == "Knowledge":
        render_knowledge_management()
    elif st.session_state.current_page == "Monitoring":
        render_monitoring()

if __name__ == "__main__":
    main()