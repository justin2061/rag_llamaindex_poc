import os
from typing import List, Optional, Dict, Any
import streamlit as st
from llama_index.core import VectorStoreIndex, Document

# Elasticsearch 支援
try:
    from elasticsearch import Elasticsearch
    from llama_index.vector_stores.elasticsearch import ElasticsearchStore
    from llama_index.core.storage.storage_context import StorageContext
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

from .rag_system import RAGSystem
from ..storage.conversation_memory import ConversationMemory
from ..processors.user_file_manager import UserFileManager
from ..processors.gemini_ocr import GeminiOCRProcessor
from ..utils.embedding_fix import setup_safe_embedding, prevent_openai_fallback
from ..utils.immediate_fix import setup_immediate_fix
# from chroma_vector_store import ChromaVectorStoreManager  # 已改用 Elasticsearch

class EnhancedRAGSystem(RAGSystem):
    def __init__(self, use_elasticsearch: bool = True, use_chroma: bool = False):
        super().__init__()
        
        # 初始化新功能模組
        self.memory = ConversationMemory()
        self.file_manager = UserFileManager()
        self.ocr_processor = GeminiOCRProcessor()
        
        # 優先使用 Elasticsearch，停用 ChromaDB
        self.use_elasticsearch = use_elasticsearch
        self.use_chroma = False  # 強制停用 ChromaDB
        self.chroma_manager = None  # 不再使用 ChromaDB
        
        # Elasticsearch 設定
        self.elasticsearch_client = None
        self.elasticsearch_store = None
        
        # 如果啟用 Elasticsearch，嘗試初始化
        if self.use_elasticsearch and ELASTICSEARCH_AVAILABLE:
            self._initialize_elasticsearch()
    
    def _initialize_elasticsearch(self):
        """初始化 Elasticsearch 連接"""
        try:
            from config import (
                ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_SCHEME,
                ELASTICSEARCH_INDEX_NAME, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD,
                ELASTICSEARCH_TIMEOUT, ELASTICSEARCH_MAX_RETRIES, ELASTICSEARCH_VERIFY_CERTS,
                ELASTICSEARCH_VECTOR_DIMENSION
            )
            
            # 建立 Elasticsearch 客戶端
            es_config = {
                'hosts': [f'{ELASTICSEARCH_SCHEME}://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}'],
                'verify_certs': ELASTICSEARCH_VERIFY_CERTS,
                'ssl_show_warn': False,
                'timeout': ELASTICSEARCH_TIMEOUT,
                'max_retries': ELASTICSEARCH_MAX_RETRIES,
                'retry_on_timeout': True
            }
            
            if ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD:
                es_config['basic_auth'] = (ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD)
            
            self.elasticsearch_client = Elasticsearch(**es_config)
            
            # 檢查連接
            if self.elasticsearch_client.ping():
                st.info("✅ Elasticsearch 連接成功")
                
                # 建立 vector store
                self.elasticsearch_store = ElasticsearchStore(
                    es_client=self.elasticsearch_client,
                    index_name=ELASTICSEARCH_INDEX_NAME,
                    vector_field="embedding",
                    text_field="content",
                    embedding_dim=ELASTICSEARCH_VECTOR_DIMENSION,
                )
                return True
            else:
                st.warning("⚠️ 無法連接到 Elasticsearch，將使用 SimpleVectorStore")
                self.use_elasticsearch = False
                return False
                
        except Exception as e:
            st.warning(f"⚠️ Elasticsearch 初始化失敗: {str(e)}，將使用 SimpleVectorStore")
            self.use_elasticsearch = False
            return False
    
    def _ensure_models_initialized(self):
        """確保模型已初始化"""
        if not self.models_initialized:
            self._setup_models()
            self.models_initialized = True
    
    def _setup_models(self):
        """設定模型 - 覆寫父類方法以確保正確初始化"""
        from config import GROQ_API_KEY, LLM_MODEL, JINA_API_KEY
        from llama_index.llms.groq import Groq
        from llama_index.core.node_parser import SimpleNodeParser
        from llama_index.core import Settings
        import streamlit as st
        
        # 防止 OpenAI 回退並設置安全的嵌入模型
        prevent_openai_fallback()
        
        # 設定LLM
        if GROQ_API_KEY:
            llm = Groq(model=LLM_MODEL, api_key=GROQ_API_KEY)
        else:
            st.error("請設定GROQ_API_KEY環境變數")
            return
        
        # 設定安全嵌入模型 - 使用立即修復方案
        try:
            # 先嘗試立即修復方案
            embed_model = setup_immediate_fix()
            st.success("✅ 成功初始化嵌入模型（立即修復版本）")
        except Exception as e:
            st.warning(f"立即修復失敗: {str(e)}，嘗試原始方案")
            try:
                embed_model = setup_safe_embedding(JINA_API_KEY)
                st.success("✅ 成功初始化嵌入模型")
            except Exception as e2:
                st.error(f"嵌入模型初始化失敗: {str(e2)}")
                return
        
        # 設定全域配置
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.node_parser = SimpleNodeParser.from_defaults(chunk_size=1024)
        
        st.success("🔧 模型初始化完成")
        
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
            
            elif file_ext == '.docx':
                # DOCX檔處理
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    
                    document = Document(
                        text=text,
                        metadata={
                            "source": uploaded_file.name,
                            "type": "user_document",
                            "original_format": "docx",
                            "file_size": uploaded_file.size,
                            "uploaded_at": st.session_state.get('current_time', 'unknown')
                        }
                    )
                    return document
                    
                except ImportError:
                    st.error("需要安裝 python-docx 套件來處理 DOCX 檔案")
                    return None
                except Exception as e:
                    st.error(f"DOCX 檔案處理失敗: {str(e)}")
                    return None
            
            else:
                st.warning(f"暫不支援的文檔格式: {file_ext}")
                return None
                
        except Exception as e:
            st.error(f"處理文檔檔案時發生錯誤: {str(e)}")
            return None
    
    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """建立新的向量索引 (優先使用 Elasticsearch)"""
        with st.spinner("正在建立向量索引..."):
            # 確保模型已正確初始化
            self._ensure_models_initialized()
            
            index = None
            
            try:
                # 優先使用 Elasticsearch
                if self.use_elasticsearch and self.elasticsearch_store:
                    st.info("使用 Elasticsearch 建立索引...")
                    try:
                        # 建立 storage context
                        storage_context = StorageContext.from_defaults(
                            vector_store=self.elasticsearch_store
                        )
                        
                        # 創建索引
                        index = VectorStoreIndex.from_documents(
                            documents, 
                            storage_context=storage_context
                        )
                        st.success("✅ 成功使用 Elasticsearch 建立索引")
                        
                    except Exception as e:
                        st.warning(f"Elasticsearch 索引創建失敗: {str(e)}")
                        st.info("回退到 SimpleVectorStore...")
                        self.use_elasticsearch = False
                
                # 如果 Elasticsearch 失敗或未啟用，使用 SimpleVectorStore
                if not self.use_elasticsearch:
                    st.info("使用 SimpleVectorStore 建立索引...")
                    index = VectorStoreIndex.from_documents(documents)
                    st.success("✅ 成功使用 SimpleVectorStore 建立索引")
                    
                    # 持久化索引
                    from config import INDEX_DIR
                    index.storage_context.persist(persist_dir=INDEX_DIR)
                    st.success("✅ 索引已持久化保存")
                
                if index:
                    self.index = index
                    return index
                else:
                    st.error("索引創建失敗")
                    return None
                    
            except Exception as e:
                st.error(f"建立索引時發生未預期錯誤: {str(e)}")
                return None
    
    def load_existing_index(self) -> bool:
        """載入現有的向量索引 (優先使用 Elasticsearch)"""
        # 確保模型已初始化
        self._ensure_models_initialized()
        
        try:
            # 優先嘗試 Elasticsearch
            if self.use_elasticsearch and self.elasticsearch_store:
                st.info("嘗試從 Elasticsearch 載入索引...")
                try:
                    # 檢查 Elasticsearch 是否有資料
                    es_stats = self.elasticsearch_client.indices.stats(
                        index=self.elasticsearch_store.index_name
                    )
                    doc_count = es_stats['indices'][self.elasticsearch_store.index_name]['total']['docs']['count']
                    
                    if doc_count > 0:
                        # 從 Elasticsearch 重建索引
                        storage_context = StorageContext.from_defaults(
                            vector_store=self.elasticsearch_store
                        )
                        self.index = VectorStoreIndex.from_vector_store(
                            vector_store=self.elasticsearch_store,
                            storage_context=storage_context
                        )
                        self.setup_query_engine()
                        st.success(f"✅ 成功從 Elasticsearch 載入 {doc_count} 個文檔")
                        return True
                    else:
                        st.info("Elasticsearch 索引為空")
                        
                except Exception as e:
                    st.warning(f"Elasticsearch 載入失敗: {str(e)}")
                    self.use_elasticsearch = False
            
            # 回退到 SimpleVectorStore
            from config import INDEX_DIR
            if os.path.exists(INDEX_DIR) and os.listdir(INDEX_DIR):
                st.info("嘗試從 SimpleVectorStore 載入索引...")
                try:
                    from llama_index.core import load_index_from_storage
                    from llama_index.core.storage.storage_context import StorageContext
                    
                    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
                    self.index = load_index_from_storage(storage_context)
                    self.setup_query_engine()
                    st.success("✅ 成功載入現有索引 (SimpleVectorStore)")
                    return True
                    
                except Exception as e:
                    st.error(f"載入 SimpleVectorStore 失敗: {str(e)}")
                    return False
            else:
                st.info("沒有找到現有索引檔案")
                return False
                
        except Exception as e:
            st.error(f"載入索引時發生未預期錯誤: {str(e)}")
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
        """取得文件統計資訊 (支援 Elasticsearch 和 SimpleVectorStore)"""
        if not self.index:
            return {}
        
        stats = {
            "total_documents": 0,
            "total_nodes": 0,
            "document_details": [],
            "total_pages": 0
        }
        
        try:
            if self.use_elasticsearch and self.elasticsearch_client:
                # 使用 Elasticsearch 統計
                try:
                    from config import ELASTICSEARCH_INDEX_NAME
                    index_name = ELASTICSEARCH_INDEX_NAME or 'rag_intelligent_assistant'
                    
                    es_stats = self.elasticsearch_client.indices.stats(
                        index=index_name
                    )
                    doc_count = es_stats['indices'][index_name]['total']['docs']['count']
                    index_size = es_stats['indices'][index_name]['total']['store']['size_in_bytes']
                    
                    stats["total_documents"] = doc_count
                    stats["total_nodes"] = doc_count
                    stats["index_size_bytes"] = index_size
                    stats["index_size_mb"] = round(index_size / 1024 / 1024, 2)
                    
                    # 從 Elasticsearch 獲取文檔類型統計
                    search_result = self.elasticsearch_client.search(
                        index=index_name,
                        body={
                            "size": 0,
                            "aggs": {
                                "source_types": {
                                    "terms": {
                                        "field": "metadata.source.keyword",
                                        "size": 100
                                    }
                                }
                            }
                        }
                    )
                    
                    source_buckets = search_result.get('aggregations', {}).get('source_types', {}).get('buckets', [])
                    for bucket in source_buckets:
                        stats["document_details"].append({
                            "name": bucket['key'],
                            "pages": bucket['doc_count'],
                            "node_count": bucket['doc_count']
                        })
                    
                    st.info(f"📊 從 Elasticsearch 獲取統計: {stats['total_documents']} 個文檔")
                    
                except Exception as es_e:
                    st.warning(f"無法從 Elasticsearch 獲取統計資訊: {str(es_e)}")
                    # 回退到 SimpleVectorStore 統計
                    return self._get_simple_vector_store_stats()
            else:
                # 使用 SimpleVectorStore 統計
                return self._get_simple_vector_store_stats()
            
        except Exception as e:
            st.error(f"獲取文檔統計時發生錯誤: {str(e)}")
        
        return stats
    
    def _get_simple_vector_store_stats(self) -> dict:
        """獲取 SimpleVectorStore 統計資訊"""
        stats = {
            "total_documents": 0,
            "total_nodes": 0,
            "document_details": [],
            "total_pages": 0
        }
        
        try:
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
            st.error(f"獲取 SimpleVectorStore 統計時發生錯誤: {str(e)}")
        
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
