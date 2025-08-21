#!/usr/bin/env python3
"""
Elasticsearch Mapping 管理工具
用於創建、驗證和管理 Elasticsearch 索引映射配置
"""

import argparse
import json
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.elasticsearch.mapping_loader import ElasticsearchMappingLoader
from elasticsearch import Elasticsearch


def create_index(es_client: Elasticsearch, index_name: str, mapping: dict, force: bool = False):
    """創建索引
    
    Args:
        es_client: Elasticsearch 客戶端
        index_name: 索引名稱
        mapping: 映射配置
        force: 是否強制重建（刪除現有索引）
    """
    if es_client.indices.exists(index=index_name):
        if force:
            print(f"🗑️  刪除現有索引: {index_name}")
            es_client.indices.delete(index=index_name)
        else:
            print(f"⚠️  索引 '{index_name}' 已存在。使用 --force 強制重建。")
            return False
    
    print(f"🔧 創建索引: {index_name}")
    try:
        response = es_client.indices.create(index=index_name, body=mapping)
        if response.get('acknowledged', False):
            print(f"✅ 成功創建索引: {index_name}")
            return True
        else:
            print(f"❌ 創建索引失敗: {response}")
            return False
    except Exception as e:
        print(f"❌ 創建索引時發生錯誤: {e}")
        return False


def validate_mapping_cmd(args):
    """驗證映射配置命令"""
    loader = ElasticsearchMappingLoader()
    
    try:
        if args.mapping_file:
            mapping = loader.load_mapping(args.mapping_file)
        else:
            mapping = loader.load_mapping()
        
        if loader.validate_mapping(mapping):
            print("✅ Mapping 配置驗證通過")
            
            # 顯示配置摘要
            properties = mapping['mappings']['properties']
            embedding_config = properties.get('embedding', {})
            
            print(f"\n📊 配置摘要:")
            print(f"  - 分片數: {mapping['settings']['number_of_shards']}")
            print(f"  - 副本數: {mapping['settings']['number_of_replicas']}")
            print(f"  - 向量維度: {embedding_config.get('dims', 'N/A')}")
            print(f"  - 相似度算法: {embedding_config.get('similarity', 'N/A')}")
            print(f"  - 字段數量: {len(properties)}")
            
        else:
            print("❌ Mapping 配置驗證失敗")
            return 1
            
    except Exception as e:
        print(f"❌ 加載配置失敗: {e}")
        return 1
    
    return 0


def list_mappings_cmd(args):
    """列出可用映射文件命令"""
    loader = ElasticsearchMappingLoader()
    
    files = loader.list_available_mappings()
    
    print(f"📋 可用的映射配置文件 ({len(files)} 個):")
    for file in files:
        print(f"  - {file}")
        
        # 顯示文件摘要
        try:
            mapping = loader.load_mapping(file)
            properties = mapping['mappings']['properties']
            print(f"    字段數: {len(properties)}")
        except Exception as e:
            print(f"    ❌ 加載失敗: {e}")
    
    return 0


def create_index_cmd(args):
    """創建索引命令"""
    # 連接 Elasticsearch
    try:
        es_client = Elasticsearch([{'host': args.host, 'port': args.port}])
        if not es_client.ping():
            print(f"❌ 無法連接到 Elasticsearch: {args.host}:{args.port}")
            return 1
        print(f"✅ 已連接到 Elasticsearch: {args.host}:{args.port}")
    except Exception as e:
        print(f"❌ 連接 Elasticsearch 失敗: {e}")
        return 1
    
    # 加載映射配置
    loader = ElasticsearchMappingLoader()
    
    try:
        if args.mapping_file:
            mapping = loader.load_mapping(args.mapping_file, **vars(args))
        else:
            # 使用自定義變數
            variables = {}
            if args.dimension:
                variables['DIMENSION'] = args.dimension
            if args.shards:
                variables['SHARDS'] = args.shards
            if args.replicas:
                variables['REPLICAS'] = args.replicas
            if args.similarity:
                variables['SIMILARITY'] = args.similarity
                
            mapping = loader.load_mapping(**variables)
            
    except Exception as e:
        print(f"❌ 加載映射配置失敗: {e}")
        return 1
    
    # 創建索引
    success = create_index(es_client, args.index_name, mapping, args.force)
    return 0 if success else 1


def show_mapping_cmd(args):
    """顯示映射配置命令"""
    loader = ElasticsearchMappingLoader()
    
    try:
        mapping = loader.load_mapping(args.mapping_file or "index_mapping.json")
        
        if args.format == 'json':
            print(json.dumps(mapping, indent=2, ensure_ascii=False))
        else:
            print(f"📋 映射配置: {args.mapping_file or 'index_mapping.json'}")
            print(f"分片數: {mapping['settings']['number_of_shards']}")
            print(f"副本數: {mapping['settings']['number_of_replicas']}")
            
            properties = mapping['mappings']['properties']
            print(f"\n📊 字段配置 ({len(properties)} 個):")
            
            for field_name, field_config in properties.items():
                field_type = field_config.get('type', 'unknown')
                print(f"  - {field_name}: {field_type}")
                
                if field_type == 'dense_vector':
                    print(f"    維度: {field_config.get('dims', 'N/A')}")
                    print(f"    相似度: {field_config.get('similarity', 'N/A')}")
                elif field_type == 'text':
                    analyzer = field_config.get('analyzer', 'default')
                    print(f"    分析器: {analyzer}")
                elif field_type == 'object' and field_name == 'metadata':
                    nested_props = field_config.get('properties', {})
                    print(f"    子字段: {list(nested_props.keys())}")
        
    except Exception as e:
        print(f"❌ 顯示配置失敗: {e}")
        return 1
    
    return 0


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Elasticsearch Mapping 管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 驗證命令
    validate_parser = subparsers.add_parser('validate', help='驗證映射配置')
    validate_parser.add_argument('-f', '--mapping-file', help='映射文件名')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出可用映射文件')
    
    # 創建索引命令
    create_parser = subparsers.add_parser('create', help='創建 Elasticsearch 索引')
    create_parser.add_argument('index_name', help='索引名稱')
    create_parser.add_argument('-f', '--mapping-file', help='映射文件名')
    create_parser.add_argument('--host', default='localhost', help='Elasticsearch 主機')
    create_parser.add_argument('--port', type=int, default=9200, help='Elasticsearch 端口')
    create_parser.add_argument('--force', action='store_true', help='強制重建索引')
    create_parser.add_argument('--dimension', type=int, help='向量維度')
    create_parser.add_argument('--shards', type=int, help='分片數')
    create_parser.add_argument('--replicas', type=int, help='副本數')
    create_parser.add_argument('--similarity', help='相似度算法')
    
    # 顯示映射命令
    show_parser = subparsers.add_parser('show', help='顯示映射配置')
    show_parser.add_argument('-f', '--mapping-file', help='映射文件名')
    show_parser.add_argument('--format', choices=['json', 'summary'], default='summary', help='輸出格式')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 執行對應命令
    if args.command == 'validate':
        return validate_mapping_cmd(args)
    elif args.command == 'list':
        return list_mappings_cmd(args)
    elif args.command == 'create':
        return create_index_cmd(args)
    elif args.command == 'show':
        return show_mapping_cmd(args)
    else:
        print(f"❌ 未知命令: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())