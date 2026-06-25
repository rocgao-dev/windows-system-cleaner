"""Internet 临时文件清理模块

清理 Internet Explorer、Microsoft Edge、Google Chrome 等浏览器的缓存。
同时还清理 DNS 缓存。
"""

import os
import subprocess
from .utils import logger, safe_rmtree, get_size, format_size


def _get_localappdata():
    """获取 LocalAppData 路径"""
    return os.environ.get("LOCALAPPDATA", os.path.expandvars(r"%LOCALAPPDATA%"))


def clean_ie_cache(days_old=1, dry_run=False):
    """清理 Internet Explorer 缓存

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = _get_localappdata()
    ie_cache = os.path.join(localappdata, "Microsoft", "Windows", "INetCache")

    if not os.path.exists(ie_cache):
        logger.info("[IE 缓存] IE 缓存路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[IE 缓存] 开始清理: {ie_cache}")

    size_before = get_size(ie_cache)
    logger.info(f"  当前大小: {format_size(size_before)}")

    result = safe_rmtree(ie_cache, days_old=days_old, dry_run=dry_run)

    if not dry_run:
        size_after = get_size(ie_cache)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    return result


def clean_edge_cache(days_old=1, dry_run=False):
    """清理 Microsoft Edge 浏览器缓存

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = _get_localappdata()
    edge_base = os.path.join(localappdata, "Microsoft", "Edge", "User Data")

    if not os.path.exists(edge_base):
        logger.info("[Edge 缓存] Edge 未安装或路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[Edge 缓存] 开始清理: {edge_base}")

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 清理所有 Profile 的缓存
    cache_dirs = [
        "Cache", "Code Cache", "GPUCache", "DawnCache",
        "Service Worker", "IndexedDB",
    ]

    edge_size_before = get_size(edge_base)

    try:
        for item in os.listdir(edge_base):
            item_path = os.path.join(edge_base, item)
            if not os.path.isdir(item_path):
                continue

            for cache_dir in cache_dirs:
                cache_path = os.path.join(item_path, cache_dir)
                if os.path.exists(cache_path):
                    result = safe_rmtree(cache_path, days_old=days_old, dry_run=dry_run)
                    for key in total_result:
                        total_result[key] += result[key]
    except OSError as e:
        logger.debug(f"Edge 缓存遍历失败: {e}")

    if not dry_run:
        edge_size_after = get_size(edge_base)
        logger.info(f"  清理前: {format_size(edge_size_before)}, 清理后: {format_size(edge_size_after)}")
        logger.info(f"  删除: {total_result['deleted_count']} 个文件, 释放: {format_size(total_result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {total_result['deleted_count']} 个文件, 释放: {format_size(total_result['deleted_size'])}")

    return total_result


def clean_chrome_cache(days_old=1, dry_run=False):
    """清理 Google Chrome 浏览器缓存

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = _get_localappdata()
    chrome_base = os.path.join(localappdata, "Google", "Chrome", "User Data")

    if not os.path.exists(chrome_base):
        logger.info("[Chrome 缓存] Chrome 未安装或路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[Chrome 缓存] 开始清理: {chrome_base}")

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    cache_dirs = [
        "Cache", "Code Cache", "GPUCache", "DawnCache",
        "Service Worker", "IndexedDB",
    ]

    chrome_size_before = get_size(chrome_base)

    try:
        for item in os.listdir(chrome_base):
            item_path = os.path.join(chrome_base, item)
            if not os.path.isdir(item_path):
                continue

            for cache_dir in cache_dirs:
                cache_path = os.path.join(item_path, cache_dir)
                if os.path.exists(cache_path):
                    result = safe_rmtree(cache_path, days_old=days_old, dry_run=dry_run)
                    for key in total_result:
                        total_result[key] += result[key]
    except OSError as e:
        logger.debug(f"Chrome 缓存遍历失败: {e}")

    if not dry_run:
        chrome_size_after = get_size(chrome_base)
        logger.info(f"  清理前: {format_size(chrome_size_before)}, 清理后: {format_size(chrome_size_after)}")
        logger.info(f"  删除: {total_result['deleted_count']} 个文件, 释放: {format_size(total_result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {total_result['deleted_count']} 个文件, 释放: {format_size(total_result['deleted_size'])}")

    return total_result


def clean_qq_browser_cache(days_old=1, dry_run=False):
    """清理 QQ 浏览器缓存

    QQ 浏览器基于 Chromium 内核，缓存结构与 Chrome/Edge 类似。

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = _get_localappdata()
    qq_base = os.path.join(localappdata, "Tencent", "QQBrowser", "User Data")

    if not os.path.exists(qq_base):
        logger.info("[QQ浏览器] QQ 浏览器未安装或路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[QQ浏览器] 开始清理: {qq_base}")

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    cache_dirs = [
        "Cache", "Code Cache", "GPUCache", "DawnCache",
        "Service Worker", "IndexedDB",
    ]

    qq_size_before = get_size(qq_base)

    try:
        for item in os.listdir(qq_base):
            item_path = os.path.join(qq_base, item)
            if not os.path.isdir(item_path):
                continue

            for cache_dir in cache_dirs:
                cache_path = os.path.join(item_path, cache_dir)
                if os.path.exists(cache_path):
                    result = safe_rmtree(cache_path, days_old=days_old, dry_run=dry_run)
                    for key in total_result:
                        total_result[key] += result[key]
    except OSError as e:
        logger.debug(f"QQ浏览器缓存遍历失败: {e}")

    if not dry_run:
        qq_size_after = get_size(qq_base)
        logger.info(f"  清理前: {format_size(qq_size_before)}, 清理后: {format_size(qq_size_after)}")
        logger.info(f"  删除: {total_result['deleted_count']} 个文件, 释放: {format_size(total_result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {total_result['deleted_count']} 个文件, 释放: {format_size(total_result['deleted_size'])}")

    return total_result


def flush_dns_cache(dry_run=False):
    """刷新 DNS 缓存

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    logger.info("[DNS 缓存] 刷新 DNS 解析缓存...")

    if dry_run:
        logger.info("  [预览] 将运行: ipconfig /flushdns")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("  [OK] DNS 缓存已刷新")
            # 检查输出
            for line in result.stdout.splitlines():
                if "已成功刷新" in line or "Successfully flushed" in line:
                    logger.info(f"  {line.strip()}")
        else:
            logger.warning(f"  [FAIL] DNS 缓存刷新失败: {result.stderr}")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
    except Exception as e:
        logger.warning(f"  [FAIL] DNS 缓存刷新失败: {e}")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
