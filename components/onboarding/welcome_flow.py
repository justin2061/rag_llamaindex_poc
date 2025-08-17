import streamlit as st
from typing import Optional
import time

class WelcomeFlow:
    """歡迎引導流程組件"""
    
    def __init__(self):
        # 初始化引導狀態
        if 'onboarding_step' not in st.session_state:
            st.session_state.onboarding_step = 0
        if 'show_onboarding' not in st.session_state:
            st.session_state.show_onboarding = False
    
    def should_show_onboarding(self, is_first_visit: bool, completed_onboarding: bool) -> bool:
        """判斷是否應該顯示引導"""
        return is_first_visit and not completed_onboarding
    
    def render_welcome_modal(self) -> Optional[str]:
        """渲染歡迎模態框"""
        if not st.session_state.get('show_onboarding', False):
            return None
        
        # 創建模態框樣式
        st.markdown("""
        <style>
        .welcome-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .welcome-content {
            background: white;
            padding: 2rem;
            border-radius: 1rem;
            max-width: 600px;
            width: 90%;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        .welcome-step {
            margin: 1rem 0;
        }
        .step-indicator {
            display: flex;
            justify-content: center;
            margin: 1rem 0;
        }
        .step-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin: 0 5px;
            background: #e5e7eb;
            transition: all 0.3s ease;
        }
        .step-dot.active {
            background: #3b82f6;
            transform: scale(1.2);
        }
        .welcome-buttons {
            margin-top: 1.5rem;
            display: flex;
            justify-content: space-between;
            gap: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 引導步驟內容
        steps = [
            {
                "title": "🎉 歡迎使用智能文檔問答助理！",
                "content": "這是一個多模態的知識庫問答系統，讓您可以上傳文檔和圖片，建立個人專屬的智能助理。",
                "icon": "🎯"
            },
            {
                "title": "📤 輕鬆上傳您的文檔",
                "content": "支援 PDF、Word、文字檔和圖片。您可以拖拽檔案到上傳區域，或點擊選擇檔案。系統會自動處理並建立索引。",
                "icon": "📁"
            },
            {
                "title": "🤖 開始智能問答",
                "content": "上傳完成後，您就可以向您的文檔提問了！系統會基於您的內容提供精準回答，並記住對話歷史。",
                "icon": "💬"
            },
            {
                "title": "🚀 準備開始吧！",
                "content": "讓我們從上傳第一個文檔開始，建立您的專屬知識庫。您隨時可以在設定中重新查看此教學。",
                "icon": "✨"
            }
        ]
        
        current_step = st.session_state.onboarding_step
        step_data = steps[current_step]
        
        with st.container():
            # 創建三欄佈局
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                # 步驟指示器
                st.markdown(self._create_step_indicator(current_step, len(steps)), unsafe_allow_html=True)
                
                # 主要內容
                st.markdown(f"""
                <div class="welcome-step">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">{step_data['icon']}</div>
                    <h2 style="color: #1f2937; margin-bottom: 1rem;">{step_data['title']}</h2>
                    <p style="color: #6b7280; font-size: 1.1rem; line-height: 1.6;">{step_data['content']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 按鈕區域
                button_col1, button_col2, button_col3 = st.columns([1, 1, 1])
                
                with button_col1:
                    if current_step > 0:
                        if st.button("⬅️ 上一步", key="prev_step"):
                            st.session_state.onboarding_step -= 1
                            st.rerun()
                
                with button_col2:
                    if st.button("跳過引導", key="skip_onboarding"):
                        return self._complete_onboarding()
                
                with button_col3:
                    if current_step < len(steps) - 1:
                        if st.button("下一步 ➡️", key="next_step", type="primary"):
                            st.session_state.onboarding_step += 1
                            st.rerun()
                    else:
                        if st.button("開始使用 🚀", key="start_using", type="primary"):
                            return self._complete_onboarding()
        
        return "showing"
    
    def _create_step_indicator(self, current_step: int, total_steps: int) -> str:
        """創建步驟指示器"""
        dots = []
        for i in range(total_steps):
            class_name = "step-dot active" if i <= current_step else "step-dot"
            dots.append(f'<div class="{class_name}"></div>')
        
        return f"""
        <div class="step-indicator">
            {''.join(dots)}
        </div>
        <p style="text-align: center; color: #9ca3af; font-size: 0.9rem;">
            步驟 {current_step + 1} / {total_steps}
        </p>
        """
    
    def _complete_onboarding(self) -> str:
        """完成引導流程"""
        st.session_state.show_onboarding = False
        st.session_state.onboarding_step = 0
        st.balloons()  # 慶祝效果
        return "completed"
    
    def start_onboarding(self):
        """開始引導流程"""
        st.session_state.show_onboarding = True
        st.session_state.onboarding_step = 0
    
    def render_quick_tips(self):
        """渲染快速提示"""
        st.markdown("""
        ### 💡 快速開始提示
        
        1. **📤 上傳文檔**：將您的 PDF、Word 或圖片檔案拖拽到上傳區域
        2. **⏳ 等待處理**：系統會自動分析和建立索引（通常需要幾分鐘）
        3. **❓ 開始提問**：向您的文檔提出任何問題，獲得智能回答
        4. **🧠 利用記憶**：系統會記住對話歷史，支援連續對話
        
        ---
        """)
    
    def render_feature_highlights(self):
        """渲染功能亮點"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🎯 智能問答
            - 基於您的文檔內容回答
            - 支援複雜問題和推理
            - 提供資料來源引用
            """)
        
        with col2:
            st.markdown("""
            #### 📄 多格式支援
            - PDF、Word、文字檔
            - 圖片 OCR 文字識別  
            - 批次檔案處理
            """)
        
        with col3:
            st.markdown("""
            #### 🧠 對話記憶
            - 記住對話歷史
            - 上下文感知回答
            - 連續深度討論
            """)
    
    def render_success_celebration(self):
        """渲染成功慶祝"""
        st.success("🎉 歡迎使用智能文檔問答助理！")
        
        # 顯示成功動畫（使用 Streamlit 內建效果）
        success_placeholder = st.empty()
        
        with success_placeholder.container():
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎊</div>
                <h3 style="color: #10b981;">設定完成！</h3>
                <p style="color: #6b7280;">您現在可以開始上傳文檔並建立您的知識庫了</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 3秒後清除慶祝畫面
        time.sleep(1)
        success_placeholder.empty()
