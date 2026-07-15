"""单元测试：工具函数

测试 cleaner/utils.py 中的核心工具函数。
"""
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

# 将被测试的包加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from cleaner.utils import (
        format_size, get_size, safe_delete, safe_rmtree,
        is_file_locked, clean_module, Colors,
    )
except ImportError as e:
    print(f"[SKIP] 导入失败（可能在非 Windows 平台）: {e}")
    sys.exit(0)


def test_format_size():
    """测试 format_size 格式输出"""
    assert format_size(0) == "0 B"
    assert format_size(500) == "500.00 B"
    assert format_size(1024) == "1.00 KB"
    assert format_size(1536) == "1.50 KB"
    assert format_size(1048576) == "1.00 MB"
    assert format_size(1073741824) == "1.00 GB"


def test_get_size_file():
    """测试 get_size 对单个文件的统计"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"x" * 1000)
        fpath = f.name
    try:
        size = get_size(fpath)
        assert size == 1000, f"Expected 1000, got {size}"
    finally:
        os.unlink(fpath)


def test_get_size_dir():
    """测试 get_size 对目录的统计"""
    tmpdir = tempfile.mkdtemp()
    try:
        # 创建两个文件
        with open(os.path.join(tmpdir, "a.txt"), "w") as f:
            f.write("x" * 500)
        with open(os.path.join(tmpdir, "b.txt"), "w") as f:
            f.write("y" * 300)

        size = get_size(tmpdir)
        assert size == 800, f"Expected 800, got {size}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_get_size_not_exist():
    """测试 get_size 对不存在路径的处理"""
    assert get_size("Z:\\this_path_should_not_exist_12345") == 0


def test_safe_delete_dry_run():
    """测试 safe_delete 预览模式"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test")
        fpath = f.name
    try:
        success, size = safe_delete(fpath, dry_run=True)
        assert success is True
        assert size == 4
        # dry_run 模式不应实际删除文件
        assert os.path.exists(fpath)
    finally:
        if os.path.exists(fpath):
            os.unlink(fpath)


def test_safe_delete_actual():
    """测试 safe_delete 实际删除"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"delete me")
        fpath = f.name
    success, size = safe_delete(fpath, dry_run=False)
    assert success is True
    assert size == 9
    assert not os.path.exists(fpath)


def test_safe_rmtree_empty_dir():
    """测试 safe_rmtree 对空目录"""
    tmpdir = tempfile.mkdtemp()
    result = safe_rmtree(tmpdir, days_old=0, dry_run=False)
    assert result["deleted_count"] == 0
    assert result["deleted_size"] == 0
    # 空目录本身不会被删除（safe_rmtree 只删内部文件）
    assert os.path.exists(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_safe_rmtree_with_files():
    """测试 safe_rmtree 删除目录中的文件"""
    tmpdir = tempfile.mkdtemp()
    try:
        # 创建超过 1 天的文件
        old_file = os.path.join(tmpdir, "old.txt")
        with open(old_file, "w") as f:
            f.write("old data")

        # 设置文件时间为 10 天前
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))

        result = safe_rmtree(tmpdir, days_old=1, dry_run=False)
        assert result["deleted_count"] >= 1
        assert result["deleted_size"] > 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_safe_rmtree_recent_files():
    """测试 safe_rmtree 跳过新文件"""
    tmpdir = tempfile.mkdtemp()
    try:
        new_file = os.path.join(tmpdir, "new.txt")
        with open(new_file, "w") as f:
            f.write("new data")

        # 文件的 mtime 是当前时间，应被跳过
        result = safe_rmtree(tmpdir, days_old=7, dry_run=False)
        assert result["deleted_count"] == 0
        assert result["skipped_count"] >= 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_safe_rmtree_dry_run():
    """测试 safe_rmtree 预览模式不实际删除"""
    tmpdir = tempfile.mkdtemp()
    try:
        old_file = os.path.join(tmpdir, "old.txt")
        with open(old_file, "w") as f:
            f.write("x" * 100)
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))

        result = safe_rmtree(tmpdir, days_old=1, dry_run=True)
        assert result["deleted_count"] >= 1  # 预览模式统计
        assert result["deleted_size"] >= 100
        assert os.path.exists(old_file)  # 预览不应删除
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_safe_rmtree_skip_extensions():
    """测试 safe_rmtree 跳过指定扩展名"""
    tmpdir = tempfile.mkdtemp()
    try:
        old_file = os.path.join(tmpdir, "keep.lock")
        with open(old_file, "w") as f:
            f.write("x" * 50)
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))

        result = safe_rmtree(tmpdir, days_old=1, dry_run=False,
                             skip_extensions={".lock"})
        assert result["deleted_count"] == 0, ".lock 文件应被跳过"
        assert result["skipped_count"] >= 1
        assert os.path.exists(old_file), ".lock 文件应保留"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_format_size_edge_cases():
    """测试 format_size 边界情况"""
    assert format_size(1) == "1.00 B"
    assert format_size(1023) == "1023.00 B"
    assert format_size(1025) == "1.00 KB"
    # 大文件
    tb_size = 1099511627776
    result = format_size(tb_size)
    assert "TB" in result, f"Big size should show TB, got {result}"


def test_clean_module_decorator():
    """测试 clean_module 装饰器"""
    @clean_module("测试模块", days_old=0)
    def test_cleaner(dry_run=False):
        return None  # 路径不存在

    # 装饰器应当能正常包装，返回标准格式
    result = test_cleaner(dry_run=True)
    assert isinstance(result, dict)
    assert "deleted_count" in result
    assert "deleted_size" in result
    assert "skipped_count" in result
    assert "dirs_removed" in result


if __name__ == "__main__":
    # 简单测试运行器
    tests = [
        test_format_size,
        test_get_size_file,
        test_get_size_dir,
        test_get_size_not_exist,
        test_safe_delete_dry_run,
        test_safe_delete_actual,
        test_safe_rmtree_empty_dir,
        test_safe_rmtree_with_files,
        test_safe_rmtree_recent_files,
        test_safe_rmtree_dry_run,
        test_safe_rmtree_skip_extensions,
        test_format_size_edge_cases,
        test_clean_module_decorator,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print(f"\n{'='*40}")
    print(f"  总计: {passed + failed}  |  通过: {passed}  |  失败: {failed}")
    print(f"{'='*40}")
