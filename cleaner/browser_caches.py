"""额外浏览器缓存清理模块

清理 Firefox、Brave、Opera、搜狗、360 等浏览器的缓存。"""
import os
from .utils import logger, clean_module, get_size, format_size


def _get_localappdata():
    return os.environ.get("LOCALAPPDATA", os.path.expandvars(r"%LOCALAPPDATA%"))


def _get_appdata():
    return os.environ.get("APPDATA", os.path.expandvars(r"%APPDATA%"))


# 标准的 Chromium Cache 子目录列表
_CHROMIUM_CACHE_DIRS = [
    "Cache", "Code Cache", "GPUCache", "DawnCache",
    "Service Worker", "IndexedDB",
]


def _clean_chromium_profile(base_path, dry_run, label):
    """通用 Chromium 系浏览器清理

    Args:
        base_path: User Data 根路径
        dry_run: 预览模式
        label: 日志标签

    Returns:
        list: 找到的缓存路径
    """
    paths = []
    if not os.path.exists(base_path):
        return paths

    try:
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if not os.path.isdir(item_path):
                continue
            for cache_dir in _CHROMIUM_CACHE_DIRS:
                cache_path = os.path.join(item_path, cache_dir)
                if os.path.exists(cache_path):
                    paths.append(cache_path)
    except OSError as e:
        logger.debug(f"[{label}] 遍历失败: {e}")

    return paths


def _find_all_profiles(base_path):
    """在 Chromium User Data 中查找所有 Profile 和 Default 目录"""
    profiles = []
    if not os.path.exists(base_path):
        return profiles
    try:
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                profiles.append(item_path)
    except OSError:
        pass
    return profiles


@clean_module("Firefox 缓存", days_old=1)
def clean_firefox_cache(dry_run=False):
    """清理 Firefox 浏览器缓存

    Returns:
        list: 要清理的路径列表
    """
    appdata = _get_appdata()
    localappdata = _get_localappdata()
    paths = []

    # Firefox Profile 目录
    firefox_profiles = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if not os.path.exists(firefox_profiles):
        # 也检查 LocalAppData 路径
        firefox_profiles = os.path.join(localappdata, "Mozilla", "Firefox", "Profiles")

    if os.path.exists(firefox_profiles):
        try:
            for profile in os.listdir(firefox_profiles):
                profile_path = os.path.join(firefox_profiles, profile)
                if not os.path.isdir(profile_path):
                    continue

                # Firefox 缓存子目录
                cache_dirs = ["cache2", "thumbnails", "offlinecache"]
                for cd in cache_dirs:
                    cd_path = os.path.join(profile_path, cd)
                    if os.path.exists(cd_path):
                        paths.append(cd_path)
        except OSError as e:
            logger.debug(f"[Firefox 缓存] 遍历失败: {e}")

    return paths if paths else None


def clean_brave_cache(days_old=1, dry_run=False):
    """清理 Brave 浏览器缓存

    Returns:
        dict: 清理结果
    """
    localappdata = _get_localappdata()
    brave_base = os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data")

    if not os.path.exists(brave_base):
        logger.info("[Brave 缓存] Brave 未安装或路径不存在，跳过")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    logger.info(f"[Brave 缓存] 开始清理: {brave_base}")

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
    brave_size_before = get_size(brave_base)

    cache_paths = _clean_chromium_profile(brave_base, dry_run, "Brave 缓存")
    from .utils import safe_rmtree
    for cp in cache_paths:
        result = safe_rmtree(cp, days_old=days_old, dry_run=dry_run)
        for key in total_result:
            total_result[key] += result[key]

    if not dry_run:
        brave_size_after = get_size(brave_base)
        logger.info(f"  清理前: {format_size(brave_size_before)}, 清理后: {format_size(brave_size_after)}")
    else:
        logger.info(f"  [预览] 将删除: {total_result['deleted_count']} 个文件, "
                    f"释放: {format_size(total_result['deleted_size'])}")

    return total_result


