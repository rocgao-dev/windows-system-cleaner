#!/usr/bin/env python3
"""Windows 系统垃圾清理工具

安全、高效地清理 Windows 系统中的垃圾文件和缓存。

用法:
    python cleaner.py                    # 交互式运行所有清理模块
    python cleaner.py --dry-run          # 预览模式，只统计不删除
    python cleaner.py --quiet            # 静默模式，只输出汇总
    python cleaner.py --skip recycle     # 跳过回收站清空
    python cleaner.py --only temp        # 只清理临时文件
    python cleaner.py --days 7           # 只删除 7 天前的文件
    python cleaner.py --no-confirm       # 跳过确认提示（适合定时任务）
    python cleaner.py --report report.txt # 保存报告到文件

注意：
    - 需要以管理员身份运行
    - 默认只删除超过 1 天未修改的文件
    - 不会删除正在使用的文件
    - 操作日志记录在 cleaner.log 中
"""

import sys
import os
import argparse
import time
import inspect

# 让 Python 自动适配控制台编码（Win 中文系统默认 GBK）
# 如果输出被重定向，由 PYTHONIOENCODING 环境变量控制

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cleaner.utils import (
    logger, is_admin, get_disk_free, format_size,
    set_console_quiet, set_console_verbose,
)
from cleaner.report import CleanupReport
from cleaner.temp_files import clean_windows_temp, clean_user_temp, clean_prefetch
from cleaner.windows_update import (
    clean_dism_component_store, clean_software_distribution,
    clean_delivery_optimization_files, clean_windows_old,
)
from cleaner.internet_cache import (
    clean_ie_cache, clean_edge_cache, clean_chrome_cache,
    clean_qq_browser_cache, flush_dns_cache,
)
from cleaner.delivery_opt import clean_delivery_optimization
from cleaner.recycle_bin import empty_recycle_bin, get_recycle_bin_info
from cleaner.system_temp import (
    clean_cbs_logs, clean_crash_dumps, clean_thumbnail_cache,
    clean_font_cache,
)
from cleaner.wps_cleaner import (
    clean_wps_backup, clean_wps_logs, clean_wps_cache,
    clean_wps_recent, clean_wps_temp, clean_wps_recovery,
    clean_wps_cloud_cache,
)
from cleaner.dev_caches import (
    clean_pip_cache, clean_npm_cache, clean_yarn_cache,
    clean_huggingface_cache, clean_ollama_models,
    clean_nuget_cache,
)
from cleaner.browser_caches import (
    clean_firefox_cache, clean_brave_cache, clean_opera_cache,
    clean_sogou_cache, clean_360_cache,
)
from cleaner.app_caches import (
    clean_bilibili_cache, clean_baidunetdisk_cache,
)


