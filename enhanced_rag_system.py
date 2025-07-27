import os
from typing import List, Optional, Dict, Any
import streamlit as st
from llama_index.core import VectorStoreIndex, Document

from rag_system import RAGSystem
from conversation_memory import ConversationMemory
from user_file_manager import UserFileManager
from gemini_ocr import GeminiOCRProcessor
from chroma_vector_store import ChromaVectorStoreManager

class EnhancedRAGSystem(RAGSystem):
    def __init__(self, use_chroma: bool = True):
        super().__init__()
        
        # 初始化新功能模組
        self.memory = ConversationMemory()
        self.file_manager = UserFileManager()
        self.ocr_processor = GeminiOCRProcessor()
        self.chroma_manager = ChromaVectorStoreManager() if use_chroma else None
        self.use_chroma = use_chroma
        
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
    
    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """建立新的向量索引 (支援 ChromaDB)"""
        with st.spinner("正在建立向量索引..."):
            chroma_success = False
            index = None
            
            try:
                if self.use_chroma and self.chroma_manager:
                    # 嘗試使用 ChromaDB
                    st.info("嘗試使用 ChromaDB 向量儲存...")
                    try:
                        # 初始化 ChromaDB 客戶端
                        if self.chroma_manager.initialize_client():
                            # 獲取 ChromaDB 儲存上下文
                            storage_context = self.chroma_manager.get_storage_context()
                            if storage_context:
                                # 創建索引
                                index = VectorStoreIndex.from_documents(
                                    documents, 
                                    storage_context=storage_context
                                )
                                st.success("✅ 成功使用 ChromaDB 建立索引")
                                chroma_success = True
                            else:
                                st.warning("無法獲取 ChromaDB 儲存上下文，回退到 SimpleVectorStore")
                        else:
                            st.warning("ChromaDB 客戶端初始化失敗，回退到 SimpleVectorStore")
                    except Exception as e:
                        st.warning(f"ChromaDB 索引創建失敗: {str(e)}")
                        st.info("正在回退到 SimpleVectorStore...")
                
                # 如果 ChromaDB 失敗或未啟用，使用 SimpleVectorStore
                if not chroma_success:
                    try:
                        st.info("使用 SimpleVectorStore 建立索引...")
                        index = VectorStoreIndex.from_documents(documents)
                        st.success("✅ 成功使用 SimpleVectorStore 建立索引")
                        # 停用 ChromaDB 避免後續衝突
                        self.use_chroma = False
                    except Exception as e:
                        st.error(f"SimpleVectorStore 索引創建也失敗: {str(e)}")
                        return None
                
                if index:
                    # 持久化索引
                    from config import INDEX_DIR
                    index.storage_context.persist(persist_dir=INDEX_DIR)
                    st.success("✅ 索引已持久化保存")
                    
                    self.index = index
                    return index
                else:
                    st.error("索引創建失敗")
                    return None
                    
            except Exception as e:
                st.error(f"建立索引時發生未預期錯誤: {str(e)}")
                return None
    
    def load_existing_index(self) -> bool:
        """載入現有的向量索引 (支援 ChromaDB 智能遷移)"""
        try:
            from config import INDEX_DIR
            if os.path.exists(INDEX_DIR) and os.listdir(INDEX_DIR):
                with st.spinner("正在載入現有索引..."):
                    
                    if self.use_chroma and self.chroma_manager:
                        # 檢查 ChromaDB 是否有資料
                        if self.chroma_manager.has_data():
                            # ChromaDB 有資料，直接載入
                            st.info("發現 ChromaDB 資料，正在載入...")
                            return self._load_chromadb_index()
                        else:
                            # ChromaDB 是空的，嘗試從 SimpleVectorStore 遷移
                            st.info("ChromaDB 是空的，嘗試從 SimpleVectorStore 遷移...")
                            return self._load_and_migrate_from_simple()
                    else:
                        # 直接載入 SimpleVectorStore
                        return self._load_simple_vector_store()
            else:
                st.info("沒有找到現有索引檔案")
                return False
        except Exception as e:
            st.error(f"載入索引時發生未預期錯誤: {str(e)}")
            return False
    
    def _load_chromadb_index(self) -> bool:
        """載入 ChromaDB 索引"""
        try:
            storage_context = self.chroma_manager.get_storage_context()
            if storage_context:
                from llama_index.core import load_index_from_storage
                self.index = load_index_from_storage(storage_context)
                self.setup_query_engine()
                st.success("✅ 成功載入 ChromaDB 索引")
                return True
            else:
                st.warning("無法獲取 ChromaDB 儲存上下文")
                return False
        except Exception as e:
            st.warning(f"載入 ChromaDB 索引失敗: {str(e)}")
            return False
    
    def _load_and_migrate_from_simple(self) -> bool:
        """從 SimpleVectorStore 載入並遷移到 ChromaDB"""
        try:
            # 先嘗試載入 SimpleVectorStore
            if self._load_simple_vector_store(migrate_to_chroma=False):
                st.info("SimpleVectorStore 載入成功，開始遷移到 ChromaDB...")
                
                # 取得當前的文檔
                documents = []
                if hasattr(self.index, 'docstore') and self.index.docstore.docs:
                    for node_id, node in self.index.docstore.docs.items():
                        documents.append(node)
                
                if documents:
                    # 使用 ChromaDB 重建索引
                    storage_context = self.chroma_manager.get_storage_context()
                    if storage_context:
                        new_index = VectorStoreIndex.from_documents(
                            documents, 
                            storage_context=storage_context
                        )
                        
                        # 持久化到 INDEX_DIR
                        from config import INDEX_DIR
                        new_index.storage_context.persist(persist_dir=INDEX_DIR)
                        
                        # 更新索引和查詢引擎
                        self.index = new_index
                        self.setup_query_engine()
                        
                        st.success(f"✅ 成功遷移 {len(documents)} 個文檔到 ChromaDB")
                        return True
                    else:
                        st.error("無法獲取 ChromaDB 儲存上下文進行遷移")
                        # 保持 SimpleVectorStore
                        self.use_chroma = False
                        return True
                else:
                    st.warning("沒有找到可遷移的文檔")
                    return True
            else:
                st.warning("無法載入 SimpleVectorStore 進行遷移")
                return False
                
        except Exception as e:
            st.error(f"遷移過程發生錯誤: {str(e)}")
            # 嘗試回退到 SimpleVectorStore
            return self._load_simple_vector_store(migrate_to_chroma=False)
    
    def _load_simple_vector_store(self, migrate_to_chroma: bool = True) -> bool:
        """載入 SimpleVectorStore"""
        try:
            st.info("載入 SimpleVectorStore 索引...")
            from llama_index.core import load_index_from_storage
            from llama_index.core.storage.storage_context import StorageContext
            from config import INDEX_DIR
            
            storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
            self.index = load_index_from_storage(storage_context)
            self.setup_query_engine()
            
            if migrate_to_chroma:
                st.success("✅ 成功載入現有索引 (SimpleVectorStore)")
                # 暫時停用 ChromaDB 以避免後續衝突
                self.use_chroma = False
            
            return True
            
        except Exception as e:
            st.error(f"載入 SimpleVectorStore 失敗: {str(e)}")
            return False

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
    
    def get_document_statistics(self) -> dict:
        """取得文件統計資訊 (支援 ChromaDB)"""
        if not self.index:
            return {}
        
        stats = {
            "total_documents": 0,
            "total_nodes": 0,
            "document_details": [],
            "total_pages": 0
        }
        
        try:
            if self.use_chroma and self.chroma_manager and self.chroma_manager.has_data():
                # 使用 ChromaDB 統計
                chroma_stats = self.chroma_manager.get_collection_stats()
                if chroma_stats:
                    stats["total_documents"] = chroma_stats.get("total_documents", 0)
                    stats["total_nodes"] = chroma_stats.get("total_documents", 0)  # ChromaDB 中每個文檔對應一個節點
                    
                    # 從 ChromaDB 元數據統計文檔詳情
                    source_types = chroma_stats.get("source_types", {})
                    for doc_type, count in source_types.items():
                        stats["document_details"].append({
                            "name": f"{doc_type} 文檔",
                            "pages": count,  # 暫時用文檔數量代替頁數
                            "node_count": count
                        })
                    
                    st.info(f"📊 從 ChromaDB 獲取統計: {stats['total_documents']} 個文檔")
                else:
                    st.warning("無法從 ChromaDB 獲取統計資訊")
            else:
                # 使用 SimpleVectorStore 統計（原有邏輯）
                doc_info = {}
                if hasattr(self.index, 'docstore') and self.index.docstore.docs:
                    for node in self.index.docstore.docs.values():
                        source = node.metadata.get("source", "未知")
                        pages = node.metadata.get("pages", 1)
                        
                        if source not in doc_info:
                            doc_info[source] = {
                                "name": source,
                                "pages": pages,
                                "node_count": 0
                            }
                        doc_info[source]["node_count"] += 1
                    
                    stats["total_documents"] = len(doc_info)
                    stats["total_nodes"] = len(self.index.docstore.docs)
                    stats["document_details"] = list(doc_info.values())
                    stats["total_pages"] = sum(doc["pages"] for doc in doc_info.values())
                    
                    st.info(f"📊 從 SimpleVectorStore 獲取統計: {stats['total_documents']} 個文檔")
                else:
                    st.warning("索引中沒有找到文檔資料")
            
        except Exception as e:
            st.error(f"獲取文檔統計時發生錯誤: {str(e)}")
        
        return stats
    
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
