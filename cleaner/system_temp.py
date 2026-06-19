"""系统临时文件清理模块

清理各种系统临时文件：
- CBS 日志文件
- 崩溃转储文件
- Windows 错误报告 (WER)
- 缩略图缓存
- 字体缓存
- 其他系统临时文件
"""

import os
from .utils import logger, safe_rmtree, safe_delete, get_size, format_size


def clean_cbs_logs(days_old=7, dry_run=False):
    """清理 Windows CBS (Component Based Servicing) 日志

    CBS 日志记录系统组件的安装和维护信息。
    旧的 .log 文件可以安全删除，.persist 日志保留以查看历史。

    Args:
        days_old: 只删除超过指定天数的日志文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    cbs_path = os.path.join(windir, "Logs", "CBS")

    if not os.path.exists(cbs_path):
        logger.info("[CBS 日志] 路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[CBS 日志] 开始清理: {cbs_path}")

    size_before = get_size(cbs_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    result = safe_rmtree(cbs_path, days_old=days_old, dry_run=dry_run)

    if not dry_run:
        size_after = get_size(cbs_path)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    return result


def _clean_dump_files(dump_paths, days_old, dry_run, label):
    """通用崩溃转储清理

    清理 .dmp 文件和相关的 .hdmp 文件。

    Args:
        dump_paths: 要清理的目录列表
        days_old: 天数阈值
        dry_run: 预览模式
        label: 日志标签

    Returns:
        dict: 清理结果
    """
    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    for dump_path in dump_paths:
        if not os.path.exists(dump_path):
            continue

        logger.info(f"[{label}] 清理: {dump_path}")
        size_before = get_size(dump_path)
        result = safe_rmtree(dump_path, days_old=days_old, dry_run=dry_run)
        for key in total_result:
            total_result[key] += result[key]

        logger.info(f"  清理前: {format_size(size_before)}, 释放: {format_size(result['deleted_size'])}")

    return total_result


def clean_crash_dumps(days_old=7, dry_run=False):
    """清理崩溃转储文件

    包括：
    - User 模式进程的崩溃转储 (CrashDumps)
    - 内核模式/蓝屏转储 (Minidump, Memory.dmp)
    - Windows 错误报告 (WER)

    Args:
        days_old: 只删除超过指定天数的转储文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = os.environ.get("LOCALAPPDATA", "")
    windir = os.environ.get("WINDIR", "C:\\Windows")
    programdata = os.environ.get("PROGRAMDATA", "C:\\ProgramData")

    dump_paths = []

    # 用户崩溃转储
    crash_dumps = os.path.join(localappdata, "CrashDumps")
    if os.path.exists(crash_dumps):
        dump_paths.append(crash_dumps)

    # 系统蓝屏转储 (Minidump)
    minidump = os.path.join(windir, "Minidump")
    if os.path.exists(minidump):
        dump_paths.append(minidump)

    # Windows 错误报告
    wer_path1 = os.path.join(localappdata, "Microsoft", "Windows", "WER")
    if os.path.exists(wer_path1):
        dump_paths.append(wer_path1)

    # ProgramData 中的 WER
    wer_path2 = os.path.join(programdata, "Microsoft", "Windows", "WER")
    if os.path.exists(wer_path2):
        dump_paths.append(wer_path2)

    if not dump_paths:
        logger.info("[崩溃转储] 无需清理")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info("[崩溃转储/WER] 开始清理...")
    return _clean_dump_files(dump_paths, days_old, dry_run, "崩溃转储")


def clean_thumbnail_cache(dry_run=False):
    """清理 Windows 缩略图缓存

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = os.environ.get("LOCALAPPDATA", "")
    thumb_path = os.path.join(localappdata, "Microsoft", "Windows", "Explorer")

    if not os.path.exists(thumb_path):
        logger.info("[缩略图缓存] 路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[缩略图缓存] 开始清理: {thumb_path}")

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 缩略图数据库文件
    thumb_files = [
        "thumbcache_*.db",
        "iconcache_*.db",
        "thumbcache_idx.db",
    ]

    try:
        for item in os.listdir(thumb_path):
            for pattern in thumb_files:
                # 简单匹配：以 pattern 前缀开头
                prefix = pattern.replace("*", "")
                if item.startswith(prefix):
                    filepath = os.path.join(thumb_path, item)
                    success, size = safe_delete(filepath, dry_run=dry_run)
                    if success:
                        total_result["deleted_count"] += 1
                        total_result["deleted_size"] += size
                    else:
                        total_result["skipped_count"] += 1
                    break
    except OSError as e:
        logger.debug(f"缩略图缓存遍历失败: {e}")

    logger.info(f"[缩略图缓存] 删除: {total_result['deleted_count']} 个文件, "
                f"释放: {format_size(total_result['deleted_size'])}")
    return total_result


def clean_font_cache(dry_run=False):
    """清理 Windows 字体缓存

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    service_profile = os.path.join(windir, "ServiceProfiles", "LocalService", "AppData", "Local")

    font_cache_paths = []

    # 字体缓存位置
    fc1 = os.path.join(service_profile, "FontCache")
    if os.path.exists(fc1):
        font_cache_paths.append(fc1)

    # 系统字体缓存（需要特殊权限，可能失败）
    fc2 = os.path.join(windir, "System32", "FNTCACHE.DAT")
    if os.path.exists(fc2):
        font_cache_paths.append(fc2)

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    for fc_path in font_cache_paths:
        logger.info(f"[字体缓存] 清理: {fc_path}")

        if os.path.isfile(fc_path):
            success, size = safe_delete(fc_path, dry_run=dry_run)
            if success:
                total_result["deleted_count"] += 1
                total_result["deleted_size"] += size
            else:
                total_result["skipped_count"] += 1
        elif os.path.isdir(fc_path):
            result = safe_rmtree(fc_path, days_old=0, dry_run=dry_run)
            for key in total_result:
                total_result[key] += result[key]

    if total_result["deleted_count"] > 0 or total_result["deleted_size"] > 0:
        logger.info(f"[字体缓存] 删除: {total_result['deleted_count']} 个文件, "
                    f"释放: {format_size(total_result['deleted_size'])}")
    else:
        logger.info("[字体缓存] 无需清理或清理失败（可能需要 TrustedInstaller 权限）")

    return total_result


def clean_event_logs(dry_run=False):
    """清理 Windows 事件日志的备份文件（不使用此功能清理活跃日志）

    仅清理 .evtx 备份和过期的存档日志文件。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    log_path = os.path.join(windir, "System32", "winevt", "Logs")

    if not os.path.exists(log_path):
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[事件日志] 检查旧日志: {log_path}")

    # 只清理备份日志（文件名包含 _backup 或以 .bak 结尾的），不碰活跃的 .evtx
    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    try:
        for item in os.listdir(log_path):
            if "_backup" in item.lower() or item.lower().endswith(".bak"):
                filepath = os.path.join(log_path, item)
                success, size = safe_delete(filepath, dry_run=dry_run)
                if success:
                    total_result["deleted_count"] += 1
                    total_result["deleted_size"] += size
    except OSError:
        pass

    return total_result
