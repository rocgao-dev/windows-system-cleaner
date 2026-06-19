"""回收站清空模块

通过 Windows Shell API 清空所有驱动器的回收站。
"""

import ctypes
from .utils import logger, format_size


# Win32 API 常量
SHERB_NOCONFIRMATION = 0x00000001  # 不显示确认对话框
SHERB_NOPROGRESSUI = 0x00000002   # 不显示进度 UI
SHERB_NOSOUND = 0x00000004         # 不播放声音


def empty_recycle_bin(dry_run=False):
    """清空所有驱动器的回收站

    使用 SHEmptyRecycleBinW API，静默清空（无确认、无进度、无声音）。

    Args:
        dry_run: 是否为预览模式

    Returns:
        dict: 清理结果
    """
    logger.info("[回收站] 清空回收站...")

    if dry_run:
        logger.info("  [预览] 将清空所有驱动器回收站")
        # 无法精确预览回收站内容
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    try:
        # SHEmptyRecycleBinW(HWND, pszRootPath, dwFlags)
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(
            None,  # 当前窗口句柄
            None,  # 所有驱动器
            SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND,
        )

        if result == 0:  # S_OK
            logger.info("  [OK] 回收站已清空")
        else:
            logger.warning(f"  [FAIL] 回收站清空返回代码: {result}")

        # API 不返回释放的空间，设为 0
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}

    except Exception as e:
        logger.warning(f"  [FAIL] 回收站清空失败: {e}")
        return {"deleted_count": 0, "deleted_size": 0, "skipped_count": 0, "dirs_removed": 0}


def get_recycle_bin_info():
    """获取回收站信息（大小等）

    通过查询回收站文件夹来估算大小。

    Returns:
        int: 回收站字节大小（估算）
    """
    import os

    total_size = 0
    try:
        # 回收站位于每个驱动器的 $Recycle.Bin 目录
        for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_root = f"{drive_letter}:\\"
            if not os.path.exists(drive_root):
                continue

            recycle_path = os.path.join(drive_root, "$Recycle.Bin")
            if not os.path.exists(recycle_path):
                continue

            try:
                for root, dirs, files in os.walk(recycle_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            total_size += os.path.getsize(fp)
                        except OSError:
                            pass
            except OSError:
                pass

    except Exception:
        pass

    return total_size
