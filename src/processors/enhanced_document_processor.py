"""
Enhanced Document Processor
增強的文檔處理器，實現智能切割和結構識別
"""

import re
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
import logging

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentStructure:
    """文檔結構信息"""
    content_type: str  # title, paragraph, list, table, etc.
    semantic_level: int  # 1=標題, 2=段落, 3=句子
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    hierarchy_path: Optional[str] = None

@dataclass
class ChunkInfo:
    """切割塊信息"""
    content: str
    structure: DocumentStructure
    chunk_index: int
    total_chunks: int
    strategy_type: str
    chunk_size: int
    chunk_overlap: int
    parent_chunk_id: Optional[str] = None

class EnhancedDocumentProcessor:
    """增強的文檔處理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 從配置導入設定
        from config.config import (
            CHUNK_SIZE, CHUNK_OVERLAP, 
            ENABLE_HIERARCHICAL_CHUNKING,
            ENABLE_DOCUMENT_STRUCTURE_DETECTION,
            CHUNK_STRATEGIES
        )
        
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        self.enable_hierarchical = ENABLE_HIERARCHICAL_CHUNKING
        self.enable_structure_detection = ENABLE_DOCUMENT_STRUCTURE_DETECTION
        self.chunk_strategies = CHUNK_STRATEGIES
        
        # 文檔結構識別正則表達式
        self.structure_patterns = {
            'chapter': [
                r'^第[一二三四五六七八九十\d]+章[：:\s]',
                r'^第[一二三四五六七八九十\d]+篇[：:\s]',
                r'^Chapter\s*\d+',
                r'^\d+\.\s*[^\d]',
            ],
            'section': [
                r'^\d+\.\d+\s*[^\d]',
                r'^第[一二三四五六七八九十\d]+節[：:\s]',
                r'^§\s*\d+',
            ],
            'subsection': [
                r'^\d+\.\d+\.\d+\s*[^\d]',
                r'^\([一二三四五六七八九十\d]+\)',
                r'^[一二三四五六七八九十]+、',
            ],
            'list_item': [
                r'^[•\-\*]\s+',
                r'^\d+\)\s+',
                r'^[一二三四五六七八九十]+、',
            ],
            'table': [
                r'\|.*\|.*\|',
                r'[\u4e00-\u9fff\w\s]*\t+[\u4e00-\u9fff\w\s]*',
            ]
        }
        
        logger.info(f"🔧 EnhancedDocumentProcessor 初始化完成")
        logger.info(f"   - 基礎chunk_size: {self.chunk_size}")
        logger.info(f"   - chunk_overlap: {self.chunk_overlap}")
        logger.info(f"   - 啟用階層切割: {self.enable_hierarchical}")
        logger.info(f"   - 啟用結構識別: {self.enable_structure_detection}")
    
    def detect_document_structure(self, text: str) -> List[Tuple[str, DocumentStructure]]:
        """
        檢測文檔結構
        
        Returns:
            List of (text_segment, structure_info)
        """
        if not self.enable_structure_detection:
            return [(text, DocumentStructure(content_type="paragraph", semantic_level=2))]
        
        segments = []
        lines = text.split('\n')
        current_chapter = None
        current_section = None
        current_subsection = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            structure = self._analyze_line_structure(line)
            
            # 更新層級信息
            if structure.content_type == 'title':
                if structure.semantic_level == 1:  # 章節
                    current_chapter = line
                    current_section = None
                    current_subsection = None
                elif structure.semantic_level == 2:  # 節
                    current_section = line
                    current_subsection = None
                elif structure.semantic_level == 3:  # 子節
                    current_subsection = line
            
            # 設定層級路徑
            structure.chapter = current_chapter
            structure.section = current_section
            structure.subsection = current_subsection
            structure.hierarchy_path = self._build_hierarchy_path(
                current_chapter, current_section, current_subsection
            )
            
            segments.append((line, structure))
        
        logger.info(f"📋 檢測到 {len(segments)} 個文檔段落")
        return segments
    
    def _analyze_line_structure(self, line: str) -> DocumentStructure:
        """分析單行的結構類型"""
        
        # 檢查是否為章節標題
        for pattern in self.structure_patterns['chapter']:
            if re.match(pattern, line):
                return DocumentStructure(content_type="title", semantic_level=1)
        
        # 檢查是否為節標題
        for pattern in self.structure_patterns['section']:
            if re.match(pattern, line):
                return DocumentStructure(content_type="title", semantic_level=2)
        
        # 檢查是否為子節標題
        for pattern in self.structure_patterns['subsection']:
            if re.match(pattern, line):
                return DocumentStructure(content_type="title", semantic_level=3)
        
        # 檢查是否為列表項目
        for pattern in self.structure_patterns['list_item']:
            if re.match(pattern, line):
                return DocumentStructure(content_type="list", semantic_level=2)
        
        # 檢查是否為表格
        for pattern in self.structure_patterns['table']:
            if re.match(pattern, line):
                return DocumentStructure(content_type="table", semantic_level=2)
        
        # 預設為段落
        return DocumentStructure(content_type="paragraph", semantic_level=2)
    
    def _build_hierarchy_path(self, chapter: str, section: str, subsection: str) -> str:
        """構建層級路徑"""
        path_parts = []
        if chapter:
            path_parts.append(chapter[:20])  # 限制長度
        if section:
            path_parts.append(section[:20])
        if subsection:
            path_parts.append(subsection[:20])
        
        return " / ".join(path_parts) if path_parts else "根目錄"
    
    def hierarchical_chunk(self, document: Document) -> List[ChunkInfo]:
        """
        階層式文檔切割
        """
        if not self.enable_hierarchical:
            return self._simple_chunk(document)
        
        text = document.text
        segments = self.detect_document_structure(text)
        
        all_chunks = []
        chunk_id = 0
        
        # 按不同策略切割
        for strategy_name, strategy_config in self.chunk_strategies.items():
            strategy_chunks = self._chunk_by_strategy(
                segments, strategy_name, strategy_config, chunk_id
            )
            all_chunks.extend(strategy_chunks)
            chunk_id += len(strategy_chunks)
        
        logger.info(f"🔄 階層切割完成，總共產生 {len(all_chunks)} 個chunks")
        return all_chunks
    
    def _chunk_by_strategy(
        self, 
        segments: List[Tuple[str, DocumentStructure]], 
        strategy_name: str, 
        strategy_config: Dict[str, int],
        start_chunk_id: int
    ) -> List[ChunkInfo]:
        """按特定策略切割"""
        
        chunk_size = strategy_config['size']
        chunk_overlap = strategy_config['overlap']
        
        chunks = []
        current_chunk = ""
        current_structure = None
        chunk_index = 0
        
        for text_segment, structure in segments:
            # 如果是標題且當前chunk不為空，先保存當前chunk
            if (structure.content_type == "title" and 
                current_chunk.strip() and 
                len(current_chunk) > chunk_overlap):
                
                chunks.append(ChunkInfo(
                    content=current_chunk.strip(),
                    structure=current_structure or structure,
                    chunk_index=start_chunk_id + chunk_index,
                    total_chunks=0,  # 稍後更新
                    strategy_type=strategy_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                ))
                chunk_index += 1
                current_chunk = ""
            
            # 添加新內容
            if current_chunk:
                current_chunk += "\n" + text_segment
            else:
                current_chunk = text_segment
                current_structure = structure
            
            # 如果超過chunk大小，進行切割
            if len(current_chunk) >= chunk_size:
                # 找到合適的切割點
                split_point = self._find_split_point(current_chunk, chunk_size, chunk_overlap)
                
                chunk_content = current_chunk[:split_point]
                remaining_content = current_chunk[split_point - chunk_overlap:]
                
                chunks.append(ChunkInfo(
                    content=chunk_content.strip(),
                    structure=current_structure or structure,
                    chunk_index=start_chunk_id + chunk_index,
                    total_chunks=0,
                    strategy_type=strategy_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                ))
                chunk_index += 1
                current_chunk = remaining_content
        
        # 處理最後一個chunk
        if current_chunk.strip():
            chunks.append(ChunkInfo(
                content=current_chunk.strip(),
                structure=current_structure or DocumentStructure(content_type="paragraph", semantic_level=2),
                chunk_index=start_chunk_id + chunk_index,
                total_chunks=0,
                strategy_type=strategy_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            ))
        
        # 更新total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        logger.info(f"📦 {strategy_name} 策略產生 {len(chunks)} 個chunks")
        return chunks
    
    def _find_split_point(self, text: str, target_size: int, overlap: int) -> int:
        """找到最佳切割點（優先在句號、段落邊界等位置切割）"""
        
        if len(text) <= target_size:
            return len(text)
        
        # 優先在句號處切割
        sentence_endings = ['.', '。', '！', '？', '!', '?']
        for i in range(target_size, overlap, -1):
            if i < len(text) and text[i] in sentence_endings:
                return min(i + 1, len(text))
        
        # 其次在換行處切割
        for i in range(target_size, overlap, -1):
            if i < len(text) and text[i] == '\n':
                return i
        
        # 最後在空格處切割
        for i in range(target_size, overlap, -1):
            if i < len(text) and text[i] == ' ':
                return i
        
        # 實在找不到合適位置，就硬切割
        return target_size
    
    def _simple_chunk(self, document: Document) -> List[ChunkInfo]:
        """簡單切割方式（後備方案）"""
        text = document.text
        parser = SimpleNodeParser.from_defaults(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        nodes = parser.get_nodes_from_documents([document])
        chunks = []
        
        for i, node in enumerate(nodes):
            structure = DocumentStructure(content_type="paragraph", semantic_level=2)
            chunks.append(ChunkInfo(
                content=node.text,
                structure=structure,
                chunk_index=i,
                total_chunks=len(nodes),
                strategy_type="simple",
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ))
        
        return chunks
    
    def create_enhanced_documents(self, chunk_infos: List[ChunkInfo], original_document: Document) -> List[Document]:
        """
        創建增強的Document對象，包含所有元數據
        """
        enhanced_docs = []
        
        for chunk_info in chunk_infos:
            # 創建增強的元數據
            enhanced_metadata = {
                **original_document.metadata,
                
                # 文檔結構信息
                "document_structure": {
                    "chapter": chunk_info.structure.chapter,
                    "section": chunk_info.structure.section,
                    "subsection": chunk_info.structure.subsection,
                    "content_type": chunk_info.structure.content_type,
                    "semantic_level": chunk_info.structure.semantic_level,
                    "hierarchy_path": chunk_info.structure.hierarchy_path
                },
                
                # 切割策略信息
                "chunking_strategy": {
                    "strategy_type": chunk_info.strategy_type,
                    "chunk_size": chunk_info.chunk_size,
                    "chunk_overlap": chunk_info.chunk_overlap,
                    "chunk_index": chunk_info.chunk_index,
                    "total_chunks": chunk_info.total_chunks,
                    "parent_chunk_id": chunk_info.parent_chunk_id
                },
                
                # 處理信息
                "processing_info": {
                    "processed_at": datetime.now().isoformat(),
                    "processor_version": "enhanced_v2.0",
                    "extraction_method": "hierarchical_chunking"
                }
            }
            
            # 創建Document對象
            doc = Document(
                text=chunk_info.content,
                metadata=enhanced_metadata
            )
            
            enhanced_docs.append(doc)
        
        logger.info(f"📄 創建了 {len(enhanced_docs)} 個增強Document對象")
        return enhanced_docs
    
    def process_document(self, document: Document) -> List[Document]:
        """
        完整的文檔處理流程
        """
        logger.info(f"🔄 開始處理文檔: {document.metadata.get('source', 'unknown')}")
        
        # 1. 階層式切割
        chunk_infos = self.hierarchical_chunk(document)
        
        # 2. 創建增強的Document對象
        enhanced_docs = self.create_enhanced_documents(chunk_infos, document)
        
        logger.info(f"✅ 文檔處理完成，產生 {len(enhanced_docs)} 個chunks")
        return enhanced_docs