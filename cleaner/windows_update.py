"""Windows 更新清理模块

清理 Windows Update 缓存文件、组件存储、Service Pack 备份等。
"""

import os
import subprocess
import shutil
from .utils import logger, safe_rmtree, get_size, format_size


def _run_cmd(cmd, timeout=600):
    """运行系统命令

    Args:
        cmd: 命令列表或字符串
        timeout: 超时时间（秒）

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "命令超时"
    except Exception as e:
        return -1, "", str(e)


def clean_dism_component_store(dry_run=False):
    """通过 DISM 清理 Windows 组件存储 (WinSxS)

    这是系统级别的干净清理，不会误删文件。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    logger.info("[DISM 组件存储] 开始清理...")

    if dry_run:
        logger.info("  [预览] 将运行: DISM /Cleanup-Image /StartComponentCleanup")
        # 预览模式下无法准确估计，返回估算值
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    total_freed = 0

    # 1. 清理被取代的组件
    logger.info("  运行: DISM /Cleanup-Image /StartComponentCleanup")
    ret, out, err = _run_cmd(
        "dism /online /cleanup-image /startcomponentcleanup",
        timeout=900,
    )
    if ret == 0:
        logger.info("  [OK] 组件存储清理完成")
        logger.debug(f"    DISM 输出: {out}")
    else:
        logger.warning(f"  [FAIL] DISM 组件清理失败: {err}")
        logger.debug(f"    returncode={ret}")

    # 2. 清理 Service Pack 备份
    logger.info("  运行: DISM /Cleanup-Image /SPSuperseded")
    ret, out, err = _run_cmd(
        "dism /online /cleanup-image /spsuperseded",
        timeout=900,
    )
    if ret == 0:
        logger.info("  [OK] SP 备份清理完成")
        logger.debug(f"    DISM 输出: {out}")
    else:
        logger.debug(f"  SP 备份清理: {err}")

    # 由于 DISM 不直接返回释放的空间，无法精确统计
    return {"deleted_count": 0, "deleted_size": total_freed, "skipped_count": 0, "dirs_removed": 0}


def clean_software_distribution(days_old=1, dry_run=False):
    """清理 SoftwareDistribution 下载缓存

    这是 Windows Update 的下载目录，可以安全清理。
    注意：清理后已下载但未安装的更新会丢失。

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    sd_path = os.path.join(windir, "SoftwareDistribution", "Download")

    if not os.path.exists(sd_path):
        logger.info("[SoftwareDistribution] 路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[SoftwareDistribution] 开始清理: {sd_path}")

    size_before = get_size(sd_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    result = safe_rmtree(sd_path, days_old=days_old, dry_run=dry_run)

    if not dry_run:
        size_after = get_size(sd_path)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    return result


def clean_delivery_optimization_files(days_old=1, dry_run=False):
    """清理 Delivery Optimization 文件

    传递优化文件用于 Windows Update 的 P2P 分发。
    这些文件可以安全删除。

    Args:
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    do_path = os.path.join(windir, "SoftwareDistribution", "DeliveryOptimization")

    if not os.path.exists(do_path):
        logger.info("[DeliveryOptimization] 路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[DeliveryOptimization] 开始清理: {do_path}")

    size_before = get_size(do_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    result = safe_rmtree(do_path, days_old=days_old, dry_run=dry_run)

    if not dry_run:
        size_after = get_size(do_path)
        logger.info(f"  清理后大小: {format_size(size_after)}")
        logger.info(f"  删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")
    else:
        logger.info(f"  [预览] 将删除: {result['deleted_count']} 个文件, 释放: {format_size(result['deleted_size'])}")

    return result


def clean_windows_old(dry_run=False):
    """清理 Windows.old 旧系统备份

    注意：清理后无法回滚到旧版 Windows。
    仅在确认不需要回滚时使用。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    system_drive = os.environ.get("SYSTEMDRIVE", "C:")
    old_path = os.path.join(system_drive + os.sep, "Windows.old")

    if not os.path.exists(old_path):
        logger.info("[Windows.old] 不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[Windows.old] 发现旧系统备份: {old_path}")

    size_before = get_size(old_path)
    logger.info(f"  当前大小: {format_size(size_before)}")

    if dry_run:
        logger.info(f"  [预览] 将删除 Windows.old 目录，释放 {format_size(size_before)}")
        return {"deleted_count": 1, "deleted_size": size_before, "skipped_count": 0, "dirs_removed": 1}

    try:
        shutil.rmtree(old_path, ignore_errors=False)
        logger.info(f"  [OK] 已删除 Windows.old, 释放 {format_size(size_before)}")
        return {"deleted_count": 1, "deleted_size": size_before, "skipped_count": 0, "dirs_removed": 1}
    except Exception as e:
        logger.warning(f"  [FAIL] 删除 Windows.old 失败: {e}")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
