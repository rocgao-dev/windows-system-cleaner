"""WPS Office 垃圾清理模块

清理 WPS Office 办公软件产生的备份文件、日志、缓存、临时文件、
崩溃恢复文件、最近文件历史记录和云文档同步缓存。

WPS Office 数据路径（基于环境变量动态解析）：
    APPDATA/Kingsoft/office6/      — 主数据目录（备份、日志、缓存、恢复等）
    LOCALAPPDATA/Kingsoft/          — 本地缓存（云文档缓存等）
"""

import os
from .utils import logger, safe_rmtree, get_size, format_size


def _get_appdata():
    """获取 Roaming AppData 路径"""
    return os.environ.get("APPDATA", os.path.expandvars(r"%APPDATA%"))


def _get_localappdata():
    """获取 Local AppData 路径"""
    return os.environ.get("LOCALAPPDATA", os.path.expandvars(r"%LOCALAPPDATA%"))


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _clean_wps_paths(paths, label, days_old, dry_run):
    """通用 WPS 路径清理

    遍历多个候选路径，逐个调用 safe_rmtree 清理。

    Args:
        paths: 候选路径列表（可能包含不存在的路径）
        label: 模块标签，用于日志输出（如 "WPS 备份"）
        days_old: 只删除超过指定天数的文件
        dry_run: 是否为预览模式

    Returns:
        dict: 聚合后的清理结果
    """
    total = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
    found_any = False

    for path in paths:
        if not os.path.exists(path):
            continue
        found_any = True

        logger.info(f"[{label}] 清理: {path}")
        size_before = get_size(path)
        result = safe_rmtree(path, days_old=days_old, dry_run=dry_run)
        for key in total:
            total[key] += result[key]

        if not dry_run:
            logger.info(f"  清理前: {format_size(size_before)}, "
                        f"释放: {format_size(result['deleted_size'])}")
        else:
            logger.info(f"  [预览] 将释放: {format_size(result['deleted_size'])}")

    if not found_any:
        logger.info(f"[{label}] 目录不存在，跳过")

    return total


# ---------------------------------------------------------------------------
# 公开清理函数
# ---------------------------------------------------------------------------

def clean_wps_backup(days_old=7, dry_run=False):
    """清理 WPS 文档备份文件

    WPS 在编辑文档时会自动创建备份文件（.bak 等），存放在
    %APPDATA%\\Kingsoft\\office6\\backup 目录下。
    正常保存文档后这些备份通常不再需要。

    Args:
        days_old: 只删除超过指定天数的备份文件（默认 7 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    paths = [os.path.join(appdata, "Kingsoft", "office6", "backup")]
    return _clean_wps_paths(paths, "WPS 备份", days_old, dry_run)


def clean_wps_logs(days_old=7, dry_run=False):
    """清理 WPS Office 日志文件

    清理 WPS 运行过程中产生的日志（.log），存放在
    %APPDATA%\\Kingsoft\\office6\\log 目录下。

    Args:
        days_old: 只删除超过指定天数的日志（默认 7 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    paths = [
        os.path.join(appdata, "Kingsoft", "office6", "log"),
        os.path.join(appdata, "Kingsoft", "office6", "logs"),
    ]
    return _clean_wps_paths(paths, "WPS 日志", days_old, dry_run)


def clean_wps_cache(days_old=7, dry_run=False):
    """清理 WPS Office 缓存文件

    包括字体缓存、加载项缓存、模板缓存等，存放在
    %APPDATA%\\Kingsoft\\office6\\ 和 %LOCALAPPDATA%\\Kingsoft\\ 下。

    Args:
        days_old: 只删除超过指定天数的缓存（默认 7 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    localappdata = _get_localappdata()
    paths = [
        os.path.join(appdata, "Kingsoft", "office6", "cache"),
        os.path.join(appdata, "Kingsoft", "office6", "fontcache"),
        os.path.join(localappdata, "Kingsoft", "office6", "cache"),
    ]
    return _clean_wps_paths(paths, "WPS 缓存", days_old, dry_run)


def clean_wps_recent(dry_run=False):
    """清理 WPS 最近文件列表

    清除 WPS Office 记录的最近打开文件历史。
    仅清除历史记录条目，不会删除原始文档。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    paths = [os.path.join(appdata, "Kingsoft", "office6", "recent")]
    return _clean_wps_paths(paths, "WPS 最近文件", 0, dry_run)


def clean_wps_temp(days_old=1, dry_run=False):
    """清理 WPS 编辑临时文件

    清理 WPS 在编辑文档过程中产生的临时文件。
    WPS 正常关闭后这些文件可以安全删除。

    Args:
        days_old: 只删除超过指定天数的临时文件（默认 1 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    paths = [os.path.join(appdata, "Kingsoft", "office6", "temp")]
    return _clean_wps_paths(paths, "WPS 临时文件", days_old, dry_run)


def clean_wps_recovery(days_old=7, dry_run=False):
    """清理 WPS 崩溃恢复文件

    WPS 异常退出时生成的自动恢复文件，通常存放在
    %APPDATA%\\Kingsoft\\office6\\autosave 或 recovery 目录下。
    若 WPS 已正常运行且文档已手动保存，这些恢复文件可以安全删除。

    Args:
        days_old: 只删除超过指定天数的恢复文件（默认 7 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    paths = [
        os.path.join(appdata, "Kingsoft", "office6", "autosave"),
        os.path.join(appdata, "Kingsoft", "office6", "recovery"),
    ]
    return _clean_wps_paths(paths, "WPS 恢复文件", days_old, dry_run)


def clean_wps_cloud_cache(days_old=7, dry_run=False):
    """清理 WPS 云文档本地缓存

    清理 WPS 云文档同步时产生的本地缓存文件。
    云文档原件保留在云端，清理本地缓存不会影响文档安全。

    Args:
        days_old: 只删除超过指定天数的缓存（默认 7 天）
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    localappdata = _get_localappdata()
    paths = [
        os.path.join(localappdata, "Kingsoft", "WPS Cloud", "cache"),
        os.path.join(localappdata, "kingsoft", "wpsoffice", "cloud"),
    ]
    return _clean_wps_paths(paths, "WPS 云缓存", days_old, dry_run)
