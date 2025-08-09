import os
import asyncio
import nest_asyncio
from typing import List, Optional, Dict, Any, Callable, Union
import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile

# LlamaIndex 核心
from llama_index.core import VectorStoreIndex, Document, PropertyGraphIndex
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.graph_stores.simple import SimpleGraphStore
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import TransformComponent, BaseNode
from llama_index.core.indices.property_graph.utils import default_parse_triplets_fn
from llama_index.core.graph_stores.types import EntityNode, KG_NODES_KEY, KG_RELATIONS_KEY, Relation
from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.default_prompts import DEFAULT_KG_TRIPLET_EXTRACT_PROMPT
from llama_index.core.async_utils import run_jobs
from llama_index.core.llms.llm import LLM

# 繼承原有系統
from enhanced_rag_system import EnhancedRAGSystem
from config import (
    GROQ_API_KEY, EMBEDDING_MODEL, LLM_MODEL, INDEX_DIR,
    ENABLE_GRAPH_RAG, MAX_TRIPLETS_PER_CHUNK, GRAPH_COMMUNITY_SIZE
)

# 應用 nest_asyncio 以支援在 Streamlit 中使用 asyncio
nest_asyncio.apply()

class GraphRAGExtractor(TransformComponent):
    """Graph RAG 知識圖譜提取器"""
    
    def __init__(
        self,
        llm: Optional[LLM] = None,
        extract_prompt: Optional[Union[str, PromptTemplate]] = None,
        parse_fn: Callable = default_parse_triplets_fn,
        max_paths_per_chunk: int = 10,
        num_workers: int = 4,
    ) -> None:
        """初始化提取器"""
        from llama_index.core import Settings
        
        if isinstance(extract_prompt, str):
            extract_prompt = PromptTemplate(extract_prompt)
            
        super().__init__(
            llm=llm or Settings.llm,
            extract_prompt=extract_prompt or DEFAULT_KG_TRIPLET_EXTRACT_PROMPT,
            parse_fn=parse_fn,
            num_workers=num_workers,
            max_paths_per_chunk=max_paths_per_chunk,
        )
    
    @classmethod
    def class_name(cls) -> str:
        return "GraphRAGExtractor"
    
    def __call__(
        self, nodes: List[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> List[BaseNode]:
        """同步提取接口"""
        return asyncio.run(
            self.acall(nodes, show_progress=show_progress, **kwargs)
        )
    
    async def _aextract(self, node: BaseNode) -> BaseNode:
        """異步提取單個節點的三元組"""
        assert hasattr(node, "text")
        
        text = node.get_content(metadata_mode="llm")
        try:
            llm_response = await self.llm.apredict(
                self.extract_prompt,
                text=text,
                max_knowledge_triplets=self.max_paths_per_chunk,
            )
            
            entities, entities_relationship = self.parse_fn(llm_response)
        except ValueError:
            entities = []
            entities_relationship = []
        
        existing_nodes = node.metadata.pop(KG_NODES_KEY, [])
        existing_relations = node.metadata.pop(KG_RELATIONS_KEY, [])
        
        # 處理實體
        metadata = node.metadata.copy()
        for entity, entity_type, description in entities:
            metadata["entity_description"] = description
            entity_node = EntityNode(
                name=entity, label=entity_type, properties=metadata
            )
            existing_nodes.append(entity_node)
        
        # 處理關係
        metadata = node.metadata.copy()
        for triple in entities_relationship:
            subj, rel, obj, description = triple
            subj_node = EntityNode(name=subj, properties=metadata)
            obj_node = EntityNode(name=obj, properties=metadata)
            metadata["relationship_description"] = description
            rel_node = Relation(
                label=rel,
                source_id=subj_node.id,
                target_id=obj_node.id,
                properties=metadata,
            )
            
            existing_nodes.extend([subj_node, obj_node])
            existing_relations.append(rel_node)
        
        node.metadata[KG_NODES_KEY] = existing_nodes
        node.metadata[KG_RELATIONS_KEY] = existing_relations
        return node
    
    async def acall(
        self, nodes: List[BaseNode], show_progress: bool = False, **kwargs: Any
    ) -> List[BaseNode]:
        """異步提取多個節點的三元組"""
        jobs = []
        for node in nodes:
            jobs.append(self._aextract(node))
        
        return await run_jobs(
            jobs,
            workers=self.num_workers,
            show_progress=show_progress,
            desc="正在提取知識圖譜...",
        )


class GraphRAGSystem(EnhancedRAGSystem):
    """Graph RAG 系統 - 基於屬性圖的檢索增強生成"""
    
    def __init__(self, use_chroma: bool = True):
        super().__init__(use_chroma)
        self.property_graph_index = None
        self.graph_store = SimpleGraphStore()
        self.kg_extractor = None
        self.graph_rag_retriever = None
        self.communities = {}
        self.community_summaries = {}
        
    def _ensure_models_initialized(self):
        """確保模型已初始化"""
        if not self.models_initialized:
            self._setup_models()
            self.models_initialized = True
            
        # 初始化知識圖譜提取器
        if self.kg_extractor is None:
            self.kg_extractor = GraphRAGExtractor(
                llm=self._get_llm(),
                max_paths_per_chunk=MAX_TRIPLETS_PER_CHUNK,
                num_workers=4
            )
    
    def _get_llm(self):
        """獲取 LLM 實例"""
        from llama_index.core import Settings
        return Settings.llm
    
    def create_property_graph_index(self, documents: List[Document]) -> PropertyGraphIndex:
        """建立屬性圖索引"""
        with st.spinner("正在建立知識圖譜索引..."):
            self._ensure_models_initialized()
            
            try:
                # 建立儲存上下文
                storage_context = StorageContext.from_defaults(
                    graph_store=self.graph_store
                )
                
                # 建立屬性圖索引
                self.property_graph_index = PropertyGraphIndex.from_documents(
                    documents,
                    kg_extractors=[self.kg_extractor],
                    storage_context=storage_context,
                    show_progress=True,
                    embed_kg_nodes=True,  # 啟用節點嵌入以支援混合檢索
                )
                
                # 持久化
                self.property_graph_index.storage_context.persist(persist_dir=INDEX_DIR)
                
                st.success("✅ 知識圖譜索引建立成功")
                return self.property_graph_index
                
            except Exception as e:
                st.error(f"知識圖譜索引建立失敗: {str(e)}")
                # 回退到傳統索引
                st.warning("正在回退到傳統 RAG 模式...")
                return super().create_index(documents)
    
    def setup_graph_rag_retriever(self):
        """設置 Graph RAG 檢索器"""
        if self.property_graph_index:
            try:
                self.graph_rag_retriever = KnowledgeGraphRAGRetriever(
                    storage_context=self.property_graph_index.storage_context,
                    verbose=True,
                    with_nl2graphquery=True,  # 啟用自然語言轉圖查詢
                )
                
                self.query_engine = RetrieverQueryEngine.from_args(
                    self.graph_rag_retriever,
                )
                
                st.success("✅ Graph RAG 檢索器設置成功")
                
            except Exception as e:
                st.warning(f"Graph RAG 檢索器設置失敗: {str(e)}")
                # 回退到傳統查詢引擎
                super().setup_query_engine()
    
    def create_index(self, documents: List[Document]):
        """覆寫索引建立方法以支援 Graph RAG"""
        if ENABLE_GRAPH_RAG:
            index = self.create_property_graph_index(documents)
            self.setup_graph_rag_retriever()
            
            # 建立社群
            if self.property_graph_index:
                self._build_communities()
            
            return index
        else:
            # 使用傳統 RAG
            return super().create_index(documents)
    
    def query_with_graph_context(self, question: str) -> str:
        """基於圖的上下文查詢"""
        if not self.query_engine:
            return "系統尚未初始化，請先載入文件。"
        
        try:
            # 建構包含歷史對話和圖上下文的查詢
            context_prompt = self.memory.get_context_prompt()
            
            if context_prompt and self.memory.is_enabled():
                enhanced_question = f"""
{context_prompt}

當前問題: {question}

請基於知識圖譜、對話歷史和文檔內容回答當前問題。
如果能從知識圖譜中找到相關的實體和關係，請優先使用這些信息。
"""
            else:
                enhanced_question = question
            
            with st.spinner("正在分析知識圖譜..."):
                response = self.query_engine.query(enhanced_question)
                response_str = str(response)
                
                # 將這輪對話加入記憶
                self.memory.add_exchange(question, response_str)
                
                return response_str
                
        except Exception as e:
            st.error(f"Graph RAG 查詢時發生錯誤: {str(e)}")
            # 回退到傳統查詢
            return super().query_with_context(question)
    
    def _build_communities(self):
        """建立圖社群"""
        try:
            if not self.property_graph_index:
                return
            
            with st.spinner("正在分析知識圖譜社群..."):
                # 轉換為 NetworkX 圖
                nx_graph = self._create_networkx_graph()
                
                if len(nx_graph.nodes()) == 0:
                    st.warning("知識圖譜中沒有足夠的節點建立社群")
                    return
                
                # 使用 NetworkX 的社群檢測
                try:
                    import community as community_louvain
                    partition = community_louvain.best_partition(nx_graph.to_undirected())
                    
                    # 組織社群資訊
                    communities = {}
                    for node, comm_id in partition.items():
                        if comm_id not in communities:
                            communities[comm_id] = []
                        communities[comm_id].append(node)
                    
                    self.communities = communities
                    
                    # 生成社群摘要
                    self._generate_community_summaries(nx_graph)
                    
                    st.success(f"✅ 識別出 {len(communities)} 個知識社群")
                    
                except ImportError:
                    # 如果沒有 python-louvain，使用簡單的連通分量
                    components = list(nx.connected_components(nx_graph.to_undirected()))
                    communities = {i: list(comp) for i, comp in enumerate(components)}
                    self.communities = communities
                    st.info(f"識別出 {len(communities)} 個知識群組")
                    
        except Exception as e:
            st.warning(f"社群建立失敗: {str(e)}")
    
    def _create_networkx_graph(self) -> nx.Graph:
        """從屬性圖建立 NetworkX 圖"""
        nx_graph = nx.Graph()
        
        try:
            # 獲取圖資料
            if hasattr(self.property_graph_index, 'property_graph_store'):
                graph_store = self.property_graph_index.property_graph_store
                
                # 添加節點
                if hasattr(graph_store, 'get_all_nodes'):
                    for node in graph_store.get_all_nodes():
                        nx_graph.add_node(node.name, **node.properties)
                
                # 添加邊
                if hasattr(graph_store, 'get_all_relationships'):
                    for rel in graph_store.get_all_relationships():
                        nx_graph.add_edge(
                            rel.source_id, 
                            rel.target_id,
                            relationship=rel.label,
                            **rel.properties
                        )
                        
        except Exception as e:
            st.warning(f"NetworkX 圖建立失敗: {str(e)}")
        
        return nx_graph
    
    def _generate_community_summaries(self, nx_graph: nx.Graph):
        """生成社群摘要"""
        try:
            llm = self._get_llm()
            
            for comm_id, nodes in self.communities.items():
                if len(nodes) < 2:
                    continue
                
                # 收集社群內的關係資訊
                relationships = []
                for node in nodes:
                    for neighbor in nx_graph.neighbors(node):
                        if neighbor in nodes:
                            edge_data = nx_graph.get_edge_data(node, neighbor)
                            if edge_data:
                                relationship = edge_data.get('relationship', '相關')
                                relationships.append(f"{node} -> {neighbor} -> {relationship}")
                
                if relationships:
                    relationships_text = "\n".join(relationships[:10])  # 限制長度
                    
                    # 生成摘要提示
                    summary_prompt = f"""
請為以下知識圖譜社群生成一個簡潔的摘要：

關係資訊：
{relationships_text}

請總結這個社群的主要主題和核心概念，不超過100字。
"""
                    try:
                        summary = llm.complete(summary_prompt).text.strip()
                        self.community_summaries[comm_id] = summary
                    except Exception:
                        self.community_summaries[comm_id] = f"包含 {len(nodes)} 個相關概念的知識群組"
                        
        except Exception as e:
            st.warning(f"社群摘要生成失敗: {str(e)}")
    
    def visualize_knowledge_graph(self, max_nodes: int = 100) -> str:
        """可視化知識圖譜"""
        try:
            nx_graph = self._create_networkx_graph()
            
            if len(nx_graph.nodes()) == 0:
                return None
            
            # 限制節點數量以避免過於複雜
            if len(nx_graph.nodes()) > max_nodes:
                # 選擇度數最高的節點
                degree_dict = dict(nx_graph.degree())
                top_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
                selected_nodes = [node for node, _ in top_nodes]
                nx_graph = nx_graph.subgraph(selected_nodes)
            
            # 創建 Pyvis 網絡
            net = Network(
                height="600px", 
                width="100%", 
                bgcolor="#ffffff",
                font_color="#333333"
            )
            
            # 配置物理效果
            net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100}
              },
              "nodes": {
                "borderWidth": 2,
                "borderWidthSelected": 3,
                "font": {"size": 14}
              },
              "edges": {
                "font": {"size": 12},
                "smooth": {"type": "continuous"}
              }
            }
            """)
            
            # 社群著色
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                     '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
            
            # 添加節點
            for node in nx_graph.nodes():
                # 確定節點所屬社群
                node_color = '#667eea'  # 默認顏色
                for comm_id, comm_nodes in self.communities.items():
                    if node in comm_nodes:
                        node_color = colors[comm_id % len(colors)]
                        break
                
                # 節點大小基於度數
                degree = nx_graph.degree(node)
                size = min(max(degree * 5, 10), 30)
                
                net.add_node(
                    node, 
                    label=str(node)[:20],  # 限制標籤長度
                    color=node_color,
                    size=size,
                    title=f"節點: {node}\n度數: {degree}"
                )
            
            # 添加邊
            for edge in nx_graph.edges():
                source, target = edge
                edge_data = nx_graph.get_edge_data(source, target)
                relationship = edge_data.get('relationship', '相關') if edge_data else '相關'
                
                net.add_edge(
                    source, 
                    target,
                    label=relationship[:10],  # 限制標籤長度
                    title=f"關係: {relationship}",
                    color={'color': '#848484'}
                )
            
            # 生成 HTML
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
                net.save_graph(tmp_file.name)
                return tmp_file.name
                
        except Exception as e:
            st.error(f"知識圖譜可視化失敗: {str(e)}")
            return None
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """獲取圖統計資訊"""
        stats = super().get_document_statistics()
        
        if self.property_graph_index:
            nx_graph = self._create_networkx_graph()
            
            graph_stats = {
                "nodes_count": len(nx_graph.nodes()),
                "edges_count": len(nx_graph.edges()),
                "communities_count": len(self.communities),
                "average_degree": sum(dict(nx_graph.degree()).values()) / len(nx_graph.nodes()) if nx_graph.nodes() else 0,
                "density": nx.density(nx_graph),
                "communities": self.communities,
                "community_summaries": self.community_summaries
            }
            
            stats["graph_stats"] = graph_stats
        
        return stats
    
    def get_related_entities(self, entity_name: str, max_results: int = 10) -> List[Dict]:
        """獲取與指定實體相關的實體"""
        related = []
        
        try:
            nx_graph = self._create_networkx_graph()
            
            if entity_name in nx_graph.nodes():
                # 獲取直接相連的鄰居
                neighbors = list(nx_graph.neighbors(entity_name))
                
                for neighbor in neighbors[:max_results]:
                    edge_data = nx_graph.get_edge_data(entity_name, neighbor)
                    relationship = edge_data.get('relationship', '相關') if edge_data else '相關'
                    
                    related.append({
                        'entity': neighbor,
                        'relationship': relationship,
                        'type': 'direct'
                    })
                
                # 如果直接鄰居不足，添加二度鄰居
                if len(related) < max_results:
                    for neighbor in neighbors:
                        second_neighbors = list(nx_graph.neighbors(neighbor))
                        for second_neighbor in second_neighbors:
                            if second_neighbor != entity_name and second_neighbor not in [r['entity'] for r in related]:
                                if len(related) >= max_results:
                                    break
                                    
                                related.append({
                                    'entity': second_neighbor,
                                    'relationship': f"透過 {neighbor}",
                                    'type': 'indirect'
                                })
                        
                        if len(related) >= max_results:
                            break
                            
        except Exception as e:
            st.warning(f"獲取相關實體失敗: {str(e)}")
        
        return related
