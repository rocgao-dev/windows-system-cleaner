# Windows 系统垃圾清理工具

安全、高效地清理 Windows 系统中的垃圾文件和缓存。不影响系统和软件正常运行。

## 功能

| 模块 | 清理内容 | 说明 |
|------|---------|------|
| `temp_win` | `C:\Windows\Temp` | Windows 临时文件 |
| `temp_user` | `%TEMP%` (用户临时文件) | 应用临时文件 |
| `prefetch` | `C:\Windows\Prefetch` | 预读取缓存（默认仅清理 7 天前的） |
| `dism` | Windows 组件存储 | 通过 DISM 清理 WinSxS 冗余组件（带进度显示） |
| `sw_dist` | `SoftwareDistribution\Download` | Windows Update 下载包 |
| `win_old` | `C:\Windows.old` | 旧版 Windows 备份（清理后无法回滚） |
| `system_restore` | 系统还原点 | 清理旧的卷影副本，默认保留最新 1 个（v2.1 新增） |
| `old_drivers` | 旧驱动程序包 | 通过 DISM 清理被取代的驱动包（v2.1 新增） |
| `ie_cache` | IE 浏览器缓存 | Internet Explorer 缓存 |
| `edge_cache` | Edge 浏览器缓存 | Microsoft Edge 缓存和 Service Worker |
| `chrome_cache` | Chrome 浏览器缓存 | Google Chrome 缓存和 Service Worker |
| `qq_browser` | QQ 浏览器缓存 | QQ 浏览器缓存和 Service Worker |
| `firefox` | Firefox 缓存 | Firefox cache2/thumbnails（v2.0 新增） |
| `brave` | Brave 缓存 | Brave 浏览器缓存（v2.0 新增） |
| `opera` | Opera 缓存 | Opera / Opera GX 缓存（v2.0 新增） |
| `sogou` | 搜狗浏览器缓存 | 搜狗高速浏览器缓存（v2.0 新增） |
| `browser_360` | 360 浏览器缓存 | 360 安全/极速浏览器缓存（v2.0 新增） |
| `dns` | DNS 缓存 | 刷新 DNS 解析缓存 |
| `delivery_opt` | 传递优化文件 | Windows P2P 更新分发缓存 |
| `recycle` | 回收站 | 清空所有驱动器回收站 |
| `cbs_logs` | CBS 日志 | 组件服务日志文件 |
| `win_logs` | 系统日志目录 | `C:\Windows\Logs` 全目录日志（CBS 除外，v2.1 新增） |
| `event_logs` | 事件日志备份 | Windows 事件日志的备份/存档文件（v2.1 新增） |
| `crash_dump` | 崩溃转储/WER | 蓝屏转储、崩溃转储、错误报告 |
| `thumbnail` | 缩略图缓存 | 资源管理器缩略图数据库 |
| `font_cache` | 字体缓存 | Windows 字体缓存文件 |
| `defender` | Defender 缓存 | Windows Defender 扫描历史和支持日志（v2.1 新增） |
| `wps_backup` | WPS 文档备份 | WPS Office 自动备份文件（.bak） |
| `wps_logs` | WPS 日志 | WPS Office 运行日志 |
| `wps_cache` | WPS 缓存 | WPS 字体缓存、加载项缓存等 |
| `wps_recent` | WPS 最近文件 | 清除最近打开文件历史 |
| `wps_temp` | WPS 临时文件 | WPS 编辑过程临时文件 |
| `wps_recovery` | WPS 崩溃恢复 | 异常退出自动恢复文件 |
| `wps_cloud` | WPS 云文档缓存 | WPS 云文档本地同步缓存 |
| `pip_cache` | pip 缓存 | Python pip 下载缓存（v2.0 新增） |
| `npm_cache` | npm 全局缓存 | Node.js npm _cacache（v2.0 新增） |
| `yarn_cache` | yarn 包缓存 | Yarn v1/v2 缓存（v2.0 新增） |
| `huggingface` | HuggingFace 模型缓存 | Hub 模型下载缓存（v2.0 新增） |
| `ollama` | Ollama 本地模型 | Ollama 模型缓存（v2.0 新增） |
| `nuget` | NuGet 缓存 | .NET 包管理器缓存（v2.0 新增） |
| `bilibili` | Bilibili 缓存 | B 站客户端更新器缓存（v2.0 新增） |
| `baidunetdisk` | 百度网盘缓存 | 下载临时目录和日志缓存（v2.0 新增） |

## 安全策略

- **管理员权限检查**：未以管理员运行时自动提权
- **跳过占用文件**：文件被锁定时自动跳过，不会报错中断
- **时间阈值保护**：默认只删除超过 1 天未修改的文件
- **白名单保护**：仅清理指定目录，不触碰 System32 等核心目录
- **只读属性处理**：自动移除只读属性后删除
- **完整日志记录**：所有操作记录在 `cleaner.log`
- **Dry-run 预览**：先预览再执行

## 使用方法

### 一键清理（推荐）

直接双击 **`run.bat`**，自动提权 → 运行清理 → 显示磁盘变化 → 按任意键退出。

```
Before: 99.56 GB

Cleaning...

[系统清理输出...]

Before: 99.56 GB  After: 101.64 GB  Freed: +2.08 GB

Done. Log: cleaner.log
按任意键继续...
```

