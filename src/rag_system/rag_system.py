import os
from typing import List, Optional
from llama_index.core import VectorStoreIndex, Document, Settings, load_index_from_storage

# 條件性導入 streamlit，如果不可用則使用 mock
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    class MockStreamlit:
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    st = MockStreamlit()
    HAS_STREAMLIT = False
from llama_index.core.storage.storage_context import StorageContext
from llama_index.llms.groq import Groq
import requests
import numpy as np
from typing import List
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import SimpleNodeParser

# 導入新的功能模組
from ..storage.conversation_memory import ConversationMemory
from ..processors.user_file_manager import UserFileManager
from ..processors.gemini_ocr import GeminiOCRProcessor

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

from config.config import (
    GROQ_API_KEY, LLM_MODEL, INDEX_DIR, JINA_API_KEY, ELASTICSEARCH_VECTOR_DIMENSION
)

class JinaEmbeddingAPI(BaseEmbedding):
    """自定義 Jina Embedding API 類別"""
    
    def __init__(self, api_key: str, model: str = "jina-embeddings-v3", task: str = "text-matching"):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.task = task
        self.url = 'https://api.jina.ai/v1/embeddings'
        # 與 Elasticsearch 向量維度保持一致（避免維度不匹配）
        self.embed_dim = ELASTICSEARCH_VECTOR_DIMENSION
        
    def _get_text_embedding(self, text: str) -> List[float]:
        """獲取單個文本的嵌入向量"""
        return self._get_text_embeddings([text])[0]
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """獲取多個文本的嵌入向量"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            "model": self.model,
            "task": self.task,
            "truncate": True,
            "input": texts
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # 提取嵌入向量
            embeddings = []
            for item in result.get('data', []):
                embeddings.append(item.get('embedding', []))
            
            return embeddings
        except Exception as e:
            st.error(f"Jina API 調用失敗: {str(e)}")
            st.warning("⚠️ 後備方案：使用簡單的文本特徵向量（功能有限）")
            # 如果 API 失敗，使用簡單的文本特徵作為後備
            return [self._simple_text_embedding(text) for text in texts]
    
    def _simple_text_embedding(self, text: str) -> List[float]:
        """簡單的文本特徵向量（後備方案） - 與設定維度對齊"""
        import hashlib
        
        # 確保文本不為空
        if not text.strip():
            text = "empty"
        
        # 基於文本內容生成一致的特徵向量（使用 sha256，長度64的十六進制）
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        dim = getattr(self, "embed_dim", ELASTICSEARCH_VECTOR_DIMENSION)
        embedding: List[float] = []
        
        # 以8為步長生成值，直到達到指定維度
        for i in range(dim // 8):  # 每8個值為一組
            hex_start = (i * 2) % 64
            hex_val = int(text_hash[hex_start:hex_start+2], 16)
            for j in range(8):
                value = (hex_val + j * 31) % 256
                normalized = (value / 255.0) * 2 - 1  # 歸一化到 [-1, 1]
                embedding.append(normalized)
        
        # 補齊或截斷到指定維度
        while len(embedding) < dim:
            embedding.append(0.0)
        
        return embedding[:dim]
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """異步獲取文本嵌入（回退到同步方法）"""
        return self._get_text_embedding(text)
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """獲取查詢嵌入向量"""
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """異步獲取查詢嵌入向量"""
        return self._get_query_embedding(query)

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
        self.models_initialized = False
        # 延遲初始化模型，避免在頁面載入時就初始化
        
    def _setup_models(self):
        """設定模型"""
        # 設定LLM
        if GROQ_API_KEY:
            llm = Groq(model=LLM_MODEL, api_key=GROQ_API_KEY)
        else:
            st.error("請設定GROQ_API_KEY環境變數")
            return
        
        # 設定 Embedding 模型 - 總是使用我們的自定義實作
        if JINA_API_KEY and JINA_API_KEY.strip():
            st.info("🚀 使用 Jina Embedding API")
            embed_model = JinaEmbeddingAPI(
                api_key=JINA_API_KEY,
                model="jina-embeddings-v3",
                task="text-matching"
            )
        else:
            st.warning("⚠️ 未設定 JINA_API_KEY，將使用簡單特徵向量作為後備")
            st.info("💡 建議設定 JINA_API_KEY 以獲得更好的 embedding 效果")
            # 使用自定義的簡單後備方案
            embed_model = JinaEmbeddingAPI(
                api_key="dummy",  # 將會觸發後備方案
                model="jina-embeddings-v3",
                task="text-matching"
            )
        
        # 先設定 embedding 模型，再設定其他
        Settings.embed_model = embed_model
        Settings.llm = llm  
        Settings.node_parser = SimpleNodeParser.from_defaults(chunk_size=1024)
        
        # 設置標記避免 LlamaIndex 嘗試使用預設的 OpenAI embedding
        self.models_initialized = True
    
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
                # 確保模型已正確初始化
                if not self.models_initialized:
                    st.info("正在初始化模型...")
                    self._setup_models()
                    self.models_initialized = True
                
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
    
    def get_knowledge_base_summary(self) -> dict:
        """取得知識庫完整摘要"""
        if not self.index:
            return {}
        
        try:
            # 基礎統計
            stats = self.get_document_statistics()
            
            # 內容主題分析
            topics = self.analyze_content_topics()
            
            # 建議問題
            suggested_questions = self.generate_suggested_questions()
            
            return {
                "statistics": stats,
                "topics": topics,
                "suggested_questions": suggested_questions,
                "last_updated": os.path.getmtime(INDEX_DIR) if os.path.exists(INDEX_DIR) else None
            }
        except Exception as e:
            st.error(f"取得知識庫摘要時發生錯誤: {str(e)}")
            return {}
    
    def get_document_statistics(self) -> dict:
        """取得文件統計資訊"""
        if not self.index:
            return {}
        
        stats = {
            "total_documents": 0,
            "total_nodes": 0,
            "document_details": [],
            "total_pages": 0
        }
        
        # 統計文件資訊
        doc_info = {}
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
        
        return stats
    
    def analyze_content_topics(self) -> List[dict]:
        """分析內容主題"""
        if not self.index:
            return []
        
        # 返回預設主題分類
        return [
            {
                "name": "茶樹品種",
                "description": "台灣茶樹品種介紹與特性分析",
                "keywords": ["品種", "茶樹", "特性", "適應性"],
                "icon": "🌱"
            },
            {
                "name": "栽培技術", 
                "description": "茶園管理與栽培技術要點",
                "keywords": ["栽培", "管理", "施肥", "病蟲害"],
                "icon": "🌿"
            },
            {
                "name": "製茶工藝",
                "description": "各類茶葉製作工藝與流程", 
                "keywords": ["製茶", "發酵", "烘焙", "工藝"],
                "icon": "🍃"
            },
            {
                "name": "品質評鑑",
                "description": "茶葉品質檢驗與感官評鑑",
                "keywords": ["品質", "評鑑", "檢驗", "標準"],
                "icon": "🎯"
            }
        ]
    
    def generate_suggested_questions(self) -> List[str]:
        """生成建議問題"""
        return [
            "台灣的茶樹品種？",
            "製茶的流程包含哪些步驟？",
            "茶葉的感官品質評鑑怎麼做？",
            "茶園栽培管理有哪些重點？",
            "不同茶類的製作工藝？",
            "茶葉品質檢驗的標準是什麼？",
            "台灣茶業的發展歷史如何？",
            "茶樹病蟲害防治方法有哪些？"
        ]
