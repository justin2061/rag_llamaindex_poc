import os
from typing import List, Optional
import streamlit as st
from llama_index.core import VectorStoreIndex, Document, Settings, load_index_from_storage
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SimpleNodeParser

# 嘗試導入不同的PDF處理庫
PDF_READER = None
PDF_READER_TYPE = None

try:
    from llama_index.readers.file import PyMuPDFReader
    PDF_READER = PyMuPDFReader()
    PDF_READER_TYPE = "PyMuPDF"
except ImportError:
    try:
        import PyPDF2
        PDF_READER_TYPE = "PyPDF2"
    except ImportError:
        try:
            import pdfplumber
            PDF_READER_TYPE = "pdfplumber"
        except ImportError:
            st.error("沒有找到可用的PDF處理庫，請安裝 PyMuPDF、PyPDF2 或 pdfplumber")

from config import GROQ_API_KEY, EMBEDDING_MODEL, LLM_MODEL, INDEX_DIR

def load_pdf_with_pypdf2(pdf_path: str) -> List[Document]:
    """使用PyPDF2載入PDF"""
    import PyPDF2
    documents = []
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            text += page.extract_text() + "\n"
        
        doc = Document(
            text=text,
            metadata={"source": os.path.basename(pdf_path), "pages": len(pdf_reader.pages)}
        )
        documents.append(doc)
    
    return documents

def load_pdf_with_pdfplumber(pdf_path: str) -> List[Document]:
    """使用pdfplumber載入PDF"""
    import pdfplumber
    documents = []
    
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        doc = Document(
            text=text,
            metadata={"source": os.path.basename(pdf_path), "pages": len(pdf.pages)}
        )
        documents.append(doc)
    
    return documents

class RAGSystem:
    def __init__(self):
        self.index = None
        self.query_engine = None
        self._setup_models()
        
    def _setup_models(self):
        """設定模型"""
        # 設定LLM
        if GROQ_API_KEY:
            llm = Groq(model=LLM_MODEL, api_key=GROQ_API_KEY)
        else:
            st.error("請設定GROQ_API_KEY環境變數")
            return
        
        # 設定嵌入模型
        embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
        
        # 設定全域配置
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.node_parser = SimpleNodeParser.from_defaults(chunk_size=1024)
    
    def load_pdfs(self, pdf_paths: List[str]) -> List[Document]:
        """載入PDF檔案 - 支援多種PDF處理庫"""
        documents = []
        
        # 顯示使用的PDF處理庫
        st.info(f"使用 {PDF_READER_TYPE} 處理PDF檔案")
        
        with st.spinner("正在載入PDF檔案..."):
            for pdf_path in pdf_paths:
                try:
                    if PDF_READER_TYPE == "PyMuPDF":
                        docs = PDF_READER.load_data(file_path=pdf_path)
                        # 為每個文件添加元數據
                        for doc in docs:
                            doc.metadata["source"] = os.path.basename(pdf_path)
                        documents.extend(docs)
                    
                    elif PDF_READER_TYPE == "PyPDF2":
                        docs = load_pdf_with_pypdf2(pdf_path)
                        documents.extend(docs)
                    
                    elif PDF_READER_TYPE == "pdfplumber":
                        docs = load_pdf_with_pdfplumber(pdf_path)
                        documents.extend(docs)
                    
                    else:
                        st.error("沒有可用的PDF處理庫")
                        return []
                    
                    st.info(f"成功載入: {os.path.basename(pdf_path)}")
                except Exception as e:
                    st.error(f"載入 {os.path.basename(pdf_path)} 時發生錯誤: {str(e)}")
        
        return documents
    
    def load_existing_index(self) -> bool:
        """載入現有的向量索引"""
        try:
            if os.path.exists(INDEX_DIR) and os.listdir(INDEX_DIR):
                with st.spinner("正在載入現有索引..."):
                    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
                    self.index = load_index_from_storage(storage_context)
                    self.setup_query_engine()
                    st.success("✅ 成功載入現有索引")
                    return True
            else:
                return False
        except Exception as e:
            st.error(f"載入索引時發生錯誤: {str(e)}")
            return False
    
    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """建立新的向量索引"""
        with st.spinner("正在建立向量索引..."):
            try:
                # 建立新索引
                index = VectorStoreIndex.from_documents(documents)
                # 儲存索引
                index.storage_context.persist(persist_dir=INDEX_DIR)
                st.success("✅ 成功建立新索引")
                
                self.index = index
                return index
            except Exception as e:
                st.error(f"建立索引時發生錯誤: {str(e)}")
                return None
    
    def setup_query_engine(self):
        """設定查詢引擎"""
        if self.index:
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                response_mode="compact"
            )
    
    def query(self, question: str) -> str:
        """執行查詢"""
        if not self.query_engine:
            return "系統尚未初始化，請先載入文件。"
        
        try:
            with st.spinner("正在思考您的問題..."):
                response = self.query_engine.query(question)
                return str(response)
        except Exception as e:
            st.error(f"查詢時發生錯誤: {str(e)}")
            return "抱歉，處理您的問題時發生錯誤。"
    
    def get_source_info(self) -> List[str]:
        """取得資料來源資訊"""
        if not self.index:
            return []
        
        sources = set()
        for node in self.index.docstore.docs.values():
            if "source" in node.metadata:
                sources.add(node.metadata["source"])
        
        return list(sources)
