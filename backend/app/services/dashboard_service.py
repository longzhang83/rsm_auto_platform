"""
Dashboard服务 - 管理统计数据和处理记录（数据库持久化）
"""

import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models import ProcessRecord as ProcessRecordModel, User
from app.schemas.dashboard import (
    DashboardStats,
    ProcessRecord,
    RecentRecordsResponse,
    DashboardData,
    ProcessRecordWithUser,
    ProcessRecordsListResponse,
)

# 时间节约估算（单位：分钟/条记录）
# 基于实际手工处理复杂度估算
TIME_SAVING_RATES = {
    "费用清单转凭证": 3.5,  # 每条记录节约3.5分钟（需查找员工、匹配科目、填写凭证、翻译摘要、核对平衡）
    "摘要翻译": 1.5,  # 每条翻译节约1.5分钟（理解术语、查字典、输入翻译）
    "银行流水转凭证": 5.0,  # 每条流水节约5分钟（三重映射系统：银行账号、交易对手、摘要关键词，数据量大）
}


class DashboardService:
    """Dashboard服务 - 使用数据库持久化存储"""

    @staticmethod
    def add_record(
        db: Session,
        tool: Literal["费用清单转凭证", "摘要翻译", "银行流水转凭证"],
        file_name: str,
        status: Literal["成功", "失败", "处理中"],
        duration: float,
        record_count: int = 0,
        user_id: Optional[int] = None,
    ) -> str:
        """
        添加处理记录到数据库

        Args:
            db: 数据库会话
            tool: 使用的工具
            file_name: 文件名
            status: 处理状态
            duration: 处理时长(秒)
            record_count: 处理记录条数
            user_id: 用户ID（可选）

        Returns:
            记录ID
        """
        record_id = str(uuid.uuid4())

        db_record = ProcessRecordModel(
            id=record_id,
            tool=tool,
            file_name=file_name,
            status=status,
            duration=duration,
            record_count=record_count,
            user_id=user_id,
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return record_id

    @staticmethod
    def get_stats(db: Session) -> DashboardStats:
        """
        获取统计数据，包含时间节约计算（从数据库查询）

        Args:
            db: 数据库会话

        Returns:
            统计数据
        """
        # 查询所有成功的记录数量（按工具分类）
        voucher_count = (
            db.query(func.sum(ProcessRecordModel.record_count))
            .filter(
                and_(
                    ProcessRecordModel.tool == "费用清单转凭证",
                    ProcessRecordModel.status == "成功",
                )
            )
            .scalar()
            or 0
        )

        translate_count = (
            db.query(func.sum(ProcessRecordModel.record_count))
            .filter(
                and_(
                    ProcessRecordModel.tool == "摘要翻译",
                    ProcessRecordModel.status == "成功",
                )
            )
            .scalar()
            or 0
        )

        bank_statement_count = (
            db.query(func.sum(ProcessRecordModel.record_count))
            .filter(
                and_(
                    ProcessRecordModel.tool == "银行流水转凭证",
                    ProcessRecordModel.status == "成功",
                )
            )
            .scalar()
            or 0
        )

        # 计算平均处理时间（所有成功的记录）
        avg_time_result = (
            db.query(func.avg(ProcessRecordModel.duration))
            .filter(ProcessRecordModel.status == "成功")
            .scalar()
        )
        avg_time = float(avg_time_result) if avg_time_result else 0.0

        # 计算不同时间范围的时间节约
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # 查询各个时间范围的记录
        def calculate_time_saved(start_time: Optional[datetime] = None) -> float:
            """计算时间节约（分钟）"""
            query = db.query(
                ProcessRecordModel.tool,
                func.sum(ProcessRecordModel.record_count).label("count"),
            ).filter(ProcessRecordModel.status == "成功")

            if start_time:
                query = query.filter(ProcessRecordModel.created_at >= start_time)

            results = query.group_by(ProcessRecordModel.tool).all()

            total_saved = 0.0
            for tool, count in results:
                rate = TIME_SAVING_RATES.get(tool, 0)
                total_saved += rate * (count or 0)

            return total_saved

        time_saved_today = calculate_time_saved(today_start)
        time_saved_week = calculate_time_saved(week_start)
        time_saved_month = calculate_time_saved(month_start)
        time_saved_year = calculate_time_saved(year_start)
        time_saved_total = calculate_time_saved()

        return DashboardStats(
            voucher_count=int(voucher_count),
            translate_count=int(translate_count),
            bank_statement_count=int(bank_statement_count),
            avg_process_time=round(avg_time, 1),
            time_saved_today=round(time_saved_today, 1),
            time_saved_week=round(time_saved_week, 1),
            time_saved_month=round(time_saved_month, 1),
            time_saved_year=round(time_saved_year, 1),
            time_saved_total=round(time_saved_total, 1),
        )

    @staticmethod
    def get_recent_records(db: Session, limit: int = 10) -> RecentRecordsResponse:
        """
        获取最近的处理记录（从数据库查询）

        Args:
            db: 数据库会话
            limit: 返回记录数量

        Returns:
            最近的记录列表
        """
        # 查询最近的记录，按创建时间降序
        db_records = (
            db.query(ProcessRecordModel)
            .order_by(ProcessRecordModel.created_at.desc())
            .limit(limit)
            .all()
        )

        # 获取总记录数
        total = db.query(func.count(ProcessRecordModel.id)).scalar() or 0

        # 转换为schema对象
        records = []
        for db_record in db_records:
            records.append(
                ProcessRecord(
                    id=db_record.id,
                    time=db_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    tool=db_record.tool,
                    file_name=db_record.file_name,
                    status=db_record.status,
                    duration=f"{db_record.duration:.1f}s",
                    record_count=db_record.record_count,
                )
            )

        return RecentRecordsResponse(
            records=records,
            total=total,
        )

    @staticmethod
    def get_dashboard_data(db: Session) -> DashboardData:
        """
        获取完整的dashboard数据

        Args:
            db: 数据库会话

        Returns:
            Dashboard完整数据
        """
        stats = DashboardService.get_stats(db)
        recent = DashboardService.get_recent_records(db)

        return DashboardData(
            stats=stats,
            recent_records=recent.records,
            last_update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    def update_record_status(
        db: Session, record_id: str, status: Literal["成功", "失败", "处理中"]
    ) -> bool:
        """
        更新记录状态

        Args:
            db: 数据库会话
            record_id: 记录ID
            status: 新状态

        Returns:
            是否更新成功
        """
        db_record = (
            db.query(ProcessRecordModel)
            .filter(ProcessRecordModel.id == record_id)
            .first()
        )

        if db_record:
            db_record.status = status
            db.commit()
            return True

        return False

    @staticmethod
    def get_record(db: Session, record_id: str) -> Optional[ProcessRecord]:
        """
        获取指定记录

        Args:
            db: 数据库会话
            record_id: 记录ID

        Returns:
            记录对象，如果不存在则返回None
        """
        db_record = (
            db.query(ProcessRecordModel)
            .filter(ProcessRecordModel.id == record_id)
            .first()
        )

        if db_record:
            return ProcessRecord(
                id=db_record.id,
                time=db_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                tool=db_record.tool,
                file_name=db_record.file_name,
                status=db_record.status,
                duration=f"{db_record.duration:.1f}s",
                record_count=db_record.record_count,
            )

        return None

    @staticmethod
    def get_records_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        tool: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ProcessRecordsListResponse:
        """
        获取处理记录列表（支持分页和过滤）

        Args:
            db: 数据库会话
            page: 页码（从1开始）
            page_size: 每页数量
            tool: 工具类型过滤（可选）
            status: 状态过滤（可选）
            start_date: 开始日期过滤（可选，格式：YYYY-MM-DD）
            end_date: 结束日期过滤（可选，格式：YYYY-MM-DD）

        Returns:
            分页的处理记录列表（包含用户信息）
        """
        from datetime import datetime, timezone

        # 构建查询
        query = db.query(ProcessRecordModel, User).outerjoin(
            User, ProcessRecordModel.user_id == User.id
        )

        # 应用过滤条件
        if tool:
            query = query.filter(ProcessRecordModel.tool == tool)

        if status:
            query = query.filter(ProcessRecordModel.status == status)

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(ProcessRecordModel.created_at >= start_dt)
            except ValueError:
                pass  # 忽略无效日期格式

        if end_date:
            try:
                # 结束日期包含当天，所以加1天
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(ProcessRecordModel.created_at <= end_dt)
            except ValueError:
                pass  # 忽略无效日期格式

        # 获取总数
        total = query.count()

        # 分页查询，按创建时间降序
        offset = (page - 1) * page_size
        results = (
            query.order_by(ProcessRecordModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # 转换为schema对象
        records = []
        for db_record, user in results:
            # 获取用户名（优先使用企业微信名称，其次使用用户名）
            user_name = None
            if user:
                user_name = user.wework_name or user.username

            # 确保时间包含时区信息（UTC）
            created_at = db_record.created_at
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            time_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else ""

            records.append(
                ProcessRecordWithUser(
                    id=db_record.id,
                    time=time_str,
                    tool=db_record.tool,
                    file_name=db_record.file_name,
                    status=db_record.status,
                    duration=f"{db_record.duration:.1f}s",
                    record_count=db_record.record_count,
                    user=user_name,
                )
            )

        return ProcessRecordsListResponse(
            records=records,
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def clear_stats(db: Session):
        """清空所有统计数据(仅用于测试)"""
        db.query(ProcessRecordModel).delete()
        db.commit()

    @staticmethod
    def clear_records(db: Session):
        """清空所有记录(仅用于测试)"""
        db.query(ProcessRecordModel).delete()
        db.commit()


# 向后兼容：创建单例包装器
class _DashboardServiceSingleton:
    """Dashboard服务单例包装器 - 保持向后兼容"""

    def add_record(self, *args, **kwargs):
        """需要注入db参数"""
        raise NotImplementedError(
            "请使用 DashboardService.add_record(db, ...) 并传入数据库会话"
        )

    def get_stats(self, *args, **kwargs):
        """需要注入db参数"""
        raise NotImplementedError(
            "请使用 DashboardService.get_stats(db) 并传入数据库会话"
        )

    def get_recent_records(self, *args, **kwargs):
        """需要注入db参数"""
        raise NotImplementedError(
            "请使用 DashboardService.get_recent_records(db) 并传入数据库会话"
        )


# 保持向后兼容的全局单例（但提示需要迁移）
dashboard_service = _DashboardServiceSingleton()