### 创建桌面快捷方式

右键 `run.bat` → 发送到 → 桌面快捷方式

然后右键桌面快捷方式 → 属性 → 高级 → 勾选"**以管理员身份运行**" → 确定

### 命令行用法

```bash
# 交互式运行（需要管理员权限）
python cleaner.py

# 全自动运行（安静不打扰）
python cleaner.py --yes

# 预览模式（只统计不删除）
python cleaner.py --dry-run

# 静默自动运行（适合定时任务）
python cleaner.py --quiet --no-confirm
```

### 高级用法

```bash
# 只清理临时文件
python cleaner.py --only temp_win,temp_user

# 跳过回收站和 DISM 清理
python cleaner.py --skip recycle,dism

# 只清理 7 天前的文件
python cleaner.py --days 7

# 详细模式（显示每个文件的处理）
python cleaner.py --verbose --dry-run

# 保存报告到文件
python cleaner.py --report 清理报告.txt

# 列出所有模块
python cleaner.py --list-modules
```

### 定时任务（计划任务）

已预设每天 **13:00** 自动运行。右键 **`update_task.bat`** → 以管理员身份运行 → 自动创建/更新任务。

> **关键**：定时任务以 SYSTEM 身份运行，SYSTEM 不认识 `python` 命令（不在其 PATH 中）。`update_task.bat` 会自动查找并使用 Python 的完整路径，确保 SYSTEM 能正确执行。

或者手动操作（注意用完整 python 路径）：

```bash
# 查看当前配置
schtasks /query /tn SystemCleaner /v

# 删除旧任务
schtasks /delete /tn SystemCleaner /f

# 创建新任务（必须用完整 python 路径）
schtasks /create /tn SystemCleaner /tr "cmd /c C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe D:\aitest\roc\projects\clear\cleaner.py --quiet --no-confirm >> D:\aitest\roc\projects\clear\cleaner_report.log 2>&1" /sc daily /st 13:00 /ru SYSTEM /rl HIGHEST /f
```

### 迁移到新路径

如果想移动整个工具到其他目录：

1. 复制 `clear` 文件夹到新位置
2. 编辑 `update_task.bat`，把第 7 行 `PROJECT` 改为新路径
3. 右键 `update_task.bat` → 以管理员身份运行
4. 同步更新桌面快捷方式的「目标」和「起始位置」

## 依赖

- Python 3.7+
- Windows 10/11
- 标准库（无需额外安装第三方包）

## 项目结构

```
cleaner/
├── cleaner.py                 # 核心清理工具（CLI 入口）
├── run.bat                    # ★ 一键启动（双击运行）
├── update_task.bat            # 定时任务创建/更新（右键管理员运行）
├── README.md                  # 本文件
├── cleaner.log                # 运行日志（自动生成）
├── cleaner_report.log         # 定时任务输出日志
├── tests/
│   ├── __init__.py
│   └── test_utils.py         # 13 个单元测试
└── cleaner/
    ├── __init__.py           # 包初始化（v2.0.0）
    ├── utils.py              # 公共工具函数 + Colors + clean_module 装饰器
    ├── report.py             # 清理报告
    ├── temp_files.py         # 临时文件清理
    ├── windows_update.py     # Windows 更新清理（DISM 进度条）
    ├── internet_cache.py     # 浏览器缓存清理（IE/Edge/Chrome/QQ）
    ├── browser_caches.py     # 额外浏览器缓存（Firefox/Brave/Opera/搜狗/360）★ 新增
    ├── delivery_opt.py       # 传递优化清理
    ├── recycle_bin.py        # 回收站清空
    ├── system_temp.py        # 系统临时文件
    ├── wps_cleaner.py        # WPS Office 垃圾清理
    ├── dev_caches.py         # 开发者缓存（pip/npm/yarn/HuggingFace/Ollama/NuGet）★ 新增
    └── app_caches.py         # 应用缓存（Bilibili/百度网盘）★ 新增
```

## 注意事项

- **必须以管理员身份运行**（`run.bat` 会自动提权）
- 清理 `Windows.old` 后无法回滚 Windows 版本
- 清理 Prefetch 后首次启动应用会稍慢
- 清空回收站操作不可撤销
- 建议首次使用时先运行 `--dry-run` 预览效果

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v2.1** | 2026-07-20 | 新增 5 个清理模块：系统日志目录、事件日志备份、Defender 缓存、系统还原点清理、旧驱动程序包清理；启用已实现但未注册的事件日志模块 |
| **v2.0** | 2026-07-15 | 新增 13 个清理模块（6 个开发者缓存 + 5 个浏览器 + 2 个应用缓存）；新增 `--yes` 全自动模式；新增 DISM 进度条显示；新增彩色输出；新增 `@clean_module` 装饰器减少模板代码；新增单元测试（13 个测试） |
| **v1.1** | 2026-06-25 | 新增 WPS Office 清理（7 个模块：备份/日志/缓存/最近文件/临时文件/崩溃恢复/云文档缓存）、QQ 浏览器缓存清理；添加 `.gitignore` 忽略本地配置文件 |
| **v1.0** | 2026-06-25 | 初始版本：16 个清理模块（Temp/Prefetch/DISM/Update/IE/Edge/Chrome/DNS/传递优化/回收站/CBS/崩溃转储/缩略图/字体缓存） |
