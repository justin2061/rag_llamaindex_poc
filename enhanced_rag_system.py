import os
from typing import List, Optional, Dict, Any
import streamlit as st
from llama_index.core import VectorStoreIndex, Document

from rag_system import RAGSystem
from conversation_memory import ConversationMemory
from user_file_manager import UserFileManager
from gemini_ocr import GeminiOCRProcessor

class EnhancedRAGSystem(RAGSystem):
    def __init__(self):
        super().__init__()
        
        # 初始化新功能模組
        self.memory = ConversationMemory()
        self.file_manager = UserFileManager()
        self.ocr_processor = GeminiOCRProcessor()
        
    def query_with_context(self, question: str) -> str:
        """帶上下文記憶的查詢"""
        if not self.query_engine:
            return "系統尚未初始化，請先載入文件。"
        
        try:
            # 建構包含歷史對話的完整查詢
            context_prompt = self.memory.get_context_prompt()
            
            if context_prompt and self.memory.is_enabled():
                enhanced_question = f"""
{context_prompt}

當前問題: {question}

請基於以上對話歷史和知識庫內容回答當前問題。如果當前問題與之前的對話相關，請考慮上下文語境。
"""
            else:
                enhanced_question = question
            
            with st.spinner("正在思考您的問題..."):
                response = self.query_engine.query(enhanced_question)
                response_str = str(response)
                
                # 將這輪對話加入記憶
                self.memory.add_exchange(question, response_str)
                
                return response_str
                
        except Exception as e:
            st.error(f"查詢時發生錯誤: {str(e)}")
            return "抱歉，處理您的問題時發生錯誤。"
    
    def process_uploaded_files(self, uploaded_files) -> List[Document]:
        """處理上傳的檔案"""
        if not uploaded_files:
            return []
        
        documents = []
        
        for uploaded_file in uploaded_files:
            try:
                # 儲存檔案
                file_path = self.file_manager.save_uploaded_file(uploaded_file)
                if not file_path:
                    continue
                
                # 根據檔案類型處理
                if self.file_manager.is_image_file(uploaded_file.name):
                    # 圖片OCR處理
                    doc = self._process_image_file(uploaded_file, file_path)
                elif self.file_manager.is_document_file(uploaded_file.name):
                    # 文檔處理
                    doc = self._process_document_file(uploaded_file, file_path)
                else:
                    st.warning(f"不支援的檔案類型: {uploaded_file.name}")
                    continue
                
                if doc:
                    documents.append(doc)
                    
            except Exception as e:
                st.error(f"處理檔案 {uploaded_file.name} 時發生錯誤: {str(e)}")
                continue
        
        return documents
    
    def _process_image_file(self, uploaded_file, file_path: str) -> Optional[Document]:
        """處理圖片檔案"""
        if not self.ocr_processor.is_available():
            st.warning(f"OCR服務不可用，跳過圖片檔案: {uploaded_file.name}")
            return None
        
        try:
            # 讀取圖片數據
            image_data = self.file_manager.get_file_content(os.path.basename(file_path))
            if not image_data:
                return None
            
            # 取得檔案擴展名
            file_ext = os.path.splitext(uploaded_file.name)[1].lower().lstrip('.')
            
            # OCR處理
            with st.spinner(f"正在進行OCR處理: {uploaded_file.name}"):
                ocr_result = self.ocr_processor.extract_text_from_image(image_data, file_ext)
            
            if ocr_result['success']:
                # 建立文檔
                document = Document(
                    text=ocr_result['text'],
                    metadata={
                        "source": uploaded_file.name,
                        "type": "image_ocr",
                        "original_format": file_ext,
                        "file_size": uploaded_file.size,
                        "ocr_confidence": ocr_result.get('confidence', 'unknown'),
                        "processed_at": st.session_state.get('current_time', 'unknown')
                    }
                )
                
                st.success(f"✅ OCR處理成功: {uploaded_file.name}")
                return document
            else:
                st.error(f"❌ OCR處理失敗: {uploaded_file.name} - {ocr_result['error']}")
                return None
                
        except Exception as e:
            st.error(f"處理圖片檔案時發生錯誤: {str(e)}")
            return None
    
    def _process_document_file(self, uploaded_file, file_path: str) -> Optional[Document]:
        """處理文檔檔案"""
        try:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext == '.pdf':
                # PDF處理
                docs = self.load_pdfs([file_path])
                if docs:
                    doc = docs[0]
                    # 更新元數據
                    doc.metadata.update({
                        "type": "user_document",
                        "file_size": uploaded_file.size,
                        "uploaded_at": st.session_state.get('current_time', 'unknown')
                    })
                    return doc
            
            elif file_ext == '.txt':
                # 文字檔處理
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                document = Document(
                    text=text,
                    metadata={
                        "source": uploaded_file.name,
                        "type": "user_document",
                        "original_format": "txt",
                        "file_size": uploaded_file.size,
                        "uploaded_at": st.session_state.get('current_time', 'unknown')
                    }
                )
                return document
            
            elif file_ext in ['.md', '.markdown']:
                # Markdown檔處理
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                document = Document(
                    text=text,
                    metadata={
                        "source": uploaded_file.name,
                        "type": "user_document",
                        "original_format": "markdown",
                        "file_size": uploaded_file.size,
                        "uploaded_at": st.session_state.get('current_time', 'unknown')
                    }
                )
                return document
            
            else:
                st.warning(f"暫不支援的文檔格式: {file_ext}")
                return None
                
        except Exception as e:
            st.error(f"處理文檔檔案時發生錯誤: {str(e)}")
            return None
    
    def rebuild_index_with_user_files(self) -> bool:
        """重建索引，包含用戶上傳的檔案"""
        try:
            all_documents = []
            
            # 載入官方茶葉資料
            from enhanced_pdf_downloader import EnhancedPDFDownloader
            downloader = EnhancedPDFDownloader()
            official_pdfs = downloader.get_existing_pdfs()
            
            if official_pdfs:
                st.info("載入官方茶葉資料...")
                official_docs = self.load_pdfs(official_pdfs)
                # 標記為官方資料
                for doc in official_docs:
                    doc.metadata["data_source"] = "official"
                all_documents.extend(official_docs)
            
            # 載入用戶上傳的檔案
            user_files = self.file_manager.get_uploaded_files()
            if user_files:
                st.info("載入用戶上傳的檔案...")
                
                # 模擬uploaded_file對象來重用現有邏輯
                class MockUploadedFile:
                    def __init__(self, file_info):
                        self.name = file_info['name']
                        self.size = file_info['size']
                
                mock_files = [MockUploadedFile(f) for f in user_files]
                user_docs = []
                
                for i, file_info in enumerate(user_files):
                    if file_info['type'] == 'image':
                        doc = self._process_image_file(mock_files[i], file_info['path'])
                    else:
                        doc = self._process_document_file(mock_files[i], file_info['path'])
                    
                    if doc:
                        doc.metadata["data_source"] = "user_upload"
                        user_docs.append(doc)
                
                all_documents.extend(user_docs)
            
            if all_documents:
                # 重建索引
                st.info("重建向量索引...")
                index = self.create_index(all_documents)
                
                if index:
                    self.setup_query_engine()
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"重建索引時發生錯誤: {str(e)}")
            return False
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """取得增強的統計資訊"""
        base_stats = self.get_document_statistics()
        
        # 用戶檔案統計
        file_stats = self.file_manager.get_file_stats()
        
        # 對話記憶統計
        memory_stats = self.memory.get_memory_stats()
        
        # OCR可用性
        ocr_available = self.ocr_processor.is_available()
        
        return {
            "base_statistics": base_stats,
            "user_files": file_stats,
            "conversation_memory": memory_stats,
            "ocr_available": ocr_available,
            "total_data_sources": {
                "official_documents": base_stats.get("total_documents", 0) - file_stats.get("total_files", 0),
                "user_documents": file_stats.get("document_count", 0),
                "user_images": file_stats.get("image_count", 0)
            }
        }
    
    def clear_conversation_memory(self):
        """清除對話記憶"""
        self.memory.clear_memory()
    
    def get_memory_for_display(self):
        """取得用於顯示的記憶內容"""
        return self.memory.get_memory_for_display()
    
    def delete_user_file(self, filename: str) -> bool:
        """刪除用戶檔案"""
        return self.file_manager.delete_file(filename)
