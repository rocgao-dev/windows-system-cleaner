"""公共工具函数"""

import os
import sys
import stat
import shutil
import ctypes
import logging
from datetime import datetime, timedelta

# 设置日志
logger = logging.getLogger("cleaner")
logger.setLevel(logging.DEBUG)

# 控制台输出
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 文件日志
file_handler = logging.FileHandler("cleaner.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_size(path):
    """计算文件或目录的大小（字节）

    Args:
        path: 文件或目录路径

    Returns:
        int: 大小（字节），路径不存在返回 0
    """
    if not os.path.exists(path):
        return 0

    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
                except OSError:
                    pass
    except OSError:
        pass
    return total


def format_size(size_bytes):
    """将字节数转换为可读的格式

    Args:
        size_bytes: 字节数

    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


def get_disk_free(path="C:\\"):
    """获取磁盘剩余空间

    Args:
        path: 磁盘路径，默认 C 盘

    Returns:
        int: 剩余空间（字节）
    """
    try:
        usage = shutil.disk_usage(path)
        return usage.free
    except OSError:
        return 0


def get_disk_total(path="C:\\"):
    """获取磁盘总空间"""
    try:
        usage = shutil.disk_usage(path)
        return usage.total
    except OSError:
        return 0


def is_file_locked(filepath):
    """检测文件是否被锁定（正在使用）

    Args:
        filepath: 文件路径

    Returns:
        bool: 被锁定返回 True
    """
    try:
        if not os.path.exists(filepath):
            return False
        # 尝试以独占模式打开文件
        fd = os.open(filepath, os.O_RDONLY | os.O_EXCL)
        os.close(fd)
        return False
    except OSError:
        return True


def safe_delete(filepath, dry_run=False):
    """安全删除单个文件

    Args:
        filepath: 文件路径
        dry_run: 是否为预览模式

    Returns:
        tuple: (是否成功, 文件大小(字节))
    """
    try:
        if not os.path.exists(filepath):
            return False, 0

        size = os.path.getsize(filepath)

        if dry_run:
            logger.debug(f"[DRY-RUN] 将删除文件: {filepath} ({format_size(size)})")
            return True, size

        # 先尝试移除只读属性
        try:
            os.chmod(filepath, stat.S_IWRITE)
        except OSError:
            pass

        os.remove(filepath)
        logger.debug(f"已删除文件: {filepath} ({format_size(size)})")
        return True, size

    except PermissionError:
        logger.debug(f"跳过（权限不足/文件占用）: {filepath}")
        return False, 0
    except OSError as e:
        logger.debug(f"跳过（{e}）: {filepath}")
        return False, 0


def safe_rmtree(dirpath, days_old=1, dry_run=False, skip_extensions=None):
    """安全删除目录中的所有文件和子目录

    Args:
        dirpath: 目录路径
        days_old: 只删除超过多少天未修改的文件（默认 1 天）
        dry_run: 是否为预览模式
        skip_extensions: 跳过的文件扩展名集合（如 {'.lock'}）

    Returns:
        dict: {'deleted_count': int, 'deleted_size': int, 'skipped_count': int,
               'dirs_removed': int}
    """
    if skip_extensions is None:
        skip_extensions = set()

    result = {
        "deleted_count": 0,
        "deleted_size": 0,
        "skipped_count": 0,
        "dirs_removed": 0,
    }

    if not os.path.exists(dirpath):
        return result

    cutoff_time = datetime.now() - timedelta(days=days_old)
    cutoff_timestamp = cutoff_time.timestamp()

    # 收集要删除的文件和目录
    files_to_delete = []
    dirs_to_delete = []

    try:
        for root, dirs, files in os.walk(dirpath, topdown=False):
            for name in files:
                filepath = os.path.join(root, name)

                # 跳过特定扩展名
                ext = os.path.splitext(name)[1].lower()
                if ext in skip_extensions:
                    result["skipped_count"] += 1
                    continue

                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime > cutoff_timestamp:
                        # 文件太新，跳过
                        result["skipped_count"] += 1
                        continue
                except OSError:
                    pass

                files_to_delete.append(filepath)

            for name in dirs:
                dirpath_full = os.path.join(root, name)
                # 检查目录是否为空（或即将为空）
                dirs_to_delete.append(dirpath_full)

    except OSError as e:
        logger.debug(f"遍历目录失败: {dirpath} - {e}")
        return result

    # 删除文件
    for filepath in files_to_delete:
        success, size = safe_delete(filepath, dry_run=dry_run)
        if success:
            result["deleted_count"] += 1
            result["deleted_size"] += size
        else:
            result["skipped_count"] += 1

    # 尝试删除空目录
    if not dry_run:
        for dirpath_full in dirs_to_delete:
            try:
                if os.path.exists(dirpath_full):
                    os.rmdir(dirpath_full)
                    result["dirs_removed"] += 1
                    logger.debug(f"已删除空目录: {dirpath_full}")
            except OSError:
                pass  # 目录非空，跳过
    else:
        # dry-run 模式下统计可能可以删除的空目录
        for dirpath_full in dirs_to_delete:
            if os.path.exists(dirpath_full):
                try:
                    if len(os.listdir(dirpath_full)) == 0:
                        result["dirs_removed"] += 1
                except OSError:
                    pass

    return result


def safe_remove_file_or_dir(path, days_old=1, dry_run=False):
    """安全删除文件或目录（自动判断类型）

    Args:
        path: 文件或目录路径
        days_old: 针对目录内的文件，只删除超过多少天未修改的
        dry_run: 是否为预览模式

    Returns:
        dict: 与 safe_rmtree 相同格式
    """
    if not os.path.exists(path):
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    if os.path.isfile(path):
        success, size = safe_delete(path, dry_run=dry_run)
        return {
            "deleted_count": 1 if success else 0,
            "deleted_size": size if success else 0,
            "skipped_count": 0 if success else 1,
            "dirs_removed": 0,
        }

    return safe_rmtree(path, days_old=days_old, dry_run=dry_run)


def set_console_quiet(quiet=True):
    """设置控制台日志级别

    Args:
        quiet: True 时只输出 WARNING 及以上
    """
    if quiet:
        console_handler.setLevel(logging.WARNING)
    else:
        console_handler.setLevel(logging.INFO)


def set_console_verbose(verbose=True):
    """设置控制台日志为详细模式

    Args:
        verbose: True 时输出 DEBUG 及以上
    """
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
