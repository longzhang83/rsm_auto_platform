"""
独立的日志管理模块

提供灵活的日志配置和管理功能，支持多种输出方式和格式化选项。
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
import json

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }

    def format(self, record):
        # 添加颜色
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = record.task_id

        return json.dumps(log_entry, ensure_ascii=False)


class LogManager:
    """日志管理器"""

    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: Dict[str, logging.Handler] = {}
        self.is_configured = False

    def setup_logging(
        self,
        level: str = "INFO",
        log_dir: Optional[Union[str, Path]] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        colored_console: bool = True,
    ):
        """设置全局日志配置"""

        # 创建日志目录
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
        else:
            # 使用项目根目录下的logs文件夹
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))

        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 控制台处理器
        if enable_console:
            # Windows下修复中文乱码问题
            if sys.platform == "win32":
                import io
                # 重新配置stdout和stderr为UTF-8编码
                if hasattr(sys.stdout, 'buffer'):
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'buffer'):
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

            console_handler = logging.StreamHandler(sys.stdout)
            if colored_console:
                console_formatter = ColoredFormatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setStream(sys.stdout)  # 确保使用UTF-8编码的流
            root_logger.addHandler(console_handler)
            self.handlers['console'] = console_handler

        # 文件处理器（普通文本）
        if enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_dir / "app.log",
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(getattr(logging, level.upper()))
            root_logger.addHandler(file_handler)
            self.handlers['file'] = file_handler

        # JSON文件处理器
        if enable_json:
            json_handler = logging.handlers.RotatingFileHandler(
                filename=log_dir / "app.json.log",
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            json_formatter = JSONFormatter()
            json_handler.setFormatter(json_formatter)
            json_handler.setLevel(getattr(logging, level.upper()))
            root_logger.addHandler(json_handler)
            self.handlers['json'] = json_handler

        # 错误日志单独处理器
        error_handler = logging.handlers.RotatingFileHandler(
            filename=log_dir / "error.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n'
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        self.handlers['error'] = error_handler

        self.is_configured = True

        # 记录日志配置完成
        logger = self.get_logger(__name__)
        logger.info(f"日志系统初始化完成 - 级别: {level}, 目录: {log_dir}")
        if enable_file:
            logger.info(f"文件日志: {log_dir / 'app.log'}")
        if enable_json:
            logger.info(f"JSON日志: {log_dir / 'app.json.log'}")

        # 关闭干扰性的第三方库DEBUG日志
        logging.getLogger('python_multipart.multipart').setLevel(logging.WARNING)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
        logging.getLogger('uvicorn').setLevel(logging.INFO)  # 只显示INFO及以上级别

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger

            # 如果还没有配置，使用基础配置
            if not self.is_configured:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)

        return self.loggers[name]

    def set_level(self, logger_name: str, level: str):
        """设置指定日志器的级别"""
        logger = self.get_logger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))

    def add_custom_handler(
        self,
        handler_name: str,
        handler: logging.Handler,
        logger_names: Optional[List[str]] = None
    ):
        """添加自定义处理器"""
        self.handlers[handler_name] = handler

        if logger_names:
            for logger_name in logger_names:
                logger = self.get_logger(logger_name)
                logger.addHandler(handler)
        else:
            # 添加到根日志器
            logging.getLogger().addHandler(handler)

    def create_module_logger(
        self,
        module_name: str,
        level: str = "INFO",
        filename: Optional[str] = None,
        **kwargs
    ) -> logging.Logger:
        """为特定模块创建独立的日志器"""

        logger = logging.getLogger(module_name)
        logger.setLevel(getattr(logging, level.upper()))

        # 如果指定了文件名，创建文件处理器
        if filename and hasattr(settings, 'log_dir'):
            log_file = settings.log_dir / filename
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                **kwargs
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.loggers[module_name] = logger
        return logger

    def log_request(
        self,
        logger: logging.Logger,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """记录HTTP请求日志"""
        extra = {}
        if user_id:
            extra['user_id'] = user_id
        if request_id:
            extra['request_id'] = request_id

        message = f"{method} {path} - {status_code} - {duration:.3f}s"

        if status_code >= 400:
            logger.error(message, extra=extra)
        else:
            logger.info(message, extra=extra)

    def log_translation_progress(
        self,
        logger: logging.Logger,
        task_id: str,
        percentage: float,
        message: str,
        completed: int = 0,
        total: int = 0,
        current_item: str = ""
    ):
        """记录翻译进度日志"""
        extra = {
            'task_id': task_id,
            'percentage': percentage,
            'completed': completed,
            'total': total
        }

        log_message = f"[{task_id}] {percentage:.1f}% - {message}"
        if completed > 0 and total > 0:
            log_message += f" ({completed}/{total})"
        if current_item:
            log_message += f" - 当前: {current_item[:50]}"

        logger.info(log_message, extra=extra)

    def get_log_files(self) -> Dict[str, Path]:
        """获取所有日志文件路径"""
        log_dir = Path("logs")
        return {
            "app": log_dir / "app.log",
            "json": log_dir / "app.json.log",
            "error": log_dir / "error.log"
        }

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)

        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.get_logger(__name__).info(f"删除旧日志文件: {log_file}")
                except Exception as e:
                    self.get_logger(__name__).error(f"删除日志文件失败 {log_file}: {e}")


# 全局日志管理器实例
log_manager = LogManager()


def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return log_manager.get_logger(name)


def setup_logging(**kwargs):
    """设置日志的便捷函数"""
    log_manager.setup_logging(**kwargs)


# 预定义的模块日志器
def get_translation_logger() -> logging.Logger:
    """获取翻译模块日志器"""
    return log_manager.get_logger('accounting_voucher_generation.async_translator')


def get_summary_logger() -> logging.Logger:
    """获取摘要翻译模块日志器"""
    return log_manager.get_logger('accounting_voucher_generation.summary_translator')


def get_api_logger() -> logging.Logger:
    """获取API模块日志器"""
    return log_manager.get_logger('app.api')


def get_service_logger() -> logging.Logger:
    """获取服务模块日志器"""
    return log_manager.get_logger('app.services')


# 日志装饰器
def log_function_call(logger: Optional[logging.Logger] = None):
    """记录函数调用的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            logger.debug(f"调用函数: {func.__name__} - 参数: args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}")
                raise
        return wrapper
    return decorator


async def log_async_function_call(logger: Optional[logging.Logger] = None):
    """记录异步函数调用的装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            logger.debug(f"调用异步函数: {func.__name__} - 参数: args={args}, kwargs={kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"异步函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"异步函数 {func.__name__} 执行失败: {e}")
                raise
        return wrapper
    return decorator