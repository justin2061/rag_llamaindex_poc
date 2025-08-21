"""
Elasticsearch Mapping 配置加載器
支持變數替換和模板化配置
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


class ElasticsearchMappingLoader:
    """Elasticsearch Mapping 配置加載器"""
    
    def __init__(self, config_dir: str = None):
        """初始化配置加載器
        
        Args:
            config_dir: 配置文件目錄，默認為 config/elasticsearch
        """
        if config_dir is None:
            current_dir = Path(__file__).parent
            self.config_dir = current_dir
        else:
            self.config_dir = Path(config_dir)
    
    def load_mapping(self, mapping_file: str = "index_mapping.json", **variables) -> Dict[str, Any]:
        """加載 mapping 配置並替換變數
        
        Args:
            mapping_file: mapping 文件名
            **variables: 要替換的變數
            
        Returns:
            Dict: 處理後的 mapping 配置
        """
        mapping_path = self.config_dir / mapping_file
        
        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping 文件不存在: {mapping_path}")
        
        # 如果沒有提供變數，使用默認變數
        if not variables:
            variables = self.get_default_variables()
        
        # 讀取原始 JSON
        with open(mapping_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替換變數
        for key, value in variables.items():
            placeholder = f"${{{key}}}"
            # 對於數值字段，直接替換為數字，不需要引號
            if key in ['DIMENSION', 'SHARDS', 'REPLICAS'] and isinstance(value, (int, float)):
                content = content.replace(placeholder, str(int(value)))
            elif isinstance(value, str):
                # 字符串值需要引號，除非模板中已有引號
                if f'"{placeholder}"' in content:
                    content = content.replace(f'"{placeholder}"', f'"{value}"')
                else:
                    content = content.replace(placeholder, f'"{value}"')
            else:
                content = content.replace(placeholder, str(value))
        
        # 解析 JSON
        try:
            mapping = json.loads(content)
            return mapping
        except json.JSONDecodeError as e:
            raise ValueError(f"無效的 JSON 格式: {e}")
    
    def get_default_variables(self) -> Dict[str, Any]:
        """獲取默認變數值
        
        Returns:
            Dict: 默認變數字典
        """
        try:
            from config.config import (
                ELASTICSEARCH_SHARDS,
                ELASTICSEARCH_REPLICAS, 
                ELASTICSEARCH_VECTOR_DIMENSION,
                ELASTICSEARCH_SIMILARITY
            )
        except ImportError:
            # 如果無法導入，使用默認值
            ELASTICSEARCH_SHARDS = 1
            ELASTICSEARCH_REPLICAS = 0
            ELASTICSEARCH_VECTOR_DIMENSION = 384
            ELASTICSEARCH_SIMILARITY = "cosine"
        
        return {
            "SHARDS": ELASTICSEARCH_SHARDS or 1,
            "REPLICAS": ELASTICSEARCH_REPLICAS or 0,
            "DIMENSION": ELASTICSEARCH_VECTOR_DIMENSION or 384,
            "SIMILARITY": ELASTICSEARCH_SIMILARITY or "cosine"
        }
    
    def create_mapping_with_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """使用配置創建 mapping
        
        Args:
            config: Elasticsearch 配置字典
            
        Returns:
            Dict: 完整的 mapping 配置
        """
        variables = {
            "SHARDS": config.get('shards', 1),
            "REPLICAS": config.get('replicas', 0),
            "DIMENSION": config.get('dimension', 384),
            "SIMILARITY": config.get('similarity', 'cosine')
        }
        
        return self.load_mapping(**variables)
    
    def validate_mapping(self, mapping: Dict[str, Any]) -> bool:
        """驗證 mapping 配置的有效性
        
        Args:
            mapping: mapping 配置
            
        Returns:
            bool: 是否有效
        """
        try:
            # 基本結構檢查
            if 'mappings' not in mapping:
                return False
                
            if 'properties' not in mapping['mappings']:
                return False
            
            properties = mapping['mappings']['properties']
            
            # 檢查必要字段
            required_fields = ['content', 'embedding', 'metadata']
            for field in required_fields:
                if field not in properties:
                    return False
            
            # 檢查向量字段配置
            embedding_config = properties['embedding']
            if embedding_config.get('type') != 'dense_vector':
                return False
                
            if 'dims' not in embedding_config:
                return False
            
            return True
            
        except Exception:
            return False
    
    def list_available_mappings(self) -> list:
        """列出可用的 mapping 文件
        
        Returns:
            list: mapping 文件列表
        """
        if not self.config_dir.exists():
            return []
            
        return [f.name for f in self.config_dir.glob("*.json")]
    
    def save_mapping(self, mapping: Dict[str, Any], filename: str = "custom_mapping.json"):
        """保存 mapping 配置到文件
        
        Args:
            mapping: mapping 配置
            filename: 文件名
        """
        mapping_path = self.config_dir / filename
        
        # 確保目錄存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)


def get_elasticsearch_mapping(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """獲取 Elasticsearch mapping 配置的便捷函數
    
    Args:
        config: Elasticsearch 配置，如果為 None 則使用默認配置
        
    Returns:
        Dict: mapping 配置
    """
    loader = ElasticsearchMappingLoader()
    
    if config:
        return loader.create_mapping_with_config(config)
    else:
        variables = loader.get_default_variables()
        return loader.load_mapping(**variables)


# 示例用法
if __name__ == "__main__":
    # 測試配置加載
    loader = ElasticsearchMappingLoader()
    
    print("📋 可用的 mapping 文件:")
    for mapping_file in loader.list_available_mappings():
        print(f"  - {mapping_file}")
    
    print("\n🔧 加載默認配置:")
    try:
        mapping = loader.load_mapping()
        print(f"✅ 成功加載 mapping，字段數: {len(mapping['mappings']['properties'])}")
        
        if loader.validate_mapping(mapping):
            print("✅ Mapping 配置驗證通過")
        else:
            print("❌ Mapping 配置驗證失敗")
            
    except Exception as e:
        print(f"❌ 加載失敗: {e}")