def clean_opera_cache(days_old=1, dry_run=False):
    """清理 Opera 浏览器缓存

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    paths_to_check = []

    # Opera 稳定版
    opera_base = os.path.join(appdata, "Opera Software", "Opera Stable")
    paths_to_check.append(opera_base)

    # Opera GX
    opera_gx = os.path.join(appdata, "Opera Software", "Opera GX Stable")
    paths_to_check.append(opera_gx)

    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}
    found = False

    from .utils import safe_rmtree
    for op_base in paths_to_check:
        if not os.path.exists(op_base):
            continue
        found = True
        logger.info(f"[Opera 缓存] 清理: {op_base}")

        cache_paths = _clean_chromium_profile(op_base, dry_run, "Opera 缓存")
        for cp in cache_paths:
            result = safe_rmtree(cp, days_old=days_old, dry_run=dry_run)
            for key in total_result:
                total_result[key] += result[key]

    if not found:
        logger.info("[Opera 缓存] Opera 未安装或路径不存在，跳过")
    elif total_result["deleted_size"] > 0:
        logger.info(f"[Opera 缓存] 删除: {total_result['deleted_count']} 个文件, "
                    f"释放: {format_size(total_result['deleted_size'])}")

    return total_result


def clean_sogou_cache(days_old=1, dry_run=False):
    """清理搜狗浏览器缓存

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    localappdata = _get_localappdata()
    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 搜狗高速浏览器
    sogou_paths = [
        os.path.join(appdata, "Sogou", "SogouExplorer"),
        os.path.join(localappdata, "Sogou", "SogouExplorer"),
    ]

    found = False
    from .utils import safe_rmtree
    for sp in sogou_paths:
        if not os.path.exists(sp):
            continue
        found = True
        logger.info(f"[搜狗浏览器] 清理: {sp}")

        # 搜狗的缓存目录命名
        cache_subdirs = ["Cache", "Cache2", "VideoCache", "WebkitCache"]
        try:
            for item in os.listdir(sp):
                item_path = os.path.join(sp, item)
                if not os.path.isdir(item_path):
                    continue
                for cd in cache_subdirs:
                    cd_path = os.path.join(item_path, cd)
                    if os.path.exists(cd_path):
                        result = safe_rmtree(cd_path, days_old=days_old, dry_run=dry_run)
                        for key in total_result:
                            total_result[key] += result[key]
        except OSError as e:
            logger.debug(f"[搜狗浏览器] 遍历失败: {e}")

    if not found:
        logger.info("[搜狗浏览器] 搜狗浏览器未安装或路径不存在，跳过")

    return total_result


def clean_360_cache(days_old=1, dry_run=False):
    """清理 360 浏览器缓存

    Returns:
        dict: 清理结果
    """
    appdata = _get_appdata()
    localappdata = _get_localappdata()
    total_result = {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    # 360 安全浏览器 / 360 极速浏览器
    browser_paths = [
        os.path.join(appdata, "360se"),         # 360 安全浏览器
        os.path.join(appdata, "360Chrome"),      # 360 极速浏览器
        os.path.join(localappdata, "360se"),
        os.path.join(localappdata, "360Chrome"),
    ]

    found = False
    from .utils import safe_rmtree
    for bp in browser_paths:
        if not os.path.exists(bp):
            continue
        found = True
        logger.info(f"[360 浏览器] 清理: {bp}")

        cache_subdirs = ["Cache", "Media Cache", "GPUCache"]
        try:
            for item in os.listdir(bp):
                item_path = os.path.join(bp, item)
                if not os.path.isdir(item_path):
                    continue
                for cd in cache_subdirs:
                    cd_path = os.path.join(item_path, cd)
                    if os.path.exists(cd_path):
                        result = safe_rmtree(cd_path, days_old=days_old, dry_run=dry_run)
                        for key in total_result:
                            total_result[key] += result[key]
        except OSError as e:
            logger.debug(f"[360 浏览器] 遍历失败: {e}")

    if not found:
        logger.info("[360 浏览器] 360 浏览器未安装或路径不存在，跳过")

    return total_result
