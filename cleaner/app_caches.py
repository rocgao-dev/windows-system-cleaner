"""应用缓存清理模块

清理 Bilibili、百度网盘（仅缓存）等应用的缓存文件。"""
import os
from .utils import logger, clean_module, get_size, format_size


def _get_localappdata():
    return os.environ.get("LOCALAPPDATA", os.path.expandvars(r"%LOCALAPPDATA%"))


def _get_appdata():
    return os.environ.get("APPDATA", os.path.expandvars(r"%APPDATA%"))


def _get_userprofile():
    return os.environ.get("USERPROFILE", "C:\\Users\\Administrator")


@clean_module("Bilibili 缓存", days_old=7)
def clean_bilibili_cache(dry_run=False):
    """清理 Bilibili 客户端缓存

    Returns:
        list: 要清理的路径列表
    """
    localappdata = _get_localappdata()
    paths = []

    # Bilibili 直播姬/客户端更新器缓存
    bili_updater = os.path.join(localappdata, "bilibili-updater")
    if os.path.exists(bili_updater):
        paths.append(bili_updater)

    # Bilibili 桌面客户端
    bili_app = os.path.join(localappdata, "Bilibili")
    if os.path.exists(bili_app):
        paths.append(bili_app)

    return paths if paths else None


def clean_baidunetdisk_cache(days_old=7, dry_run=False):
    """清理百度网盘缓存（只清理缓存目录，不删程序文件）

    百度网盘安装在 AppData/Roaming 下，包含大量程序模块（BrowserEngine 等）。
    此函数仅清理下载临时目录和缓存目录。

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 百度网盘安装目录
    baidu_base = os.path.join(appdata, "baidu", "BaiduNetdisk")
    if not os.path.exists(baidu_base):
        logger.info("[百度网盘缓存] 未安装或路径不存在，跳过")
        return total_result

    from .utils import safe_rmtree
    logger.info("[百度网盘缓存] 清理下载临时目录和缓存...")

    # 只清理以下安全缓存目录（不碰程序模块）
    cache_paths = [
        os.path.join(baidu_base, "download"),         # 下载临时文件
    ]

    # 清理下载临时文件
    for cp in cache_paths:
        if os.path.exists(cp):
            result = safe_rmtree(cp, days_old=days_old, dry_run=dry_run)
            for key in total_result:
                total_result[key] += result[key]

    # 清理各个 Profile 下的日志缓存
    profiles_path = os.path.join(baidu_base, "users")
    if os.path.exists(profiles_path):
        try:
            for item in os.listdir(profiles_path):
                item_path = os.path.join(profiles_path, item)
                if not os.path.isdir(item_path):
                    continue
                # 缓存/日志子目录
                for sub in ["log_cache", "thumb_cache", "datacache"]:
                    sub_path = os.path.join(item_path, sub)
                    if os.path.exists(sub_path):
                        result = safe_rmtree(sub_path, days_old=days_old, dry_run=dry_run)
                        for key in total_result:
                            total_result[key] += result[key]
        except OSError:
            pass

    if total_result["deleted_size"] > 0 or total_result["deleted_count"] > 0:
        logger.info(f"[百度网盘缓存] 删除: {total_result['deleted_count']} 个文件, "
                    f"释放: {format_size(total_result['deleted_size'])}")
    else:
        logger.info("[百度网盘缓存] 无需清理")

    return total_result
