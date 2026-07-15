"""开发者缓存清理模块

清理 pip、npm、yarn、HuggingFace、Ollama、NuGet 等开发者工具的本地缓存。"""
import os
from .utils import logger, clean_module, get_size, format_size


def _get_localappdata():
    return os.environ.get("LOCALAPPDATA", os.path.expandvars(r"%LOCALAPPDATA%"))


def _get_userprofile():
    return os.environ.get("USERPROFILE", "C:\\Users\\Administrator")


@clean_module("pip 缓存", days_old=1)
def clean_pip_cache(dry_run=False):
    """清理 pip 下载缓存

    Returns:
        list: 要清理的路径列表
    """
    localappdata = _get_localappdata()
    paths = []

    pip_cache = os.path.join(localappdata, "pip", "cache")
    if os.path.exists(pip_cache):
        paths.append(pip_cache)

    # 也检查用户目录下的 .cache/pip（WSL/Linux 子系统的常见位置）
    user_cache = os.path.join(_get_userprofile(), ".cache", "pip")
    if os.path.exists(user_cache):
        paths.append(user_cache)

    return paths if paths else None


@clean_module("npm 缓存", days_old=1)
def clean_npm_cache(dry_run=False):
    """清理 npm 全局缓存 (_cacache)

    Returns:
        list: 要清理的路径列表
    """
    localappdata = _get_localappdata()
    paths = []

    npm_cache = os.path.join(localappdata, "npm-cache")
    if os.path.exists(npm_cache):
        paths.append(npm_cache)

    return paths if paths else None


@clean_module("yarn 缓存", days_old=1)
def clean_yarn_cache(dry_run=False):
    """清理 yarn 包缓存

    Returns:
        list: 要清理的路径列表
    """
    userprofile = _get_userprofile()
    localappdata = _get_localappdata()
    paths = []

    # Yarn v1 全局缓存
    yarn_cache = os.path.join(localappdata, "Yarn", "Cache")
    if os.path.exists(yarn_cache):
        paths.append(yarn_cache)

    # Yarn v2/v3 berry 缓存
    yarn_berry = os.path.join(userprofile, ".yarn", "berry", "cache")
    if os.path.exists(yarn_berry):
        paths.append(yarn_berry)

    return paths if paths else None


@clean_module("HuggingFace 模型缓存", days_old=7)
def clean_huggingface_cache(dry_run=False):
    """清理 HuggingFace Hub 模型缓存

    注意：清理后需要重新下载模型。

    Returns:
        list: 要清理的路径列表
    """
    userprofile = _get_userprofile()
    paths = []

    hf_cache = os.path.join(userprofile, ".cache", "huggingface", "hub")
    if os.path.exists(hf_cache):
        paths.append(hf_cache)

    # 旧路径兼容
    hf_old = os.path.join(userprofile, ".cache", "huggingface", "transformers")
    if os.path.exists(hf_old):
        paths.append(hf_old)

    return paths if paths else None


@clean_module("Ollama 模型", days_old=30)
def clean_ollama_models(dry_run=False):
    """清理 Ollama 本地模型

    注意：此模块只列出大小，实际删除需要用户运行 ollama rm <模型名>
    因为直接删除模型文件可能不完整，建议通过 ollama 命令管理。

    Returns:
        list: 要清理的路径列表
    """
    userprofile = _get_userprofile()
    paths = []

    ollama_dir = os.path.join(userprofile, ".ollama", "models")
    if os.path.exists(ollama_dir):
        paths.append(ollama_dir)

    ollama_blobs = os.path.join(userprofile, ".ollama", "models", "blobs")
    if os.path.exists(ollama_blobs):
        paths.append(ollama_blobs)

    return paths if paths else None


@clean_module("NuGet 缓存", days_old=7)
def clean_nuget_cache(dry_run=False):
    """清理 NuGet (.NET) 包缓存

    Returns:
        list: 要清理的路径列表
    """
    userprofile = _get_userprofile()
    localappdata = _get_localappdata()
    windir = os.environ.get("WINDIR", "C:\\Windows")
    paths = []

    # NuGet 全局包缓存
    nuget_packages = os.path.join(userprofile, ".nuget", "packages")
    if os.path.exists(nuget_packages):
        # 只清理 packages 下的 temp 和 download 缓存，不碰已安装的包
        nuget_temp = os.path.join(nuget_packages, ".temp")
        if os.path.exists(nuget_temp):
            paths.append(nuget_temp)
        nuget_download = os.path.join(nuget_packages, ".download")
        if os.path.exists(nuget_download):
            paths.append(nuget_download)

    # NuGet 缓存目录 (http-cache)
    nuget_httpcache = os.path.join(localappdata, "NuGet", "v3-cache")
    if os.path.exists(nuget_httpcache):
        paths.append(nuget_httpcache)

    # NuGet temp 目录
    nuget_temp2 = os.path.join(localappdata, "NuGet", "temp")
    if os.path.exists(nuget_temp2):
        paths.append(nuget_temp2)

    return paths if paths else None
