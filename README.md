# Git History Purger 🚀

A lightweight, standalone, and safety-first CLI utility to inspect, analyze, and purge oversized historical files, binary bloat, and confidential artifacts from any Git repository.

Bundles [`git-filter-repo`](https://github.com/newren/git-filter-repo) directly so it works out-of-the-box on any machine with standard Python 3—**zero `pip install` or complex PATH setup required**.

---

## 🌟 Key Features

- **⚡ Zero Setup Required**: Includes a bundled standalone copy of `git-filter-repo`. Runs immediately with `python purge_git_history.py`.
- **🛡️ Safety-First Architecture**:
  - Automatically verifies a clean working tree before touching history.
  - Automatically creates a timestamped Git backup branch (`backup_history_YYYYMMDD_HHMMSS`).
  - Automatically generates an uncompressed full `.git_backup_*.bundle` snapshot.
- **🌐 Universal Multi-Project Support**:
  - Defaults to the current repository (`Path.cwd()`).
  - Or target any external project with `--repo C:\path\to\project`.
  - Automatically discovers and restores all Git remotes (`origin`, `upstream`, etc.) after filtering.
- **🔍 Fast Blob Inspection**:
  - Instantly inspect the top $N$ largest historical files ever committed with `--inspect` or `--top 20`.
- **🧹 Automatic Reclamation**:
  - Automatically expires reflogs and runs aggressive garbage collection (`git gc --prune=now --aggressive`) to immediately shrink `.git` folder size on disk.
- **📊 Detailed Metrics**:
  - Reports `.git` size before and after, showing exact megabytes reclaimed and percentage reduction.

---

## 📂 Project Structure

```
C:\src\git-history-purger\
├── git_filter_repo.py     # Bundled upstream git-filter-repo engine (v2.47.0)
├── purge_git_history.py   # Universal CLI orchestrator & safety wrapper
├── __main__.py            # Directory execution support: python C:\src\git-history-purger
├── purge-history.bat      # Windows CMD launcher
├── purge-history.ps1      # Windows PowerShell launcher
├── README.md              # Full documentation & usage guide
└── .gitignore
```

---

## 🚀 Quickstart & Usage

### 1. Inspect Largest Files in History (Safe, Read-Only)

Navigate to any git project and run:

```powershell
python C:\src\git-history-purger\purge_git_history.py --inspect
```

Or target another repository directly:

```powershell
python C:\src\git-history-purger\purge_git_history.py --repo C:\dev\projects\products\my-app --inspect
```

*Sample output:*
```text
[*] Scanning Git object database in: C:\dev\projects\products\rrtools
[*] Listing top 10 largest historical objects...

Size           Object Hash    File Path
--------------------------------------------------------------------------------
42.66 MB       e8a1f29c01     thesis/draft_main.pdf
36.99 MB       0d82fa910b     draft.pdf
27.28 MB       b14f828114     thesis/draft_IMPLEMENTATION.pdf
13.28 MB       4a7e91244f     dissertation.pdf
 8.91 MB       9481b82fa0     thesis/presentation.pptx
 8.45 MB       74917481ba     tests/im_completer_Result2.png
--------------------------------------------------------------------------------
Total .git directory size: 610.89 MB
```

---

### 2. Dry-Run a Purge (Simulation)

Test what would happen without altering your Git history:

```powershell
python C:\src\git-history-purger\purge_git_history.py --dry-run --strip-blobs-bigger 3M
```

---

### 3. Purge Blobs Exceeding a Size Limit

Strip any historical object larger than `3M`, `5M`, or `500K`:

```powershell
python C:\src\git-history-purger\purge_git_history.py --strip-blobs-bigger 3M
```

---

### 4. Purge Specific Historical Folders or Files

Purge entire folders or specific files from all commits:

```powershell
# Purge multiple directories:
python C:\src\git-history-purger\purge_git_history.py --purge-path results/ thesis/ temp/

# Purge specific files:
python C:\src\git-history-purger\purge_git_history.py --purge-path draft.pdf dissertation.pdf
```

---

### 5. Purge by File Pattern / Extension

Strip all PDFs, PowerPoint files, or large archives across the entire repository history:

```powershell
python C:\src\git-history-purger\purge_git_history.py --purge-glob "*.pdf" "*.pptx" "*.docx" "*.zip"
```

---

### 6. Combined Power Purge

You can combine size filters, paths, and glob patterns in a single command:

```powershell
python C:\src\git-history-purger\purge_git_history.py `
  --strip-blobs-bigger 5M `
  --purge-path results/ thesis/ `
  --purge-glob "*.pdf" "*.pptx" "*.zip"
```

---

## 🛠️ CLI Options Reference

| Option | Shorthand | Description |
|---|---|---|
| `--inspect` | `-i` | List the largest historical objects in Git history (read-only). |
| `--top <N>` | | Number of objects to display in inspect mode (default: 20). |
| `--repo <PATH>` | `-C` | Path to target Git repo (defaults to current working directory). |
| `--dry-run` | `-n` | Simulate history rewrite without altering Git history. |
| `--strip-blobs-bigger <SIZE>` | | Purge blobs larger than threshold (e.g. `1M`, `3M`, `10M`, `500K`). |
| `--purge-path <PATH...>` | | One or more historical paths/directories to purge across all commits. |
| `--purge-glob <PATTERN...>` | | One or more filename globs to purge (e.g. `'*.pdf'`, `'*.zip'`). |
| `--analyze` | `-a` | Run `git-filter-repo --analyze` to generate full reports in `.git/filter-repo/analysis/`. |
| `--no-gc` | | Skip aggressive `git gc` and reflog expiration after filtering. |

---

## 🛡️ Safety & Recovery Protocol

Every purge automatically creates two safety artifacts in the target repository:
1. **A local Git backup branch**: e.g., `backup_history_20261026_183500`.
2. **A full standalone Git bundle**: e.g., `.git_backup_20261026_183500.bundle`.

### How to Restore if Needed
If you ever want to revert a purge:
```bash
# Option A: Fast reset to the backup branch
git reset --hard backup_history_YYYYMMDD_HHMMSS

# Option B: Restore from the bundle
git pull .git_backup_YYYYMMDD_HHMMSS.bundle main
```

---

## 🚀 Publishing Clean History to Remote

Once you have verified your clean commit history and test suite:

```bash
# Push the updated, lightweight history to GitHub/GitLab:
git push --force origin main
```

*(Replace `main` with `master` if your repository uses the legacy default branch).*

---

## 💡 Optional: Add to Windows System PATH

To run `purge-history` from any command prompt or PowerShell window without specifying the full path:
1. Add `C:\src\git-history-purger` to your user `PATH` environment variable.
2. In any terminal, simply run:
   ```powershell
   purge-history --inspect
   ```
