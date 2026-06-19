"""临时文件夹清理模块

清理 Windows 临时文件夹和用户临时文件夹。
"""

import os
from .utils import logger, safe_rmtree, get_size, format_size


def clean_windows_temp(days_old=1, dry_run=False):
    """清理 C:\\Windows\\Temp

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    temp_path = os.path.join(windir, "Temp")

    logger.info(f"[Windows\\Temp] 开始清理: {temp_path}")

    size_before = get_size(temp_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    # Windows\Temp 中的文件通常可以安全删除
    # 但跳过一些可能正在使用的文件扩展名
    skip_ext = {".lock", ".pending"}

    result = safe_rmtree(temp_path, days_old=days_old, dry_run=dry_run, skip_extensions=skip_ext)

    if not dry_run:
        size_after = get_size(temp_path)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    if result["skipped_count"] > 0:
        logger.info(f"  跳过: {result['skipped_count']} 个文件（占用中或较新）")

    return result


def clean_user_temp(days_old=1, dry_run=False):
    """清理用户临时文件夹 (%TEMP%)

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    temp_path = os.environ.get("TEMP", "")
    if not temp_path:
        # 默认路径
        temp_path = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\Administrator"), "AppData", "Local", "Temp")

    logger.info(f"[用户 Temp] 开始清理: {temp_path}")

    size_before = get_size(temp_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    # 用户 Temp 目录同样跳过锁定文件
    skip_ext = {".lock", ".pending"}

    result = safe_rmtree(temp_path, days_old=days_old, dry_run=dry_run, skip_extensions=skip_ext)

    if not dry_run:
        size_after = get_size(temp_path)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    if result["skipped_count"] > 0:
        logger.info(f"  跳过: {result['skipped_count']} 个文件（占用中或较新）")

    return result


def clean_prefetch(days_old=7, dry_run=False):
    """清理 Windows Prefetch 预读取缓存

    注意：Prefetch 是性能优化缓存，清理后首次启动应用会稍慢。
    默认只删除超过 7 天的文件。

    Args:
        days_old: 只删除超过指定天数的文件（默认 7 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    prefetch_path = os.path.join(windir, "Prefetch")

    if not os.path.exists(prefetch_path):
        logger.info(f"[Prefetch] 路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[Prefetch] 开始清理: {prefetch_path}")

    size_before = get_size(prefetch_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    result = safe_rmtree(prefetch_path, days_old=days_old, dry_run=dry_run)

    if not dry_run:
        size_after = get_size(prefetch_path)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    return result