# 定义所有清理模块
MODULES = [
    # (name, label, function, kwargs)
    ("temp_win", "Windows\\Temp", clean_windows_temp, {}),
    ("temp_user", "用户 Temp", clean_user_temp, {}),
    ("prefetch", "Prefetch 预读取", clean_prefetch, {"days_old": 7}),
    ("dism", "DISM 组件存储", clean_dism_component_store, {}),
    ("sw_dist", "SoftwareDistribution", clean_software_distribution, {}),
    ("win_old", "Windows.old", clean_windows_old, {}),
    ("ie_cache", "IE 浏览器缓存", clean_ie_cache, {}),
    ("edge_cache", "Edge 浏览器缓存", clean_edge_cache, {}),
    ("chrome_cache", "Chrome 浏览器缓存", clean_chrome_cache, {}),
    ("qq_browser", "QQ 浏览器缓存", clean_qq_browser_cache, {}),
    ("dns", "DNS 缓存刷新", flush_dns_cache, {}),
    ("delivery_opt", "传递优化文件", clean_delivery_optimization, {}),
    ("recycle", "回收站", empty_recycle_bin, {}),
    ("cbs_logs", "CBS 日志", clean_cbs_logs, {"days_old": 7}),
    ("crash_dump", "崩溃转储/WER", clean_crash_dumps, {"days_old": 7}),
    ("thumbnail", "缩略图缓存", clean_thumbnail_cache, {}),
    ("font_cache", "字体缓存", clean_font_cache, {}),
    ("wps_backup", "WPS 文档备份", clean_wps_backup, {"days_old": 3}),
    ("wps_logs", "WPS 日志文件", clean_wps_logs, {"days_old": 1}),
    ("wps_cache", "WPS 缓存", clean_wps_cache, {"days_old": 1}),
    ("wps_recent", "WPS 最近文件列表", clean_wps_recent, {}),
    ("wps_temp", "WPS 临时文件", clean_wps_temp, {}),
    ("wps_recovery", "WPS 崩溃恢复", clean_wps_recovery, {"days_old": 3}),
    ("wps_cloud", "WPS 云文档缓存", clean_wps_cloud_cache, {"days_old": 3}),

    # ---- 开发者缓存（v2.0） ----
    ("pip_cache", "pip 下载缓存", clean_pip_cache, {}),
    ("npm_cache", "npm 全局缓存", clean_npm_cache, {}),
    ("yarn_cache", "yarn 包缓存", clean_yarn_cache, {}),
    ("huggingface", "HuggingFace 模型缓存", clean_huggingface_cache, {}),
    ("ollama", "Ollama 本地模型", clean_ollama_models, {}),
    ("nuget", "NuGet 缓存", clean_nuget_cache, {}),

    # ---- 额外浏览器缓存（v2.0） ----
    ("firefox", "Firefox 缓存", clean_firefox_cache, {}),
    ("brave", "Brave 缓存", clean_brave_cache, {}),
    ("opera", "Opera 缓存", clean_opera_cache, {}),
    ("sogou", "搜狗浏览器缓存", clean_sogou_cache, {}),
    ("browser_360", "360 浏览器缓存", clean_360_cache, {}),

    # ---- 应用缓存（v2.0） ----
    ("bilibili", "Bilibili 缓存", clean_bilibili_cache, {}),
    ("baidunetdisk", "百度网盘缓存", clean_baidunetdisk_cache, {}),
]


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Windows 系统垃圾清理工具 - 安全清理系统缓存和垃圾文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cleaner.py                       交互式运行
  python cleaner.py --dry-run             预览不删除
  python cleaner.py --quiet --no-confirm  静默自动运行
  python cleaner.py --only temp_win --days 3   只清理 Windows\\Temp, 3天前的文件
  python cleaner.py --skip recycle,dism   跳过回收站和 DISM
  python cleaner.py --report report.txt   保存报告
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true",
        help="预览模式，只统计不删除任何文件",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="静默模式，只输出最终汇总",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="详细模式，输出每个文件的处理细节",
    )
    parser.add_argument(
        "--skip", type=str, default="",
        help="跳过指定模块，多个用逗号分隔（可用名称见下方模块列表）",
    )
    parser.add_argument(
        "--only", type=str, default="",
        help="只运行指定模块，多个用逗号分隔",
    )
    parser.add_argument(
        "--days", type=int, default=1,
        help="只删除 N 天前的文件（默认 1，对 Prefetch/CBS/崩溃转储默认 7）",
    )
    parser.add_argument(
        "--report", type=str, default="",
        help="将报告保存到指定文件",
    )
    parser.add_argument(
        "--no-confirm", action="store_true",
        help="跳过确认提示（适合定时任务/脚本调用）",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="全自动模式：等价于 --quiet --no-confirm --days 1 的快捷方式",
    )
    parser.add_argument(
        "--list-modules", action="store_true",
        help="列出所有可用的清理模块",
    )

    return parser.parse_args()


def list_modules():
    """列出所有清理模块"""
    from cleaner.utils import Colors

    groups = [
        ("系统临时文件", ["temp_win", "temp_user", "prefetch"]),
        ("Windows 更新", ["dism", "sw_dist", "win_old", "delivery_opt"]),
        ("浏览器缓存", ["ie_cache", "edge_cache", "chrome_cache", "qq_browser", "firefox", "brave", "opera", "sogou", "browser_360"]),
        ("系统组件", ["dns", "recycle", "cbs_logs", "crash_dump", "thumbnail", "font_cache"]),
        ("WPS Office", ["wps_backup", "wps_logs", "wps_cache", "wps_recent", "wps_temp", "wps_recovery", "wps_cloud"]),
        ("开发者缓存", ["pip_cache", "npm_cache", "yarn_cache", "huggingface", "ollama", "nuget"]),
        ("应用缓存", ["bilibili", "baidunetdisk"]),
    ]

    mod_map = {m[0]: m[1] for m in MODULES}

    print(f"\n{Colors.bold('可用的清理模块') if Colors else '可用的清理模块'}")
    print(f"{'名称':<20} {'说明':<30}")
    print("-" * 52)

    for group_name, mods in groups:
        print(f"  {Colors.cyan('[' + group_name + ']') if Colors else '  [' + group_name + ']'}")
        for name in mods:
            label = mod_map.get(name, "")
            if label:
                print(f"    {name:<18} {label}")
    print()


