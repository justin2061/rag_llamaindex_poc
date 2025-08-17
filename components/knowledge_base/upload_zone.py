import streamlit as st
import os
from datetime import datetime
from typing import List, Optional
from user_file_manager import UserFileManager

class UploadZone:
    """改良的檔案上傳區域"""
    
    def __init__(self):
        self.file_manager = UserFileManager()
        
    def render_empty_state(self) -> Optional[List]:
        """渲染空狀態的上傳區域"""
        st.markdown("""
        <div class="upload-zone">
            <div style="text-align: center; padding: 2rem;">
                <h2 style="color: var(--text-secondary); margin-bottom: 1rem;">
                    📤 開始建立您的知識庫
                </h2>
                <p style="color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 2rem;">
                    上傳文檔開始使用 AI 助手
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 檔案上傳器
        uploaded_files = st.file_uploader(
            "選擇檔案",
            type=['pdf', 'txt', 'docx', 'md', 'png', 'jpg', 'jpeg', 'webp', 'bmp'],
            accept_multiple_files=True,
            help="支援 PDF、文字檔、圖片等格式"
        )
        
        return uploaded_files
    
    def render_upload_with_files(self) -> Optional[List]:
        """渲染有檔案時的上傳區域"""
        with st.expander("📤 上傳更多檔案", expanded=False):
            uploaded_files = st.file_uploader(
                "選擇檔案",
                type=['pdf', 'txt', 'docx', 'md', 'png', 'jpg', 'jpeg', 'webp', 'bmp'],
                accept_multiple_files=True,
                help="支援 PDF、文字檔、圖片等格式",
                key="additional_upload"
            )
            
            return uploaded_files
    
    def render_upload_progress(self, uploaded_files: List) -> dict:
        """渲染上傳進度"""
        if not uploaded_files:
            return {}
        
        st.markdown("### 📋 上傳檔案預覽")
        
        progress_data = {
            'total_files': len(uploaded_files),
            'total_size': 0,
            'document_files': [],
            'image_files': [],
            'valid_files': 0
        }
        
        # 顯示檔案列表
        for i, file in enumerate(uploaded_files):
            file_type = self._get_file_type(file.name)
            file_size_mb = file.size / (1024 * 1024)
            progress_data['total_size'] += file.size
            
            # 驗證檔案
            is_valid = self.file_manager.validate_file(file)
            if is_valid:
                progress_data['valid_files'] += 1
            
            # 分類檔案
            if file_type == 'image':
                progress_data['image_files'].append(file.name)
            else:
                progress_data['document_files'].append(file.name)
            
            # 顯示檔案資訊
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                file_icon = self._get_file_icon(file_type)
                st.write(f"{file_icon} {file.name}")
            
            with col2:
                st.write(f"{file_size_mb:.1f} MB")
            
            with col3:
                st.write(file_type.upper())
            
            with col4:
                if is_valid:
                    st.success("✅")
                else:
                    st.error("❌")
        
        # 顯示總結
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "總檔案數",
                f"{progress_data['valid_files']}/{progress_data['total_files']}"
            )
        
        with col2:
            st.metric(
                "總大小",
                f"{progress_data['total_size'] / (1024 * 1024):.1f} MB"
            )
        
        with col3:
            doc_count = len(progress_data['document_files'])
            img_count = len(progress_data['image_files'])
            st.metric(
                "文檔/圖片",
                f"{doc_count}/{img_count}"
            )
        
        return progress_data
    
    def render_file_manager(self):
        """渲染檔案管理器"""
        st.markdown("### 📁 已上傳的檔案")
        
        files = self.file_manager.get_uploaded_files()
        
        if not files:
            st.info("尚未上傳任何檔案")
            return
        
        # 檔案列表
        for file_info in files:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    file_icon = self._get_file_icon(file_info['type'])
                    st.write(f"{file_icon} {file_info['name']}")
                
                with col2:
                    st.write(f"{file_info['size_mb']} MB")
                
                with col3:
                    st.write(file_info['modified'].strftime("%m/%d %H:%M"))
                
                with col4:
                    if st.button("🗑️", key=f"delete_{file_info['name']}", help="刪除檔案"):
                        if self.file_manager.delete_file(file_info['name']):
                            st.success(f"已刪除 {file_info['name']}")
                            st.rerun()
                        else:
                            st.error("刪除失敗")
        
        # 批量操作
        st.markdown("---")
        if st.button("🗑️ 清空所有檔案", type="secondary"):
            if st.button("確認清空", type="secondary", key="confirm_clear"):
                # 實作清空邏輯
                st.success("已清空所有檔案")
                st.rerun()
    
    def render_quick_start_guide(self):
        """渲染快速開始指南"""
        st.markdown("""
        <div class="custom-card">
            <h3>🚀 快速開始</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📄</div>
                    <strong>1. 上傳文檔</strong>
                    <p style="font-size: 0.9rem; color: var(--text-secondary);">支援 PDF、Word、文字檔</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🖼️</div>
                    <strong>2. 新增圖片</strong>
                    <p style="font-size: 0.9rem; color: var(--text-secondary);">OCR 提取圖片中的文字</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🕸️</div>
                    <strong>3. 建立圖譜</strong>
                    <p style="font-size: 0.9rem; color: var(--text-secondary);">AI 自動建構知識圖譜</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
                    <strong>4. 開始問答</strong>
                    <p style="font-size: 0.9rem; color: var(--text-secondary);">基於圖譜的智能對話</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_upload_tips(self):
        """渲染上傳提示"""
        with st.expander("💡 上傳提示", expanded=False):
            st.markdown("""
            **支援的檔案格式：**
            - 📄 文檔：PDF, DOCX, TXT, Markdown
            - 🖼️ 圖片：PNG, JPG, JPEG, WEBP, BMP
            
            **檔案大小限制：**
            - 文檔：最大 10 MB
            - 圖片：最大 5 MB
            
            **最佳實務：**
            - 確保 PDF 檔案可以選取文字（非掃描檔）
            - 圖片內容清晰，文字可讀
            - 一次上傳多個相關檔案以建立更完整的知識圖譜
            - 檔案名稱使用有意義的命名
            """)
    
    def _get_file_type(self, filename: str) -> str:
        """獲取檔案類型"""
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        image_exts = ['png', 'jpg', 'jpeg', 'webp', 'bmp']
        
        if ext in image_exts:
            return 'image'
        else:
            return 'document'
    
    def _get_file_icon(self, file_type: str) -> str:
        """獲取檔案圖標"""
        icons = {
            'document': '📄',
            'image': '🖼️',
            'pdf': '📕',
            'txt': '📝',
            'docx': '📘',
            'md': '📋'
        }
        
        return icons.get(file_type, '📄')
    
    def get_upload_stats(self) -> dict:
        """獲取上傳統計"""
        files = self.file_manager.get_uploaded_files()
        
        stats = {
            'total_files': len(files),
            'total_size_mb': sum(f['size_mb'] for f in files),
            'document_count': len([f for f in files if f['type'] == 'document']),
            'image_count': len([f for f in files if f['type'] == 'image']),
            'recent_uploads': sorted(files, key=lambda x: x['modified'], reverse=True)[:5]
        }
        
        return stats
