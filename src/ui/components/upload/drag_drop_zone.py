import streamlit as st
from typing import List, Optional, Dict, Any
import os

class DragDropZone:
    """拖拽上傳區域組件"""
    
    def __init__(self):
        self.supported_formats = {
            'documents': ['.pdf', '.txt', '.docx', '.md', '.markdown'],
            'images': ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_image_size = 5 * 1024 * 1024   # 5MB
    
    def render_empty_state(self) -> bool:
        """渲染空狀態的大型上傳區域"""
        st.markdown("""
        <style>
        .drag-drop-zone {
            border: 3px dashed #e5e7eb;
            border-radius: 1rem;
            padding: 3rem 2rem;
            text-align: center;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            transition: all 0.3s ease;
            margin: 2rem 0;
            min-height: 300px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .drag-drop-zone:hover {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.1);
        }
        .upload-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.7;
        }
        .upload-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        .upload-subtitle {
            color: #6b7280;
            margin-bottom: 1.5rem;
            font-size: 1.1rem;
        }
        .upload-formats {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .format-badge {
            background: #f3f4f6;
            color: #374151;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.875rem;
            font-weight: 500;
        }
        .quick-start-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        .quick-start-card {
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #e5e7eb;
            text-align: center;
            transition: all 0.3s ease;
        }
        .quick-start-card:hover {
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
            transform: translateY(-2px);
        }
        .card-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .card-title {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        .card-description {
            color: #6b7280;
            font-size: 0.875rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 主要上傳區域
        st.markdown("""
        <div class="drag-drop-zone">
            <div class="upload-icon">📤</div>
            <div class="upload-title">拖拽檔案到這裡開始</div>
            <div class="upload-subtitle">或點擊下方按鈕選擇檔案</div>
            
            <div class="upload-formats">
                <span class="format-badge">📄 PDF</span>
                <span class="format-badge">📝 Word</span>
                <span class="format-badge">📋 文字檔</span>
                <span class="format-badge">🖼️ 圖片</span>
                <span class="format-badge">📑 Markdown</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 上傳按鈕區域
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # 文檔上傳
            doc_files = st.file_uploader(
                "📄 選擇文檔檔案",
                type=['pdf', 'txt', 'docx', 'md'],
                accept_multiple_files=True,
                key="main_doc_uploader",
                help="支援 PDF、Word、文字檔案和 Markdown"
            )
            
            # 圖片上傳
            image_files = st.file_uploader(
                "🖼️ 選擇圖片檔案",
                type=['png', 'jpg', 'jpeg', 'webp', 'bmp'],
                accept_multiple_files=True,
                key="main_image_uploader",
                help="支援 PNG、JPG、JPEG、WEBP、BMP 格式，將進行 OCR 處理"
            )
        
        # 如果有檔案上傳，返回檔案列表
        uploaded_files = []
        if doc_files:
            uploaded_files.extend(doc_files)
        if image_files:
            uploaded_files.extend(image_files)
        
        return uploaded_files
    
    def render_upload_progress(self, files: List[Any]) -> Dict[str, Any]:
        """渲染上傳進度"""
        if not files:
            return {}
        
        st.markdown("### 📋 檔案處理狀態")
        
        progress_data = {}
        
        for i, file in enumerate(files):
            # 檔案資訊卡片
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    file_type = self._get_file_type(file.name)
                    icon = "📄" if file_type == "document" else "🖼️"
                    st.write(f"{icon} **{file.name}**")
                
                with col2:
                    size_mb = file.size / (1024 * 1024)
                    st.write(f"{size_mb:.1f} MB")
                
                with col3:
                    # 狀態指示器
                    status_key = f"file_status_{i}"
                    if status_key not in st.session_state:
                        st.session_state[status_key] = "waiting"
                    
                    status = st.session_state[status_key]
                    status_icon = {
                        "waiting": "⏳",
                        "processing": "🔄",
                        "completed": "✅",
                        "error": "❌"
                    }.get(status, "❓")
                    
                    st.write(f"{status_icon} {status}")
                
                with col4:
                    # 進度條
                    progress_key = f"file_progress_{i}"
                    if progress_key not in st.session_state:
                        st.session_state[progress_key] = 0
                    
                    progress = st.session_state[progress_key]
                    st.progress(progress)
                
                progress_data[file.name] = {
                    "status": status,
                    "progress": progress,
                    "size": file.size,
                    "type": file_type
                }
                
                st.divider()
        
        return progress_data
    
    def render_quick_start_guide(self):
        """渲染快速開始指南"""
        st.markdown("""
        <div class="quick-start-cards">
            <div class="quick-start-card">
                <div class="card-icon">🚀</div>
                <div class="card-title">3 步驟開始</div>
                <div class="card-description">上傳檔案 → 等待處理 → 開始問答</div>
            </div>
            
            <div class="quick-start-card">
                <div class="card-icon">📚</div>
                <div class="card-title">多格式支援</div>
                <div class="card-description">PDF、Word、圖片、文字檔都支援</div>
            </div>
            
            <div class="quick-start-card">
                <div class="card-icon">🧠</div>
                <div class="card-title">智能對話</div>
                <div class="card-description">記住歷史對話，支援連續問答</div>
            </div>
            
            <div class="quick-start-card">
                <div class="card-icon">🔒</div>
                <div class="card-title">資料安全</div>
                <div class="card-description">所有資料在本地處理，完全保密</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def validate_file(self, file) -> Dict[str, Any]:
        """驗證檔案"""
        result = {
            "valid": True,
            "error": None,
            "warnings": []
        }
        
        # 檢查檔案大小
        file_type = self._get_file_type(file.name)
        max_size = self.max_image_size if file_type == "image" else self.max_file_size
        
        if file.size > max_size:
            result["valid"] = False
            result["error"] = f"檔案大小超過限制 ({max_size / (1024*1024):.0f}MB)"
            return result
        
        # 檢查檔案格式
        file_ext = os.path.splitext(file.name)[1].lower()
        all_formats = self.supported_formats['documents'] + self.supported_formats['images']
        
        if file_ext not in all_formats:
            result["valid"] = False
            result["error"] = f"不支援的檔案格式: {file_ext}"
            return result
        
        # 添加警告
        if file.size > 5 * 1024 * 1024:  # 5MB
            result["warnings"].append("大檔案可能需要較長處理時間")
        
        if file_type == "image" and file.size < 100 * 1024:  # 100KB
            result["warnings"].append("圖片檔案較小，OCR效果可能受限")
        
        return result
    
    def _get_file_type(self, filename: str) -> str:
        """取得檔案類型"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in self.supported_formats['documents']:
            return "document"
        elif ext in self.supported_formats['images']:
            return "image"
        else:
            return "unknown"
    
    def render_upload_tips(self):
        """渲染上傳提示"""
        with st.expander("💡 上傳檔案的最佳實踐", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **📄 文檔檔案建議：**
                - PDF 檔案品質越好，解析越準確
                - Word 檔案會自動轉換格式
                - 文字檔案請使用 UTF-8 編碼
                - 建議單檔不超過 10MB
                """)
            
            with col2:
                st.markdown("""
                **🖼️ 圖片檔案建議：**
                - 圖片清晰度影響 OCR 效果
                - 建議使用高解析度圖片
                - 文字對比度要足夠
                - 建議單檔不超過 5MB
                """)
    
    def update_file_status(self, filename: str, status: str, progress: float = 0):
        """更新檔案處理狀態"""
        # 這個方法供外部調用，更新處理狀態
        for key in st.session_state.keys():
            if key.startswith("file_status_") and filename in str(st.session_state.get(key, "")):
                st.session_state[key] = status
                # 同時更新進度
                progress_key = key.replace("status", "progress")
                st.session_state[progress_key] = progress
                break
