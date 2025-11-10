"""
Dashboard服务 - 管理统计数据和处理记录
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Literal, Optional
from collections import deque
import threading

from app.schemas.dashboard import (
    DashboardStats,
    ProcessRecord,
    RecentRecordsResponse,
    DashboardData,
)

# 时间节约估算（单位：分钟/条记录）
TIME_SAVING_RATES = {
    "费用清单转凭证": 2.5,  # 每条记录节约2.5分钟
    "摘要翻译": 1.5,          # 每条翻译节约1.5分钟
    "银行流水转凭证": 4.0,  # 每条流水节约4分钟
}


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

        # 统计数据（不再统计金额，改为统计记录条数）
        self._stats = {
            "voucher_count": 0,
            "translate_count": 0,
            "bank_statement_count": 0,
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
        record_count: int = 0,
    ) -> str:
        """
        添加处理记录

        Args:
            tool: 使用的工具
            file_name: 文件名
            status: 处理状态
            duration: 处理时长(秒)
            record_count: 处理记录条数

        Returns:
            记录ID
        """
        record_id = str(uuid.uuid4())
        now = datetime.now()
        record = ProcessRecord(
            id=record_id,
            time=now.strftime("%Y-%m-%d %H:%M:%S"),
            tool=tool,
            file_name=file_name,
            status=status,
            duration=f"{duration:.1f}s",
            record_count=record_count,
        )

        with self._records_lock:
            self._records.appendleft(record)  # 新记录放在最前面

        # 如果成功，更新统计数据
        if status == "成功":
            self._update_stats(tool, record_count, duration)

        return record_id

    def _update_stats(
        self, tool: str, record_count: int, duration: float
    ):
        """更新统计数据"""
        with self._stats_lock:
            if tool == "费用清单转凭证":
                self._stats["voucher_count"] += record_count
            elif tool == "摘要翻译":
                self._stats["translate_count"] += record_count
            elif tool == "银行流水转凭证":
                self._stats["bank_statement_count"] += record_count

            self._stats["total_process_time"] += duration
            self._stats["process_count"] += 1

    def get_stats(self) -> DashboardStats:
        """获取统计数据，包含时间节约计算"""
        with self._stats_lock:
            avg_time = 0.0
            if self._stats["process_count"] > 0:
                avg_time = (
                    self._stats["total_process_time"]
                    / self._stats["process_count"]
                )

        # 计算不同时间范围的时间节约
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        time_saved = {
            "today": 0.0,
            "week": 0.0,
            "month": 0.0,
            "year": 0.0,
            "total": 0.0,
        }

        with self._records_lock:
            for record in self._records:
                # 只统计成功的记录
                if record.status != "成功":
                    continue

                # 解析记录时间
                try:
                    record_time = datetime.strptime(record.time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue

                # 计算该记录节约的时间
                saved_minutes = TIME_SAVING_RATES.get(record.tool, 0) * record.record_count

                # 累加到总计
                time_saved["total"] += saved_minutes

                # 今日
                if record_time >= today_start:
                    time_saved["today"] += saved_minutes

                # 本周
                if record_time >= week_start:
                    time_saved["week"] += saved_minutes

                # 本月
                if record_time >= month_start:
                    time_saved["month"] += saved_minutes

                # 本年
                if record_time >= year_start:
                    time_saved["year"] += saved_minutes

        with self._stats_lock:
            return DashboardStats(
                voucher_count=self._stats["voucher_count"],
                translate_count=self._stats["translate_count"],
                bank_statement_count=self._stats["bank_statement_count"],
                avg_process_time=round(avg_time, 1),
                time_saved_today=round(time_saved["today"], 1),
                time_saved_week=round(time_saved["week"], 1),
                time_saved_month=round(time_saved["month"], 1),
                time_saved_year=round(time_saved["year"], 1),
                time_saved_total=round(time_saved["total"], 1),
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
                "bank_statement_count": 0,
                "total_process_time": 0.0,
                "process_count": 0,
            }

    def clear_records(self):
        """清空记录(仅用于测试)"""
        with self._records_lock:
            self._records.clear()


# 创建全局单例
dashboard_service = DashboardService()
