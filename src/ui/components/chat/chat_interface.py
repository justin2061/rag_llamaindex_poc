import streamlit as st
from typing import List, Dict, Optional
import time
from datetime import datetime

class ChatInterface:
    """智能聊天界面組件"""
    
    def __init__(self):
        # 初始化聊天狀態
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'chat_input' not in st.session_state:
            st.session_state.chat_input = ""
        if 'is_thinking' not in st.session_state:
            st.session_state.is_thinking = False
    
    def render_chat_container(self) -> Optional[str]:
        """渲染主要聊天界面"""
        # 聊天樣式
        st.markdown("""
        <style>
        .chat-container {
            background: #ffffff;
            border-radius: 1rem;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #e5e7eb;
            max-height: 600px;
            overflow-y: auto;
        }
        .message-bubble {
            margin: 0.5rem 0;
            padding: 0.75rem 1rem;
            border-radius: 1rem;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-message {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            margin-left: auto;
            margin-right: 0;
            border-bottom-right-radius: 0.25rem;
        }
        .assistant-message {
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            color: #1f2937;
            margin-left: 0;
            margin-right: auto;
            border-bottom-left-radius: 0.25rem;
        }
        .message-meta {
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
        .thinking-indicator {
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            background: #f3f4f6;
            border-radius: 1rem;
            margin: 0.5rem 0;
            max-width: 200px;
        }
        .thinking-dots {
            display: flex;
            gap: 0.25rem;
        }
        .thinking-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6b7280;
            animation: thinking 1.4s infinite ease-in-out;
        }
        .thinking-dot:nth-child(1) { animation-delay: -0.32s; }
        .thinking-dot:nth-child(2) { animation-delay: -0.16s; }
        .thinking-dot:nth-child(3) { animation-delay: 0s; }
        
        @keyframes thinking {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        
        .source-indicator {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 0.5rem;
            padding: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.875rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 聊天歷史顯示
        self._render_chat_history()
        
        # 思考指示器
        if st.session_state.get('is_thinking', False):
            self._render_thinking_indicator()
        
        # 輸入區域
        return self._render_input_area()
    
    def _render_chat_history(self):
        """渲染聊天歷史"""
        # 確保 chat_messages 已初始化
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
            
        if not st.session_state.chat_messages:
            # 空狀態
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #6b7280;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                <h3>開始您的智能問答</h3>
                <p>在下方輸入您的問題，我會基於您上傳的文檔來回答</p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # 渲染訊息
        for message in st.session_state.chat_messages:
            self._render_message(message)
    
    def _render_message(self, message: Dict):
        """渲染單個訊息"""
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="message-bubble user-message">
                {message['content']}
                <div class="message-meta">
                    您 • {message.get('timestamp', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message-bubble assistant-message">
                {message['content']}
                <div class="message-meta">
                    AI 助理 • {message.get('timestamp', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 來源指示器
            if message.get('sources'):
                self._render_source_indicator(message['sources'])
            
            # 操作按鈕
            self._render_message_actions(message)
    
    def _render_source_indicator(self, sources: List[str]):
        """渲染來源指示器"""
        sources_text = "、".join(sources[:3])  # 最多顯示3個來源
        if len(sources) > 3:
            sources_text += f" 等 {len(sources)} 個來源"
        
        st.markdown(f"""
        <div class="source-indicator">
            📚 <strong>參考來源:</strong> {sources_text}
        </div>
        """, unsafe_allow_html=True)
    
    def _render_message_actions(self, message: Dict):
        """渲染訊息操作按鈕"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
        
        with col1:
            if st.button("👍", key=f"like_{message.get('id', '')}", help="有用"):
                self._handle_feedback(message, "like")
        
        with col2:
            if st.button("👎", key=f"dislike_{message.get('id', '')}", help="無用"):
                self._handle_feedback(message, "dislike")
        
        with col3:
            if st.button("📋", key=f"copy_{message.get('id', '')}", help="複製"):
                st.write("已複製到剪貼板")  # 實際複製功能需要JavaScript
        
        with col4:
            pass  # 空白區域
    
    def _render_thinking_indicator(self):
        """渲染思考指示器"""
        st.markdown("""
        <div class="thinking-indicator">
            <span style="margin-right: 0.5rem;">🤔 AI 正在思考</span>
            <div class="thinking-dots">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_input_area(self) -> Optional[str]:
        """渲染輸入區域"""
        # 建議問題
        suggested_question = self._render_suggested_questions()
        if suggested_question:
            return suggested_question
        
        # 輸入框和發送按鈕
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "輸入您的問題...",
                key="chat_input_field",
                placeholder="例如：這份文檔的主要內容是什麼？",
                label_visibility="collapsed"
            )
        
        with col2:
            send_clicked = st.button("發送 📤", type="primary", use_container_width=True)
        
        # 快捷鍵提示
        st.markdown("""
        <div style="text-align: center; color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem;">
            💡 提示：您可以進行連續對話，AI 會記住之前的內容
        </div>
        """, unsafe_allow_html=True)
        
        # 處理發送
        if send_clicked and user_input.strip():
            return user_input.strip()
        
        return None
    
    def _render_suggested_questions(self):
        """渲染建議問題"""
        # 這裡可以基於上傳的文檔內容動態生成建議問題
        suggestions = [
            "這份文檔的主要內容是什麼？",
            "文檔中提到的關鍵概念有哪些？",
            "能幫我總結重點嗎？",
            "有哪些值得注意的細節？"
        ]
        
        if suggestions:
            st.markdown("### 💡 建議問題")
            
            # 使用列來顯示建議問題
            cols = st.columns(2)
            for i, suggestion in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(f"💬 {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                        return suggestion
        
        return None
    
    def add_message(self, role: str, content: str, sources: List[str] = None):
        """添加訊息到聊天歷史"""
        message = {
            'id': len(st.session_state.chat_messages),
            'role': role,
            'content': content,
            'timestamp': datetime.now().strftime("%H:%M"),
            'sources': sources or []
        }
        
        st.session_state.chat_messages.append(message)
    
    def set_thinking(self, thinking: bool):
        """設定思考狀態"""
        st.session_state.is_thinking = thinking
    
    def clear_chat(self):
        """清空聊天記錄"""
        st.session_state.chat_messages = []
        st.success("聊天記錄已清空")
    
    def _handle_feedback(self, message: Dict, feedback_type: str):
        """處理用戶回饋"""
        # 這裡可以記錄用戶回饋，用於改善AI回答品質
        message[f'{feedback_type}_feedback'] = True
        
        if feedback_type == "like":
            st.success("感謝您的回饋！😊")
        else:
            st.info("感謝您的回饋，我們會持續改進！")
    
    def export_chat(self) -> str:
        """匯出聊天記錄"""
        if not st.session_state.chat_messages:
            return "沒有聊天記錄可匯出"
        
        export_text = "# 聊天記錄匯出\n\n"
        export_text += f"匯出時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for message in st.session_state.chat_messages:
            role_name = "您" if message['role'] == 'user' else "AI 助理"
            export_text += f"## {role_name} ({message['timestamp']})\n\n"
            export_text += f"{message['content']}\n\n"
            
            if message.get('sources'):
                export_text += f"**參考來源:** {', '.join(message['sources'])}\n\n"
            
            export_text += "---\n\n"
        
        return export_text
    
    def get_chat_stats(self) -> Dict:
        """獲取聊天統計"""
        messages = st.session_state.chat_messages
        
        user_messages = [m for m in messages if m['role'] == 'user']
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_sources': sum(len(m.get('sources', [])) for m in assistant_messages),
            'avg_response_length': sum(len(m['content']) for m in assistant_messages) / max(len(assistant_messages), 1)
        }
