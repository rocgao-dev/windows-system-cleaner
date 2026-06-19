"""清理报告模块

跟踪每个清理模块的执行情况，生成汇总报告。
"""

import time
from datetime import datetime
from .utils import format_size


class CleanupReport:
    """清理报告类"""

    def __init__(self):
        self.start_time = time.time()
        self.modules = []  # 每个模块的清理结果
        self.total_deleted_size = 0
        self.total_deleted_count = 0
        self.total_skipped_count = 0
        self.total_dirs_removed = 0
        self.errors = []

    def add_module_result(self, name, label, result, error=None):
        """添加一个模块的清理结果

        Args:
            name: 模块名称（用于 --skip/--only）
            label: 模块中文描述
            result: safe_rmtree 返回的 dict 或 None
            error: 错误信息（如果有）
        """
        module_info = {
            "name": name,
            "label": label,
            "deleted_count": result.get("deleted_count", 0) if result else 0,
            "deleted_size": result.get("deleted_size", 0) if result else 0,
            "skipped_count": result.get("skipped_count", 0) if result else 0,
            "dirs_removed": result.get("dirs_removed", 0) if result else 0,
            "error": error,
        }
        self.modules.append(module_info)

        if not error:
            self.total_deleted_count += module_info["deleted_count"]
            self.total_deleted_size += module_info["deleted_size"]
            self.total_skipped_count += module_info["skipped_count"]
            self.total_dirs_removed += module_info["dirs_removed"]
        else:
            self.errors.append(f"{label}: {error}")

    def add_custom_result(self, name, label, deleted_size):
        """添加自定义清理结果（不适用于 safe_rmtree 格式的操作）

        Args:
            name: 模块名称
            label: 模块描述
            deleted_size: 释放的空间（字节）
        """
        module_info = {
            "name": name,
            "label": label,
            "deleted_count": 0,
            "deleted_size": deleted_size,
            "skipped_count": 0,
            "dirs_removed": 0,
            "error": None,
        }
        self.modules.append(module_info)
        self.total_deleted_size += deleted_size

    @property
    def elapsed(self):
        """已运行时间（秒）"""
        return time.time() - self.start_time

    def print_summary(self, quiet=False):
        """打印汇总报告

        Args:
            quiet: 安静模式，只打印基本信息
        """
        disk_free = 0
        disk_total = 0
        try:
            from .utils import get_disk_free, get_disk_total
            disk_free = get_disk_free()
            disk_total = get_disk_total()
        except Exception:
            pass

        print()
        print("=" * 60)
        print("  清理报告")
        print("=" * 60)

        if not quiet:
            print(f"{'模块':<25} {'文件数':>8} {'释放空间':>12}")
            print("-" * 60)
            for m in self.modules:
                if m["error"]:
                    status = f"[FAIL] {m['error']}"
                    print(f"{m['label']:<25} {'':>8} {status:>12}")
                else:
                    size_str = format_size(m["deleted_size"]) if m["deleted_size"] > 0 else "-"
                    count_str = str(m["deleted_count"]) if m["deleted_count"] > 0 else "-"
                    if m["deleted_size"] == 0 and m["deleted_count"] == 0:
                        status = "(无需清理)"
                        print(f"{m['label']:<25} {'':>8} {status:>12}")
                    else:
                        print(f"{m['label']:<25} {count_str:>8} {size_str:>12}")

        print("-" * 60)
        print(f"{'总计':<25} {self.total_deleted_count:>8} {format_size(self.total_deleted_size):>12}")

        if self.total_skipped_count > 0:
            print(f"  跳过项目: {self.total_skipped_count} 个（文件占用或权限不足）")
        if self.total_dirs_removed > 0:
            print(f"  清理空目录: {self.total_dirs_removed} 个")
        if self.errors:
            print(f"  错误: {len(self.errors)} 个")
            for e in self.errors:
                print(f"    - {e}")

        print(f"  耗时: {self.elapsed:.1f} 秒")

        if disk_total > 0:
            free_percent = (disk_free / disk_total) * 100
            print(f"  C 盘剩余空间: {format_size(disk_free)} / {format_size(disk_total)} ({free_percent:.1f}%)")

        print("=" * 60)

    def save_to_file(self, filepath):
        """将报告保存到文件

        Args:
            filepath: 保存路径
        """
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Windows 系统垃圾清理报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*60}\n\n")

            for m in self.modules:
                f.write(f"[{m['name']}] {m['label']}\n")
                if m["error"]:
                    f.write(f"  状态: 失败 - {m['error']}\n")
                else:
                    f.write(f"  删除文件: {m['deleted_count']} 个\n")
                    f.write(f"  释放空间: {format_size(m['deleted_size'])}\n")
                    f.write(f"  跳过文件: {m['skipped_count']} 个\n")
                    f.write(f"  清理目录: {m['dirs_removed']} 个\n")
                f.write("\n")

            f.write(f"{'='*60}\n")
            f.write(f"总计删除: {self.total_deleted_count} 个文件\n")
            f.write(f"总计释放: {format_size(self.total_deleted_size)}\n")
            f.write(f"总计跳过: {self.total_skipped_count} 个\n")
            f.write(f"运行耗时: {self.elapsed:.1f} 秒\n")
