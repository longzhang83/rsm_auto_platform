"""
系统设置API端点
"""

from fastapi import APIRouter, Depends, HTTPException
from app.db.models import User
from app.api.dependencies import get_current_user, get_current_admin
from app.schemas.settings import (
    SystemSettings,
    SystemSettingsUpdate,
    SystemInfo,
    ApiTestRequest,
    ApiTestResponse,
    ClearCacheResponse,
)
from app.services.settings_service import SettingsService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=SystemSettings, summary="获取系统设置")
async def get_settings(current_user: User = Depends(get_current_user)):
    """
    获取当前系统设置

    - 所有已登录用户都可以查看设置
    - 返回系统的所有配置信息
    """
    try:
        return SettingsService.get_settings()
    except Exception as e:
        logger.error(f"获取系统设置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取系统设置失败: {str(e)}")


@router.put("", response_model=SystemSettings, summary="更新系统设置")
async def update_settings(
    updates: SystemSettingsUpdate,
    _: User = Depends(get_current_admin),
):
    """
    更新系统设置（需要管理员权限）

    - 只有管理员可以更新设置
    - 更新后会写入.env文件
    - 某些设置可能需要重启应用才能生效
    """
    try:
        # 转换为字典
        updates_dict = updates.dict(exclude_unset=True)

        # 更新设置
        updated_settings = await SettingsService.update_settings(updates_dict)

        logger.info("系统设置已更新")
        return updated_settings

    except Exception as e:
        logger.error(f"更新系统设置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新系统设置失败: {str(e)}")


@router.get("/info", response_model=SystemInfo, summary="获取系统信息")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """
    获取系统信息

    - 返回应用版本、运行环境等信息
    - 所有已登录用户都可以查看
    """
    try:
        return SettingsService.get_system_info()
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")


@router.post("/test-api", response_model=ApiTestResponse, summary="测试API连接")
async def test_api_connection(
    request: ApiTestRequest,
    _: User = Depends(get_current_admin),
):
    """
    测试智谱AI API连接（需要管理员权限）

    - 测试指定的API密钥是否有效
    - 返回测试结果和响应延迟
    """
    try:
        result = await SettingsService.test_api_connection(
            api_key=request.api_key,
            model=request.model,
        )
        return result

    except Exception as e:
        logger.error(f"测试API连接失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试API连接失败: {str(e)}")


@router.post("/clear-cache", response_model=ClearCacheResponse, summary="清理缓存")
async def clear_cache(_: User = Depends(get_current_admin)):
    """
    清理翻译缓存（需要管理员权限）

    - 清理翻译缓存文件
    - 返回清理的缓存项数量
    """
    try:
        result = await SettingsService.clear_translation_cache()
        return result

    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.post("/export", summary="导出设置")
async def export_settings(_: User = Depends(get_current_admin)):
    """
    导出系统设置（需要管理员权限）

    - 导出当前系统设置为JSON文件
    - 可用于备份或迁移配置
    """
    try:
        settings_data = SettingsService.get_settings()
        return {
            "success": True,
            "message": "设置导出成功",
            "data": settings_data.dict(),
        }

    except Exception as e:
        logger.error(f"导出设置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出设置失败: {str(e)}")


@router.post("/import", summary="导入设置")
async def import_settings(
    settings_data: SystemSettings,
    _: User = Depends(get_current_admin),
):
    """
    导入系统设置（需要管理员权限）

    - 从JSON数据导入系统设置
    - 会覆盖当前配置
    """
    try:
        # 转换为更新格式
        updates_dict = settings_data.dict()

        # 更新设置
        await SettingsService.update_settings(updates_dict)

        return {
            "success": True,
            "message": "设置导入成功",
        }

    except Exception as e:
        logger.error(f"导入设置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入设置失败: {str(e)}")
