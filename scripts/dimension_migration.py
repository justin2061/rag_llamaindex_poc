#!/usr/bin/env python3
"""
Elasticsearch 向量維度遷移工具
支持安全的維度切換和數據遷移
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class DimensionMigrator:
    """維度遷移管理器"""
    
    def __init__(self):
        self.project_root = project_root
        self.env_file = self.project_root / ".env"
        self.backup_dir = self.project_root / "data" / "migration_backups"
        self.migration_log = self.project_root / "data" / "migration.log"
        
        # 確保目錄存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def log_message(self, message: str, level: str = "INFO"):
        """記錄遷移日誌"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.migration_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def get_current_dimension(self) -> Optional[int]:
        """獲取當前維度配置"""
        try:
            if not self.env_file.exists():
                self.log_message("未找到 .env 文件", "ERROR")
                return None
                
            with open(self.env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line in content.split('\n'):
                if line.strip().startswith('ELASTICSEARCH_VECTOR_DIMENSION='):
                    dimension_str = line.split('=')[1].strip()
                    return int(dimension_str)
                    
            self.log_message("未找到 ELASTICSEARCH_VECTOR_DIMENSION 配置", "WARNING")
            return None
            
        except Exception as e:
            self.log_message(f"讀取當前維度配置失敗: {e}", "ERROR")
            return None
    
    def backup_configuration(self) -> bool:
        """備份當前配置"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # 備份 .env 文件
            if self.env_file.exists():
                shutil.copy2(self.env_file, backup_path / ".env")
                self.log_message(f"已備份 .env 文件到 {backup_path}")
            
            # 備份 mapping 配置
            mapping_file = self.project_root / "config" / "elasticsearch" / "index_mapping.json"
            if mapping_file.exists():
                shutil.copy2(mapping_file, backup_path / "index_mapping.json")
                self.log_message(f"已備份 mapping 配置")
            
            # 備份 config.py
            config_file = self.project_root / "config" / "config.py"
            if config_file.exists():
                shutil.copy2(config_file, backup_path / "config.py")
                self.log_message(f"已備份 config.py")
            
            # 記錄備份信息
            backup_info = {
                "timestamp": timestamp,
                "backup_path": str(backup_path),
                "original_dimension": self.get_current_dimension(),
                "files_backed_up": [".env", "index_mapping.json", "config.py"]
            }
            
            with open(backup_path / "backup_info.json", 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"配置備份完成: {backup_path}")
            return True
            
        except Exception as e:
            self.log_message(f"配置備份失敗: {e}", "ERROR")
            return False
    
    def update_env_dimension(self, new_dimension: int) -> bool:
        """更新 .env 文件中的維度配置"""
        try:
            if not self.env_file.exists():
                self.log_message("未找到 .env 文件", "ERROR")
                return False
            
            with open(self.env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith('ELASTICSEARCH_VECTOR_DIMENSION='):
                    lines[i] = f"ELASTICSEARCH_VECTOR_DIMENSION={new_dimension}\n"
                    updated = True
                    break
            
            if not updated:
                # 如果沒有找到，添加到文件末尾
                lines.append(f"\nELASTICSEARCH_VECTOR_DIMENSION={new_dimension}\n")
            
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.log_message(f"已更新 .env 文件，新維度: {new_dimension}")
            return True
            
        except Exception as e:
            self.log_message(f"更新 .env 文件失敗: {e}", "ERROR")
            return False
    
    def update_config_py(self, new_dimension: int) -> bool:
        """更新 config.py 文件中的默認維度"""
        try:
            config_file = self.project_root / "config" / "config.py"
            
            if not config_file.exists():
                self.log_message("未找到 config.py 文件", "WARNING")
                return True  # 不是必須的，所以返回 True
            
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新默認維度配置
            import re
            pattern = r'ELASTICSEARCH_VECTOR_DIMENSION = int\(os\.getenv\("ELASTICSEARCH_VECTOR_DIMENSION", (\d+)\)\)'
            replacement = f'ELASTICSEARCH_VECTOR_DIMENSION = int(os.getenv("ELASTICSEARCH_VECTOR_DIMENSION", {new_dimension}))'
            
            new_content = re.sub(pattern, replacement, content)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.log_message(f"已更新 config.py 默認維度: {new_dimension}")
            return True
            
        except Exception as e:
            self.log_message(f"更新 config.py 失敗: {e}", "ERROR")
            return False
    
    def stop_services(self) -> bool:
        """停止 Docker 服務"""
        try:
            self.log_message("正在停止 Docker 服務...")
            
            import subprocess
            result = subprocess.run(
                ["docker-compose", "down"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log_message("Docker 服務已停止")
                return True
            else:
                self.log_message(f"停止服務失敗: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("停止服務超時", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"停止服務時發生錯誤: {e}", "ERROR")
            return False
    
    def start_services(self) -> bool:
        """啟動 Docker 服務"""
        try:
            self.log_message("正在啟動 Docker 服務...")
            
            import subprocess
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log_message("Docker 服務已啟動")
                return True
            else:
                self.log_message(f"啟動服務失敗: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("啟動服務超時", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"啟動服務時發生錯誤: {e}", "ERROR")
            return False
    
    def wait_for_elasticsearch(self, max_wait: int = 60) -> bool:
        """等待 Elasticsearch 服務就緒"""
        try:
            self.log_message("等待 Elasticsearch 服務就緒...")
            
            import requests
            
            for i in range(max_wait):
                try:
                    response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
                    if response.status_code == 200:
                        health = response.json()
                        if health.get('status') in ['yellow', 'green']:
                            self.log_message(f"Elasticsearch 服務就緒 (狀態: {health.get('status')})")
                            return True
                except requests.RequestException:
                    pass
                
                time.sleep(1)
                if i % 10 == 0:
                    self.log_message(f"等待中... ({i}/{max_wait}s)")
            
            self.log_message("等待 Elasticsearch 超時", "ERROR")
            return False
            
        except Exception as e:
            self.log_message(f"等待 Elasticsearch 時發生錯誤: {e}", "ERROR")
            return False
    
    def verify_new_dimension(self, expected_dimension: int) -> bool:
        """驗證新維度配置"""
        try:
            self.log_message(f"驗證新維度配置: {expected_dimension}")
            
            # 等待容器完全啟動
            time.sleep(10)
            
            import subprocess
            result = subprocess.run(
                ["docker", "exec", "rag-intelligent-assistant", "python", "-c", 
                 "import os; from config.config import ELASTICSEARCH_VECTOR_DIMENSION; print(f'DIMENSION={ELASTICSEARCH_VECTOR_DIMENSION}')"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if f"DIMENSION={expected_dimension}" in output:
                    self.log_message("維度配置驗證成功")
                    return True
                else:
                    self.log_message(f"維度配置不符預期: {output}", "ERROR")
                    return False
            else:
                self.log_message(f"驗證命令執行失敗: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"驗證新維度時發生錯誤: {e}", "ERROR")
            return False
    
    def test_embedding_generation(self, expected_dimension: int) -> bool:
        """測試嵌入生成功能"""
        try:
            self.log_message("測試嵌入生成功能...")
            
            import subprocess
            test_script = f"""
import sys
sys.path.append('/app')
from src.utils.embedding_fix import SafeJinaEmbedding
import os

api_key = os.getenv('JINA_API_KEY')
embedding_model = SafeJinaEmbedding(
    api_key=api_key,
    model='jina-embeddings-v3',
    dimensions={expected_dimension}
)

test_text = '測試文本'
embedding = embedding_model.get_text_embedding(test_text)
actual_dim = len(embedding)

print(f'EXPECTED={expected_dimension}')
print(f'ACTUAL={actual_dim}')
print(f'SUCCESS={actual_dim == {expected_dimension}}')
"""
            
            result = subprocess.run(
                ["docker", "exec", "rag-intelligent-assistant", "python", "-c", test_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "SUCCESS=True" in output:
                    self.log_message("嵌入生成測試成功")
                    return True
                else:
                    self.log_message(f"嵌入維度不符預期: {output}", "ERROR")
                    return False
            else:
                self.log_message(f"嵌入測試失敗: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"測試嵌入生成時發生錯誤: {e}", "ERROR")
            return False
    
    def cleanup_elasticsearch_data(self) -> bool:
        """清理 Elasticsearch 數據（可選）"""
        try:
            es_data_dir = self.project_root / "elasticsearch_data"
            
            if es_data_dir.exists():
                self.log_message("清理 Elasticsearch 數據目錄...")
                shutil.rmtree(es_data_dir)
                self.log_message("Elasticsearch 數據已清理")
            else:
                self.log_message("未找到 Elasticsearch 數據目錄")
            
            return True
            
        except Exception as e:
            self.log_message(f"清理數據時發生錯誤: {e}", "ERROR")
            return False
    
    def migrate_dimension(self, target_dimension: int, cleanup_data: bool = True) -> bool:
        """執行完整的維度遷移"""
        self.log_message(f"開始維度遷移: 目標維度 {target_dimension}")
        
        # 1. 獲取當前維度
        current_dimension = self.get_current_dimension()
        if current_dimension is None:
            self.log_message("無法獲取當前維度，終止遷移", "ERROR")
            return False
        
        if current_dimension == target_dimension:
            self.log_message(f"當前維度已是 {target_dimension}，無需遷移")
            return True
        
        self.log_message(f"當前維度: {current_dimension} -> 目標維度: {target_dimension}")
        
        # 2. 備份配置
        if not self.backup_configuration():
            self.log_message("配置備份失敗，終止遷移", "ERROR")
            return False
        
        # 3. 停止服務
        if not self.stop_services():
            self.log_message("停止服務失敗，終止遷移", "ERROR")
            return False
        
        # 4. 清理數據（如果需要）
        if cleanup_data:
            if not self.cleanup_elasticsearch_data():
                self.log_message("數據清理失敗，但繼續遷移", "WARNING")
        
        # 5. 更新配置文件
        if not self.update_env_dimension(target_dimension):
            self.log_message("更新 .env 失敗，終止遷移", "ERROR")
            return False
        
        if not self.update_config_py(target_dimension):
            self.log_message("更新 config.py 失敗，但繼續遷移", "WARNING")
        
        # 6. 啟動服務
        if not self.start_services():
            self.log_message("啟動服務失敗，終止遷移", "ERROR")
            return False
        
        # 7. 等待服務就緒
        if not self.wait_for_elasticsearch():
            self.log_message("Elasticsearch 服務未就緒，但繼續驗證", "WARNING")
        
        # 8. 驗證新配置
        if not self.verify_new_dimension(target_dimension):
            self.log_message("維度驗證失敗", "ERROR")
            return False
        
        # 9. 測試嵌入生成
        if not self.test_embedding_generation(target_dimension):
            self.log_message("嵌入生成測試失敗", "ERROR")
            return False
        
        self.log_message(f"維度遷移成功完成！{current_dimension} -> {target_dimension}")
        return True

def main():
    """主函數"""
    print("🚀 Elasticsearch 向量維度遷移工具")
    print("=" * 50)
    
    migrator = DimensionMigrator()
    
    # 顯示當前維度
    current_dim = migrator.get_current_dimension()
    if current_dim:
        print(f"📊 當前維度: {current_dim}")
    else:
        print("❌ 無法讀取當前維度")
        return 1
    
    # 獲取目標維度
    target_dim = 128  # 根據研究建議的最佳維度
    
    print(f"🎯 目標維度: {target_dim}")
    print(f"💾 清理數據: 是")
    
    # 確認遷移
    print(f"\n⚠️  注意事項:")
    print(f"   - 此操作將清理所有現有的 Elasticsearch 數據")
    print(f"   - 需要重新索引所有文檔")
    print(f"   - 服務將暫時中斷")
    print(f"   - 配置文件將被備份")
    
    confirm = input(f"\n確認要從 {current_dim} 維度遷移到 {target_dim} 維度嗎？(y/N): ").strip().lower()
    
    if confirm != 'y':
        print("❌ 遷移已取消")
        return 0
    
    # 執行遷移
    success = migrator.migrate_dimension(target_dim, cleanup_data=True)
    
    if success:
        print(f"\n✅ 維度遷移成功完成！")
        print(f"📋 遷移日誌: {migrator.migration_log}")
        print(f"💾 配置備份: {migrator.backup_dir}")
        print(f"\n🔄 後續步驟:")
        print(f"   1. 重新上傳並索引文檔")
        print(f"   2. 驗證查詢結果質量")
        print(f"   3. 監控系統性能")
        return 0
    else:
        print(f"\n❌ 維度遷移失敗！")
        print(f"📋 詳細日誌: {migrator.migration_log}")
        print(f"💾 可從備份恢復: {migrator.backup_dir}")
        return 1

if __name__ == "__main__":
    sys.exit(main())