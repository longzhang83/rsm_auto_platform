from __future__ import annotations

from typing import Optional

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