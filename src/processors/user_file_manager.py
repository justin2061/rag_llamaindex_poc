import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st
from config.config import USER_UPLOADS_DIR, MAX_FILE_SIZE_MB, MAX_IMAGE_SIZE_MB, SUPPORTED_FILE_TYPES

class UserFileManager:
    def __init__(self):
        self.upload_dir = USER_UPLOADS_DIR
        self.supported_file_types = SUPPORTED_FILE_TYPES
        self.max_file_size = MAX_FILE_SIZE_MB * 1024 * 1024  # 轉換為bytes
        self.max_image_size = MAX_IMAGE_SIZE_MB * 1024 * 1024
        
    def validate_file(self, uploaded_file) -> bool:
        """驗證上傳的檔案"""
        import logging
        logger = logging.getLogger(__name__)
        
        # FastAPI UploadFile 使用 filename 屬性，Streamlit 使用 name 屬性
        filename = getattr(uploaded_file, 'filename', getattr(uploaded_file, 'name', 'unknown'))
        logger.info(f"🔍 FileManager: 驗證文件 - {filename}")
        
        # 檢查檔案格式
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        logger.info(f"   - 檔案副檔名: {file_ext}")
        logger.info(f"   - 支援的格式: {self.supported_file_types}")
        
        if file_ext not in self.supported_file_types:
            logger.error(f"❌ FileManager: 不支援的檔案格式: {file_ext} - {filename}")
            if hasattr(st, 'error'):  # 只有在Streamlit環境才調用
                st.error(f"不支援的檔案格式: {file_ext}")
            return False
        
        logger.info(f"✅ FileManager: 檔案格式驗證通過 - {file_ext}")
        
        # 檢查檔案大小
        is_image = self.is_image_file(filename)
        max_size = self.max_image_size if is_image else self.max_file_size
        max_size_mb = max_size / (1024 * 1024)
        
        # FastAPI UploadFile 使用不同的大小屬性
        file_size = getattr(uploaded_file, 'size', 0)
        if hasattr(uploaded_file, 'file'):
            # 對於 FastAPI UploadFile，需要通過實際讀取來獲取大小
            try:
                current_pos = uploaded_file.file.tell()
                uploaded_file.file.seek(0, 2)  # 移動到文件末尾
                file_size = uploaded_file.file.tell()
                uploaded_file.file.seek(current_pos)  # 恢復原位置
            except:
                pass
                
        file_size_mb = file_size / (1024 * 1024)
        
        logger.info(f"   - 文件類型: {'圖片' if is_image else '文檔'}")
        logger.info(f"   - 文件大小: {file_size_mb:.2f} MB")
        logger.info(f"   - 大小限制: {max_size_mb:.2f} MB")
        
        if file_size > max_size:
            logger.error(f"❌ FileManager: 檔案大小超過限制: {file_size_mb:.1f}MB > {max_size_mb}MB - {filename}")
            if hasattr(st, 'error'):  # 只有在Streamlit環境才調用
                st.error(f"檔案大小超過限制: {file_size_mb:.1f}MB > {max_size_mb}MB")
            return False
        
        logger.info(f"✅ FileManager: 檔案大小驗證通過 - {filename}")
        return True
    
    def is_image_file(self, filename: str) -> bool:
        """判斷是否為圖片檔案"""
        image_extensions = ['png', 'jpg', 'jpeg', 'webp', 'bmp']
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return file_ext in image_extensions
    
    def is_document_file(self, filename: str) -> bool:
        """判斷是否為文檔檔案"""
        doc_extensions = ['pdf', 'txt', 'docx', 'md']
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return file_ext in doc_extensions
    
    def save_uploaded_file(self, uploaded_file) -> Optional[str]:
        """儲存上傳的檔案"""
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # 獲取文件名
        filename = getattr(uploaded_file, 'filename', getattr(uploaded_file, 'name', 'unknown'))
        
        # 獲取文件大小
        file_size = getattr(uploaded_file, 'size', 0)
        if hasattr(uploaded_file, 'file') and file_size == 0:
            try:
                current_pos = uploaded_file.file.tell()
                uploaded_file.file.seek(0, 2)
                file_size = uploaded_file.file.tell()
                uploaded_file.file.seek(current_pos)
            except:
                pass
        
        logger.info(f"💾 FileManager: 開始保存文件 - {filename}")
        logger.info(f"   - 文件大小: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB)")
        
        if not self.validate_file(uploaded_file):
            logger.error(f"❌ FileManager: 文件驗證失敗 - {filename}")
            return None
        
        logger.info(f"✅ FileManager: 文件驗證通過 - {filename}")
        
        try:
            # 生成唯一檔案名稱避免衝突
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]
            unique_filename = f"{base_name}_{timestamp}{extension}"
            
            file_path = os.path.join(self.upload_dir, unique_filename)
            logger.info(f"📁 FileManager: 目標路徑 - {file_path}")
            
            # 確保目錄存在
            os.makedirs(self.upload_dir, exist_ok=True)
            logger.info(f"📂 FileManager: 確保目錄存在 - {self.upload_dir}")
            
            # 儲存檔案
            logger.info(f"💻 FileManager: 開始寫入文件數據 - {filename}")
            with open(file_path, "wb") as f:
                # FastAPI UploadFile 需要不同的讀取方法
                if hasattr(uploaded_file, 'file'):
                    # 確保文件指針在開始位置
                    uploaded_file.file.seek(0)
                    data = uploaded_file.file.read()
                elif hasattr(uploaded_file, 'read'):
                    # Streamlit UploadedFile
                    data = uploaded_file.read()
                else:
                    # 其他情況，嘗試獲取值
                    data = getattr(uploaded_file, 'getvalue', lambda: b'')()
                f.write(data)
                logger.info(f"   - 實際寫入數據: {len(data):,} bytes")
            
            # 驗證文件是否成功寫入
            if os.path.exists(file_path):
                actual_size = os.path.getsize(file_path)
                logger.info(f"✅ FileManager: 文件寫入成功")
                logger.info(f"   - 磁盤文件大小: {actual_size:,} bytes")
                logger.info(f"   - 大小匹配: {actual_size == file_size}")
            else:
                logger.error(f"❌ FileManager: 文件寫入後不存在於磁盤 - {file_path}")
                return None
            
            # 重置檔案指針
            if hasattr(uploaded_file, 'file'):
                uploaded_file.file.seek(0)
            else:
                uploaded_file.seek(0)
            logger.info(f"🔄 FileManager: 重置文件指針 - {filename}")
            
            logger.info(f"🎉 FileManager: 文件保存完成 - {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ FileManager: 儲存檔案時發生錯誤: {filename} - {str(e)}")
            import traceback
            logger.error(f"   錯誤堆疊: {traceback.format_exc()}")
            if hasattr(st, 'error'):
                st.error(f"儲存檔案時發生錯誤: {str(e)}")
            return None
    
    def get_uploaded_files(self) -> List[Dict]:
        """取得已上傳的檔案列表"""
        if not os.path.exists(self.upload_dir):
            return []
        
        files = []
        for filename in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'type': 'image' if self.is_image_file(filename) else 'document',
                    'extension': os.path.splitext(filename)[1].lower().lstrip('.')
                })
        
        # 按修改時間排序（最新的在前）
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files
    
    def delete_file(self, filename: str) -> bool:
        """刪除檔案"""
        try:
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            st.error(f"刪除檔案時發生錯誤: {str(e)}")
            return False
    
    def get_file_content(self, filename: str) -> Optional[bytes]:
        """取得檔案內容"""
        try:
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            st.error(f"讀取檔案時發生錯誤: {str(e)}")
            return None
    
    def get_file_stats(self) -> Dict:
        """取得檔案統計資訊"""
        files = self.get_uploaded_files()
        
        total_files = len(files)
        total_size = sum(f['size'] for f in files)
        
        doc_files = [f for f in files if f['type'] == 'document']
        image_files = [f for f in files if f['type'] == 'image']
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'document_count': len(doc_files),
            'image_count': len(image_files),
            'document_files': doc_files,
            'image_files': image_files
        }
