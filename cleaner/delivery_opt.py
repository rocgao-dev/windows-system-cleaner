"""传递优化文件清理模块

清理 Windows 传递优化 (Delivery Optimization) 的缓存文件。
这些文件是 Windows Update P2P 分发的临时缓存，可以安全删除。
"""

import os
from .utils import logger, safe_rmtree, get_size, format_size


def clean_delivery_optimization(days_old=1, dry_run=False):
    """清理传递优化文件

    清理以下位置：
    1. C:\\Windows\\SoftwareDistribution\\DeliveryOptimization
    2. C:\\Windows\\ServiceState\\ (部分传递优化状态文件)

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 1. DeliveryOptimization 目录
    do_paths = [
        os.path.join(windir, "SoftwareDistribution", "DeliveryOptimization"),
        os.path.join(windir, "ServiceState"),
    ]

    for do_path in do_paths:
        if not os.path.exists(do_path):
            logger.info(f"[传递优化] 路径不存在: {do_path}")
            continue

        logger.info(f"[传递优化] 开始清理: {do_path}")

        size_before = get_size(do_path)
        logger.info(f"  当前大小: {format_size(size_before)}")

        result = safe_rmtree(do_path, days_old=days_old, dry_run=dry_run)

        for key in total_result:
            total_result[key] += result[key]

        if not dry_run:
            size_after = get_size(do_path)
            logger.info(f"  清理后大小: {format_size(size_after)}")
        else:
            logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    logger.info(f"[传递优化] 合计: 删除 {total_result['deleted_count']} 个文件, "
                f"释放 {format_size(total_result['deleted_size'])}")
    return total_result


def clean_windows_temp_delivery_files(days_old=1, dry_run=False):
    """清理 Windows\\Temp 下与传递优化相关的文件

    有时候传递优化文件也会暂存在 Windows\\Temp 中。

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    win_temp = os.path.join(windir, "Temp")

    if not os.path.exists(win_temp):
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 传递优化相关的文件前缀
    do_prefixes = ["DUI", "DeliveryOptimization"]

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    try:
        from .utils import safe_delete
        for item in os.listdir(win_temp):
            item_path = os.path.join(win_temp, item)
            if os.path.isfile(item_path):
                for prefix in do_prefixes:
                    if item.startswith(prefix):
                        import time
                        try:
                            mtime = os.path.getmtime(item_path)
                            cutoff = time.time() - days_old * 86400
                            if mtime > cutoff:
                                continue
                            success, size = safe_delete(item_path, dry_run=dry_run)
                            if success:
                                total_result["deleted_count"] += 1
                                total_result["deleted_size"] += size
                            else:
                                total_result["skipped_count"] += 1
                        except OSError:
                            pass
                        break
    except OSError:
        pass

    return total_result
