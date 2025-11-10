"""
Dashboard服务 - 管理统计数据和处理记录
"""
import uuid
from datetime import datetime
from typing import List, Literal, Optional
from collections import deque
import threading

from app.schemas.dashboard import (
    DashboardStats,
    ProcessRecord,
    RecentRecordsResponse,
    DashboardData,
)


class DashboardService:
    """Dashboard服务 - 单例模式"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 处理记录 - 使用deque实现固定大小的队列
        self._records = deque(maxlen=100)  # 最多保存100条记录

        # 统计数据
        self._stats = {
            "voucher_count": 0,
            "translate_count": 0,
            "total_amount": 0.0,
            "total_process_time": 0.0,
            "process_count": 0,
        }

        # 线程锁
        self._stats_lock = threading.Lock()
        self._records_lock = threading.Lock()

        self._initialized = True

    def add_record(
        self,
        tool: Literal["费用清单转凭证", "摘要翻译", "银行流水转凭证"],
        file_name: str,
        status: Literal["成功", "失败", "处理中"],
        duration: float,
        amount: float = 0.0,
    ) -> str:
        """
        添加处理记录

        Args:
            tool: 使用的工具
            file_name: 文件名
            status: 处理状态
            duration: 处理时长(秒)
            amount: 处理金额

        Returns:
            记录ID
        """
        record_id = str(uuid.uuid4())
        record = ProcessRecord(
            id=record_id,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tool=tool,
            file_name=file_name,
            status=status,
            duration=f"{duration:.1f}s",
            amount=amount,
        )

        with self._records_lock:
            self._records.appendleft(record)  # 新记录放在最前面

        # 如果成功，更新统计数据
        if status == "成功":
            self._update_stats(tool, amount, duration)

        return record_id

    def _update_stats(
        self, tool: str, amount: float, duration: float
    ):
        """更新统计数据"""
        with self._stats_lock:
            if tool == "费用清单转凭证":
                self._stats["voucher_count"] += 1
                self._stats["total_amount"] += amount
            elif tool == "摘要翻译":
                self._stats["translate_count"] += 1

            self._stats["total_process_time"] += duration
            self._stats["process_count"] += 1

    def get_stats(self) -> DashboardStats:
        """获取统计数据"""
        with self._stats_lock:
            avg_time = 0.0
            if self._stats["process_count"] > 0:
                avg_time = (
                    self._stats["total_process_time"]
                    / self._stats["process_count"]
                )

            return DashboardStats(
                voucher_count=self._stats["voucher_count"],
                translate_count=self._stats["translate_count"],
                total_amount=self._stats["total_amount"],
                avg_process_time=round(avg_time, 1),
            )

    def get_recent_records(self, limit: int = 10) -> RecentRecordsResponse:
        """获取最近的处理记录"""
        with self._records_lock:
            records = list(self._records)[:limit]
            return RecentRecordsResponse(
                records=records,
                total=len(self._records),
            )

    def get_dashboard_data(self) -> DashboardData:
        """获取完整的dashboard数据"""
        stats = self.get_stats()
        recent = self.get_recent_records()

        return DashboardData(
            stats=stats,
            recent_records=recent.records,
            last_update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def update_record_status(
        self, record_id: str, status: Literal["成功", "失败", "处理中"]
    ) -> bool:
        """
        更新记录状态

        Args:
            record_id: 记录ID
            status: 新状态

        Returns:
            是否更新成功
        """
        with self._records_lock:
            for record in self._records:
                if record.id == record_id:
                    record.status = status
                    return True
        return False

    def get_record(self, record_id: str) -> Optional[ProcessRecord]:
        """获取指定记录"""
        with self._records_lock:
            for record in self._records:
                if record.id == record_id:
                    return record
        return None

    def clear_stats(self):
        """清空统计数据(仅用于测试)"""
        with self._stats_lock:
            self._stats = {
                "voucher_count": 0,
                "translate_count": 0,
                "total_amount": 0.0,
                "total_process_time": 0.0,
                "process_count": 0,
            }

    def clear_records(self):
        """清空记录(仅用于测试)"""
        with self._records_lock:
            self._records.clear()


# 创建全局单例
dashboard_service = DashboardService()
