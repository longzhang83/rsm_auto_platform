from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """翻译请求模型"""
    summary_column: str = Field(default="费用摘要", description="摘要列名")
    sheet_name: Optional[str] = Field(None, description="工作表名称")
    output_column: str = Field(default="摘要翻译", description="输出列名")
    force: bool = Field(default=False, description="是否强制重新翻译")
    target_language: str = Field(default="en", description="目标语言: 'en' for English, 'zh' for Chinese")


class TranslateResponse(BaseModel):
    """翻译响应模型"""
    message: str = Field(..., description="响应消息")
    total_items: int = Field(..., description="翻译项目总数")
    translated_count: int = Field(..., description="已翻译数量")
    download_url: Optional[str] = Field(None, description="下载链接")
    target_language: str = Field(..., description="使用的目标语言")
    task_id: Optional[str] = Field(None, description="任务ID，用于进度查询")


class CacheItem(BaseModel):
    """翻译缓存条目模型"""
    source: str = Field(..., description="原文")
    target: str = Field(..., description="译文")
    usage_count: int = Field(default=0, description="使用次数")
    last_used: str = Field(default="", description="最后使用时间")


class CacheUpdateRequest(BaseModel):
    """缓存更新请求模型"""
    source: str = Field(..., description="原文")
    target: str = Field(..., description="译文")


class TranslationStats(BaseModel):
    """翻译统计模型"""
    service_type: str = Field(..., description="服务类型")
    runtime_hours: Optional[float] = Field(None, description="运行时长（小时）")
    total_requests: Optional[int] = Field(None, description="总请求数")
    cache_hits: Optional[int] = Field(None, description="缓存命中数")
    cache_hit_rate: Optional[str] = Field(None, description="缓存命中率")
    errors: Optional[int] = Field(None, description="错误数")
    cache_size: Optional[int] = Field(None, description="缓存大小")
    account_stats: Optional[List[Dict[str, Any]]] = Field(None, description="账户统计信息")
    cache_file: Optional[str] = Field(None, description="缓存文件路径")
    cache_exists: Optional[bool] = Field(None, description="缓存文件是否存在")