"""
統一日誌配置模組
提供結構化日誌記錄，包含時間、程式、行號、錯誤等級等詳細資訊
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
import traceback
import json


class DetailedFormatter(logging.Formatter):
    """詳細格式化器，包含所有必要資訊"""
    
    def __init__(self):
        super().__init__()
    
    def format(self, record):
        # 創建詳細的日誌格式
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 獲取調用者資訊
        filename = os.path.basename(record.pathname)
        
        # 構建基本日誌訊息
        log_parts = [
            f"[{log_time}]",
            f"[{record.levelname:8s}]",
            f"[{filename}:{record.lineno}]",
            f"[{record.funcName}()]"
        ]
        
        # 如果有模組資訊，添加進去
        if hasattr(record, 'module'):
            log_parts.append(f"[{record.module}]")
        
        # 添加主要訊息
        message = record.getMessage()
        
        # 如果是異常，添加堆疊追蹤
        if record.exc_info:
            exc_text = ''.join(traceback.format_exception(*record.exc_info))
            message += f"\n堆疊追蹤:\n{exc_text}"
        
        return " ".join(log_parts) + f" - {message}"


class JSONFormatter(logging.Formatter):
    """JSON格式化器，便於程式解析"""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": os.path.basename(record.pathname),
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.thread,
            "thread_name": record.threadName
        }
        
        # 添加異常資訊
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # 添加額外字段
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'exc_info', 'exc_text', 
                          'stack_info']:
                log_obj[key] = value
        
        return json.dumps(log_obj, ensure_ascii=False, default=str)


def setup_logging(
    app_name: str,
    log_level: str = "INFO",
    log_dir: str = "/app/logs",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    設置統一的日誌配置
    
    Args:
        app_name: 應用程式名稱
        log_level: 日誌等級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日誌目錄
        enable_console: 是否啟用控制台輸出
        enable_file: 是否啟用文件輸出
        enable_json: 是否啟用JSON格式日誌
        max_file_size: 日誌檔案最大大小（位元組）
        backup_count: 保留的備份檔案數量
    """
    
    # 創建日誌目錄
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # 設置根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除現有處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台處理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(DetailedFormatter())
        root_logger.addHandler(console_handler)
    
    # 文件處理器（詳細格式）
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir_path / f"{app_name}.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(DetailedFormatter())
        root_logger.addHandler(file_handler)
    
    # JSON日誌處理器（便於分析）
    if enable_json:
        json_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir_path / f"{app_name}.json.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(getattr(logging, log_level.upper()))
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    # 錯誤專用日誌
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir_path / f"{app_name}_errors.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(DetailedFormatter())
    root_logger.addHandler(error_handler)
    
    # 記錄日誌系統啟動
    logger = logging.getLogger(f"{app_name}.logging")
    logger.info(f"🚀 日誌系統啟動完成")
    logger.info(f"   - 應用程式: {app_name}")
    logger.info(f"   - 日誌等級: {log_level}")
    logger.info(f"   - 日誌目錄: {log_dir}")
    logger.info(f"   - 控制台輸出: {enable_console}")
    logger.info(f"   - 文件輸出: {enable_file}")
    logger.info(f"   - JSON輸出: {enable_json}")
    
    return logger


def get_logger(name: str):
    """獲取具名日誌器"""
    return logging.getLogger(name)


def log_exception(logger, message: str, exc_info=None):
    """記錄異常的便利函數"""
    if exc_info is None:
        exc_info = sys.exc_info()
    
    logger.error(message, exc_info=exc_info)


def log_function_call(logger, func_name: str, args=None, kwargs=None):
    """記錄函數調用"""
    call_info = f"🔧 調用函數: {func_name}()"
    if args:
        call_info += f" args={args}"
    if kwargs:
        call_info += f" kwargs={kwargs}"
    logger.debug(call_info)


def log_performance(logger, operation: str, duration: float, details=None):
    """記錄性能指標"""
    perf_info = f"⏱️ 性能: {operation} 耗時 {duration:.3f}秒"
    if details:
        perf_info += f" - {details}"
    logger.info(perf_info)


# 預定義的模組日誌器
def get_api_logger():
    return get_logger("rag_api")

def get_dashboard_logger():
    return get_logger("rag_dashboard")

def get_rag_logger():
    return get_logger("rag_system")

def get_elasticsearch_logger():
    return get_logger("elasticsearch")

def get_upload_logger():
    return get_logger("upload")