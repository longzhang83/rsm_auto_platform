"""
日志管理API端点
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from app.core.config import settings
from app.utils.logger import log_manager, get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/info", summary="获取日志系统信息")
async def get_log_info():
    """获取日志系统配置信息"""
    try:
        log_files = log_manager.get_log_files()

        # 检查文件是否存在和大小
        file_info = {}
        for name, path in log_files.items():
            if path.exists():
                file_info[name] = {
                    "path": str(path),
                    "exists": True,
                    "size": path.stat().st_size,
                    "modified": path.stat().st_mtime,
                }
            else:
                file_info[name] = {
                    "path": str(path),
                    "exists": False,
                    "size": 0,
                    "modified": 0,
                }

        return {
            "log_directory": str(settings.log_dir),
            "log_level": settings.log_level,
            "enable_console": settings.log_enable_console,
            "enable_file": settings.log_enable_file,
            "enable_json": settings.log_enable_json,
            "max_file_size": settings.log_max_file_size,
            "backup_count": settings.log_backup_count,
            "retention_days": settings.log_retention_days,
            "files": file_info,
        }
    except Exception as e:
        logger.error(f"获取日志信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志信息失败: {e}")


@router.get("/files", summary="获取日志文件列表")
async def get_log_files():
    """获取所有日志文件列表"""
    try:
        log_dir = settings.log_dir
        if not log_dir.exists():
            return {"files": [], "directory": str(log_dir), "exists": False}

        # 获取所有日志文件
        files = []
        for file_path in log_dir.glob("*.log*"):
            stat = file_path.stat()
            files.append(
                {
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "is_readable": os.access(file_path, os.R_OK),
                }
            )

        # 按修改时间排序
        files.sort(key=lambda x: x["modified"], reverse=True)

        return {"directory": str(log_dir), "exists": True, "files": files}
    except Exception as e:
        logger.error(f"获取日志文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志文件列表失败: {e}")


@router.get("/download/{filename}", summary="下载日志文件")
async def download_log_file(filename: str):
    """下载指定的日志文件"""
    try:
        # 安全检查：确保文件名不包含路径遍历字符
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="无效的文件名")

        log_dir = settings.log_dir
        file_path = log_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="日志文件不存在")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="指定的路径不是文件")

        # 检查文件是否为日志文件
        if not filename.endswith(
            (".log", ".log.gz", ".log.1", ".log.2", ".log.3", ".log.4", ".log.5")
        ):
            raise HTTPException(status_code=400, detail="只能下载日志文件")

        return FileResponse(path=file_path, filename=filename, media_type="text/plain")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载日志文件失败 {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"下载日志文件失败: {e}")


@router.get("/view/{filename}", summary="查看日志文件内容")
async def view_log_file(
    filename: str,
    lines: int = Query(default=100, ge=1, le=10000, description="显示的行数"),
    offset: int = Query(default=0, ge=0, description="跳过的行数"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
):
    """查看日志文件内容"""
    try:
        # 安全检查
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="无效的文件名")

        log_dir = settings.log_dir
        file_path = log_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="日志文件不存在")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="指定的路径不是文件")

        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                all_lines = f.readlines()

        # 应用搜索过滤
        if search:
            search_lower = search.lower()
            filtered_lines = [
                line for line in all_lines if search_lower in line.lower()
            ]
        else:
            filtered_lines = all_lines

        total_lines = len(filtered_lines)

        # 应用分页
        start_idx = offset
        end_idx = start_idx + lines
        page_lines = filtered_lines[start_idx:end_idx]

        return {
            "filename": filename,
            "total_lines": total_lines,
            "offset": offset,
            "lines_requested": lines,
            "lines_returned": len(page_lines),
            "has_more": end_idx < total_lines,
            "search_term": search,
            "content": "".join(page_lines),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查看日志文件失败 {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"查看日志文件失败: {e}")


@router.delete("/cleanup", summary="清理旧日志文件")
async def cleanup_old_logs(
    background_tasks: BackgroundTasks,
    days: int = Query(default=30, ge=1, le=365, description="保留天数"),
):
    """清理指定天数之前的日志文件"""
    try:
        # 在后台任务中执行清理
        background_tasks.add_task(log_manager.cleanup_old_logs, days)

        logger.info(f"已启动日志清理任务，保留 {days} 天内的日志")

        return {
            "message": "日志清理任务已启动",
            "retention_days": days,
            "status": "running",
        }
    except Exception as e:
        logger.error(f"启动日志清理任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动日志清理任务失败: {e}")


@router.get("/search", summary="搜索日志内容")
async def search_logs(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    filename: Optional[str] = Query(
        default=None, description="指定文件名，不指定则搜索所有文件"
    ),
    max_results: int = Query(default=100, ge=1, le=1000, description="最大结果数"),
):
    """在日志文件中搜索关键词"""
    try:
        results = []
        log_dir = settings.log_dir

        if not log_dir.exists():
            return {"query": query, "results": [], "total_files": 0}

        # 确定要搜索的文件
        if filename:
            search_files = [log_dir / filename]
            if not search_files[0].exists():
                raise HTTPException(status_code=404, detail="指定的日志文件不存在")
        else:
            search_files = list(log_dir.glob("*.log*"))

        total_files = len(search_files)
        query_lower = query.lower()

        for file_path in search_files:
            if not file_path.is_file():
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                file_results = []
                for line_num, line in enumerate(lines, 1):
                    if query_lower in line.lower():
                        file_results.append(
                            {
                                "line_number": line_num,
                                "content": line.strip(),
                                "filename": file_path.name,
                            }
                        )

                        if len(results) + len(file_results) >= max_results:
                            break

                results.extend(file_results[-(max_results - len(results)) :])

                if len(results) >= max_results:
                    break

            except Exception as e:
                logger.warning(f"搜索文件时出错 {file_path}: {e}")
                continue

        return {
            "query": query,
            "total_files_searched": total_files,
            "total_results": len(results),
            "max_results": max_results,
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索日志失败: {e}")


@router.get("/tail/{filename}", summary="获取日志文件尾部内容")
async def tail_log_file(
    filename: str,
    lines: int = Query(default=50, ge=1, le=1000, description="显示的行数"),
):
    """获取日志文件的最后N行内容"""
    try:
        # 安全检查
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="无效的文件名")

        log_dir = settings.log_dir
        file_path = log_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="日志文件不存在")

        # 读取文件最后几行
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取日志文件失败: {e}")

        return {
            "filename": filename,
            "total_lines": len(all_lines),
            "tail_lines": len(tail_lines),
            "content": "".join(tail_lines),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志尾部内容失败 {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志尾部内容失败: {e}")