def run_module(module_tuple, days_old, dry_run, quiet):
    """运行单个清理模块

    Args:
        module_tuple: (name, label, func, kwargs)
        days_old: 天数阈值
        dry_run: 预览模式
        quiet: 静默模式

    Returns:
        tuple: (name, label, result, error)
    """
    name, label, func, kwargs = module_tuple

    if not quiet:
        print()
        print(f"{'─' * 50}")
        print(f"  [{label}]")
        print(f"{'─' * 50}")

    try:
        # 合并 kwargs 和默认参数
        merged_kwargs = {"days_old": days_old, "dry_run": dry_run}
        merged_kwargs.update(kwargs)

        # 只传递函数接受的参数
        sig = inspect.signature(func)
        filtered_kwargs = {k: v for k, v in merged_kwargs.items() if k in sig.parameters}

        result = func(**filtered_kwargs)
        return name, label, result, None
    except Exception as e:
        logger.error(f"  [FAIL] [{label}] 清理失败: {e}")
        return name, label, None, str(e)


def main():
    """主函数"""
    args = parse_args()

    # 列出模块
    if args.list_modules:
        list_modules()
        return

    # 配置日志级别
    if args.quiet:
        set_console_quiet(True)
    elif args.verbose:
        set_console_verbose(True)

    # 打印标题
    print("=" * 60)
    print("  Windows 系统垃圾清理工具 v2.0")
    print("=" * 60)

    # 检查管理员权限
    if not is_admin():
        print()
        print("  [WARN] 未以管理员身份运行!")
        print("  许多清理操作需要管理员权限，请以管理员身份重新运行此脚本。")
        print("  右键点击命令提示符/PowerShell → 以管理员身份运行")
        print()
        if not args.dry_run and not args.no_confirm:
            choice = input("  是否继续以普通权限运行？(y/N): ")
            if choice.lower() != "y":
                print("  已取消")
                return
        else:
            print("  将以普通权限继续...")
            print()

    # --yes 模式：全自动，不交互
    if args.yes:
        args.quiet = True
        args.no_confirm = True
        args.days = args.days if args.days != 1 else 1

    # 解析 --skip 和 --only
    skip_list = [s.strip() for s in args.skip.split(",") if s.strip()]
    only_list = [s.strip() for s in args.only.split(",") if s.strip()]

    # 过滤模块
    modules_to_run = []
    for mod in MODULES:
        name = mod[0]
        if only_list:
            if name in only_list:
                modules_to_run.append(mod)
        elif name in skip_list:
            continue
        else:
            modules_to_run.append(mod)

    if not modules_to_run:
        print("  没有需要运行的模块。")
        return

    # 打印运行信息
    print(f"\n  运行模式: {'预览 (dry-run)' if args.dry_run else '实际清理'}")
    print(f"  文件天数阈值: {args.days} 天")
    print(f"  将要运行 {len(modules_to_run)} 个模块:")
    for name, label, _, _ in modules_to_run:
        print(f"    - {label}")
    print()

    # 显示清理前磁盘空间
    disk_free = get_disk_free()
    print(f"  C 盘当前剩余空间: {format_size(disk_free)}")
    print()

    # 确认
    if not args.dry_run and not args.no_confirm:
        choice = input("  是否开始清理？(Y/n): ")
        if choice.lower() not in ("", "y", "yes"):
            print("  已取消")
            return

    # 显示回收站信息（预览模式下）
    if args.dry_run and "recycle" not in skip_list:
        recycle_size = get_recycle_bin_info()
        if recycle_size > 0:
            print(f"  [回收站] 估算大小: {format_size(recycle_size)}")
            print()

    # 初始化报告
    report = CleanupReport()

    # 记录清理前空间
    disk_before = get_disk_free()

    # 逐个运行模块
    for i, mod in enumerate(modules_to_run):
        name, label, result, error = run_module(
            mod, args.days, args.dry_run, args.quiet
        )
        report.add_module_result(name, label, result, error)

    # 打印报告
    report.print_summary(quiet=args.quiet)

    # 对比清理前后
    disk_after = get_disk_free()
    freed = disk_after - disk_before
    if freed > 0 and not args.dry_run:
        print(f"  磁盘空间变化: +{format_size(freed)}")
    elif freed < 0 and not args.dry_run:
        # 某些操作（如缩略图缓存重建）可能暂时占用更多空间
        print(f"  磁盘空间变化: {format_size(freed)}")

    # 保存报告到文件
    if args.report:
        report.save_to_file(args.report)
        print(f"\n  报告已保存到: {args.report}")

    # 静默模式下的简洁输出
    if args.quiet:
        freed_str = format_size(report.total_deleted_size)
        print(f"清理完成: 释放 {freed_str}, 耗时 {report.elapsed:.1f}s")

    print()


if __name__ == "__main__":
    main()
