# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Windows system junk cleaner — a Python CLI tool that safely removes temp files, browser caches, system logs, and other junk from Windows 10/11. No third-party dependencies; uses only the Python standard library + Windows built-in tools (DISM, ipconfig, Shell API via ctypes).

## Common commands

```bash
# Interactive run (requires admin)
python cleaner.py

# Full auto mode — quiet, no confirm, runs everything (v2.0)
python cleaner.py --yes

# Dry-run preview — always run this first when adding/editing a cleaning module
python cleaner.py --dry-run --no-confirm

# Silent automated run (for scheduled tasks)
python cleaner.py --quiet --no-confirm

# Run only specific modules
python cleaner.py --only temp_win,temp_user

# Skip specific modules
python cleaner.py --skip recycle,dism

# List all registered modules (grouped by category, v2.0)
python cleaner.py --list-modules

# Save report to file
python cleaner.py --report report.txt

# One-click launch (auto-elevates to admin)
run.bat

# Update the scheduled task (edit path on line 3 first)
powershell -ExecutionPolicy Bypass -File update_task.ps1

# Run tests
python tests/test_utils.py
```

## Architecture

```
cleaner.py              # CLI entry point — argument parsing, module dispatch, report orchestration
cleaner/
├── __init__.py          # Package init, version v2.0.0
├── utils.py             # Shared utilities + Colors class + clean_module decorator
├── report.py            # CleanupReport class
├── temp_files.py        # clean_windows_temp, clean_user_temp, clean_prefetch
├── windows_update.py    # DISM with progress bar, clean_software_distribution, clean_windows_old
├── internet_cache.py    # IE/Edge/Chrome/QQ browser cache, DNS flush
├── browser_caches.py    # Firefox/Brave/Opera/Sogou/360 browser cache  ★ NEW
├── delivery_opt.py      # Delivery Optimization cleanup
├── recycle_bin.py       # empty_recycle_bin via SHEmptyRecycleBinW
├── system_temp.py       # CBS logs, crash dumps, thumbnails, font cache
├── wps_cleaner.py       # WPS Office (7 modules)
├── dev_caches.py        # pip/npm/yarn/HuggingFace/Ollama/NuGet  ★ NEW
└── app_caches.py        # Bilibili/BaiduNetdisk (cache only)  ★ NEW
tests/
├── __init__.py
└── test_utils.py        # 13 unit tests for utils.py  ★ NEW
```

## Module pattern

Every cleaning module follows a uniform contract:

1. **Function signature**: `clean_xxx(days_old=1, dry_run=False)` or a subset of those params. The `run_module()` dispatcher in `cleaner.py` uses `inspect.signature` to only pass params the function accepts.
2. **Return type**: `dict` with keys `{"deleted_count", "deleted_size", "skipped_count", "dirs_removed"}` — all ints.
3. **Atomicity**: each module is independent; a failure in one does not stop others.
4. **Logging**: use `from .utils import logger` (not `print`). Modules log at `logger.info` level by default; `logger.debug` for per-file details.
5. **Dry-run**: must be respected throughout — when `True`, log intent but perform zero deletions.
6. **Decorator shortcut (v2.0)**: For simple modules that only return a list of paths to clean, use `@clean_module(label, days_old=N)` from `utils.py`. The decorator handles logging, size measurement, safe_rmtree, and result reporting automatically.

## Adding a new cleaning module

1. Create (or use an existing) `.py` file under `cleaner/`.
2. Implement the function following the module pattern above.
3. Register it in `cleaner.py`'s `MODULES` list as `(name, label, function, kwargs)`.
   - `name`: short id for `--only`/`--skip` (e.g. `"browser_logs"`)
   - `label`: human-readable Chinese description
   - `kwargs`: optional extra defaults merged with the CLI `days_old`/`dry_run`
4. Update the README feature table.

## Key design decisions

- **No deletion without age check by default**: `safe_rmtree` uses `days_old` to skip files modified within the cutoff window. The CLI default is 1 day (overridable via `--days`). A few modules (Prefetch, CBS logs, crash dumps) override to 7 days.
- **Locked file tolerance**: `is_file_locked()` checks via `O_EXCL` open; locked files are skipped silently, not errored.
- **Read-only file handling**: `safe_delete` calls `os.chmod(filepath, stat.S_IWRITE)` before `os.remove`.
- **Admin detection at startup**: `is_admin()` via `ctypes.windll.shell32.IsUserAnAdmin`. Non-admin runs warn but allow continuation (most modules will just skip inaccessible paths).
- **Dual logging**: console gets INFO+ (configurable via `--quiet`/`--verbose`), `cleaner.log` always gets DEBUG+ for audit trail.
- **DISM with progress (v2.0)**: `_run_dism_with_progress()` parses DISM's stdout to show a real-time `[==== xx% ====]` progress bar instead of blocking silently.
- **Color output (v2.0)**: `Colors` class auto-enables Windows 10+ ANSI/VT support via `SetConsoleMode` and provides green/red/yellow/cyan helpers.
- **`@clean_module` decorator (v2.0)**: Reduces boilerplate for simple path-cleaning modules. The decorator handles logging, size measurement, `safe_rmtree`, and result reporting — the function just returns a list of paths.
- **`--yes` mode (v2.0)**: Shortcut for `--quiet --no-confirm` — fully automatic, no prompts.
- **Recycle bin**: uses `SHEmptyRecycleBinW` with `SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND` flags — silent, no dialog.

## Scheduled task

`update_task.ps1` registers a Windows Task Scheduler job named `SystemCleaner`:
- Runs daily at 13:00 as `SYSTEM` with highest privileges
- Executes `cleaner.py --quiet --no-confirm` with `PYTHONIOENCODING=gbk` (Chinese Windows compatibility)
- Output redirected to `cleaner_report.log`
- To migrate paths: edit `$ProjectPath` on line 3, then re-run the script
