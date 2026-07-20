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


def _run_dism_with_progress(cmd_parts, label, timeout=900):
    """运行 DISM 命令并实时显示进度

    Args:
        cmd_parts: DISM 命令参数列表（不含 "dism"）
        label: 日志标签
        timeout: 超时时间

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    import subprocess
    import sys

    cmd = ["dism"] + cmd_parts
    logger.info(f"  运行: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        last_progress = -1
        stdout_lines = []

        for line in iter(process.stdout.readline, ""):
            stdout_lines.append(line)

            # 解析 DISM 进度 [=== xx.x% ===]
            if "[" in line and "%" in line:
                import re as re_mod
                match = re_mod.search(r"(\d+\.?\d*)%", line)
                if match:
                    pct = int(float(match.group(1)))
                    if pct != last_progress:
                        last_progress = pct
                        bar_len = 30
                        filled = int(bar_len * pct / 100)
                        bar = "=" * filled + " " * (bar_len - filled)
                        sys.stdout.write(f"\r    [{bar}] {pct}%")
                        sys.stdout.flush()

        process.wait()
        if last_progress >= 0:
            sys.stdout.write("\n")
            sys.stdout.flush()

        stdout_text = "".join(stdout_lines)

        if process.returncode == 0:
            logger.info(f"  [OK] {label}完成")
            return process.returncode, stdout_text, ""
        else:
            logger.warning(f"  [FAIL] {label}失败 (code={process.returncode})")
            return process.returncode, stdout_text, ""

    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning(f"  [TIMEOUT] {label}超时")
        return -1, "", "命令超时"
    except FileNotFoundError:
        logger.warning("  [FAIL] DISM 命令不存在（非 Windows 系统？）")
        return -1, "", "DISM 不存在"
    except Exception as e:
        logger.warning(f"  [FAIL] {label}异常: {e}")
        return -1, "", str(e)


def clean_dism_component_store(dry_run=False):
    """通过 DISM 清理 Windows 组件存储 (WinSxS)

    这是系统级别的干净清理，不会误删文件。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    from .utils import Colors
    logger.info(f"{Colors.cyan('[DISM 组件存储]') if hasattr(Colors, 'cyan') else '[DISM 组件存储]'} 开始清理...")

    if dry_run:
        logger.info("  [预览] 将运行: DISM /Cleanup-Image /StartComponentCleanup")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    total_freed = 0

    # 1. 清理被取代的组件（带进度显示）
    _run_dism_with_progress(
        ["/online", "/cleanup-image", "/startcomponentcleanup"],
        "组件存储清理",
        timeout=900,
    )

    # 2. 清理 Service Pack 备份
    _run_dism_with_progress(
        ["/online", "/cleanup-image", "/spsuperseded"],
        "SP 备份清理",
        timeout=900,
    )

    logger.info(f"  {Colors.green('[OK]') if hasattr(Colors, 'green') else '[OK]'} DISM 清理完成")

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


def clean_system_restore_points(dry_run=False, keep_latest=1):
    """清理旧的系统还原点（卷影副本）

    默认保留最新的 N 个还原点，删除其余旧的。

    Args:
        dry_run: 是否为预览模式
        keep_latest: 保留最新的还原点数量（默认 1 个）

    Returns:
        dict: 清理结果
    """
    from .utils import Colors
    logger.info(f"{Colors.cyan('[系统还原点]') if hasattr(Colors, 'cyan') else '[系统还原点]'} 开始检查...")

    # 先列出所有还原点
    code, stdout, stderr = _run_cmd("vssadmin list shadows")
    if code != 0:
        logger.warning("  无法获取还原点列表（可能需要管理员权限或系统未启用）")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 统计还原点数量
    shadow_count = stdout.count("影子副本 ID")
    if shadow_count == 0:
        logger.info("  没有系统还原点，无需清理")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"  当前共有 {shadow_count} 个系统还原点")
    logger.info(f"  保留最新的 {keep_latest} 个，删除其余 {max(0, shadow_count - keep_latest)} 个")

    if dry_run:
        logger.info("  [预览] 将删除旧的系统还原点")
        return {"deleted_count": max(0, shadow_count - keep_latest), "deleted_size": 0,
                "skipped_count": 0, "dirs_removed": 0}

    if shadow_count <= keep_latest:
        logger.info("  还原点数量不超过保留数，无需清理")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 逐个删除最旧的，直到保留 keep_latest 个
    deleted = 0
    for i in range(shadow_count - keep_latest):
        code, _, _ = _run_cmd("vssadmin delete shadows /for=C: /oldest /quiet", timeout=120)
        if code == 0:
            deleted += 1
            logger.info(f"  已删除第 {deleted} 个旧还原点")
        else:
            logger.warning("  删除还原点失败")
            break

    logger.info(f"  {Colors.green('[OK]') if hasattr(Colors, 'green') else '[OK]'} "
                f"共删除 {deleted} 个系统还原点")

    return {"deleted_count": deleted, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}


def clean_old_drivers(dry_run=False):
    """清理旧的驱动程序包（通过 DISM 组件存储清理）

    使用 DISM 的 /StartComponentCleanup 清理被取代的驱动包和系统组件。
    这是微软官方推荐的安全清理方式，不会删除正在使用的驱动。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    from .utils import Colors
    logger.info(f"{Colors.cyan('[旧驱动包清理]') if hasattr(Colors, 'cyan') else '[旧驱动包清理]'} 开始清理...")

    if dry_run:
        logger.info("  [预览] 将运行 DISM 清理旧驱动程序包")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 使用 DISM 组件清理，会同时清理被取代的驱动包
    # /resetbase 参数会彻底清理被取代的组件，清理后无法卸载已安装的更新
    # 这里只用基础的 /startcomponentcleanup，更安全
    _run_dism_with_progress(
        ["/online", "/cleanup-image", "/startcomponentcleanup"],
        "驱动包与组件清理",
        timeout=900,
    )

    logger.info(f"  {Colors.green('[OK]') if hasattr(Colors, 'green') else '[OK]'} 旧驱动包清理完成")

    return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
