---
name: git-history-purger
description: Inspect, analyze, and purge oversized historical files, binary bloat, or accidental credentials from Git history using git-filter-repo. Use when repositories have bloated .git directories, slow clone times, large historical commits, when open-sourcing or modernizing projects, or when the user asks to clean up, curate, or shrink a Git repository.
---

# Git History Purger: Agent Skill Guide

This skill guides AI agents on when and how to safely inspect, analyze, and purge historical binary bloat or sensitive artifacts from any Git repository using the universal `git-history-purger` utility.

---

## 📍 Tool Location & Availability

The standalone tool is located at:
- **Primary Script**: `C:\src\git-history-purger\purge_git_history.py`
- **Module Entry**: `python C:\src\git-history-purger [args]`
- **PowerShell / CMD Launchers**: `C:\src\git-history-purger\purge-history.bat` / `.ps1`
- **Bundled Engine**: `C:\src\git-history-purger\git_filter_repo.py` (v2.47.0 standalone, requires NO pip install)

---

## 🎯 When to Activate This Skill

Trigger this workflow whenever:
1. **User asks about `.git/` size**: e.g., *"Why is my .git folder so big?"*, *"Can we shrink this repo?"*, *"How to make git light?"*
2. **Repository clone bloat**: A project has large historical binaries (PDFs, PPTX, videos, datasets, caches, `.zip`, `.npy`, raw image dumps) committed in past revisions.
3. **Open-sourcing / Modernization**: Transitioning a private or legacy research repository to a public GitHub repo where fast clone speeds and light footprint are essential.
4. **Accidental credentials / leaks**: Stripping accidental API keys, tokens, or private credentials across all historical commits.

---

## 🛡️ Built-in Safety Protocol

`purge_git_history.py` enforces safety automatically:
- **Clean Working Tree**: Aborts if uncommitted changes exist.
- **Safety Backup Branch**: Creates `backup_history_YYYYMMDD_HHMMSS`.
- **Full Safety Bundle**: Creates a complete `.git_backup_*.bundle` archive before rewriting history.
- **Automatic Remote Restoration**: Preserves and re-attaches remote origin post-filtering.
- **Immediate GC**: Automatically executes `git reflog expire --expire=now --all && git gc --prune=now --aggressive` to reclaim disk space immediately.

---

## 📋 Standard Agent Execution Workflow

Follow these steps sequentially when helping a user curate a repository:

### Step 1: Diagnose & Inspect
Always begin with a non-destructive scan of the largest objects in the repository:

```powershell
python C:\src\git-history-purger\purge_git_history.py --inspect --top 15
```
*(If operating from outside the target repository, add `--repo <PATH>`)*

Present the user with a summary table of the largest historical blobs and the total `.git` size.

### Step 2: Formulate the Purge Strategy
Based on the inspection output, select the appropriate filter strategy:
- **Global size threshold**: Use `--strip-blobs-bigger 3M` (or `5M`) to drop all historical files exceeding that size.
- **Specific directories**: Use `--purge-path results/ thesis/ temp/` to eliminate entire historical experimental directories.
- **File extensions**: Use `--purge-glob "*.pdf" "*.pptx" "*.zip" "*.docx"` to purge document drafts or archives.

### Step 3: Run Simulation (Dry-Run)
Demonstrate safety to the user by running a dry-run first:

```powershell
python C:\src\git-history-purger\purge_git_history.py --dry-run --strip-blobs-bigger 3M
```

### Step 4: Execute the History Purge
Run the command against the target repository:

```powershell
python C:\src\git-history-purger\purge_git_history.py `
  --strip-blobs-bigger 3M `
  --purge-path results/ thesis/ `
  --purge-glob "*.pdf" "*.pptx" "*.zip"
```

### Step 5: Verify Integrity & Space Reclaimed
1. Inspect commit log: `git log --oneline -n 10`
2. Verify test suite passes: e.g. `pytest` or project test command.
3. Report the before-and-after `.git` sizes and space reclaimed.

### Step 6: Guide User on Force-Push
Explain to the user that rewriting Git history creates new commit hashes. To publish to GitHub:

```bash
git push --force origin <current-branch>
```

---

## 🔄 Recovery Protocol (If User Needs to Revert)

If the user wants to revert to the state prior to the purge:
```bash
# Option A: Reset to the backup branch created before filtering
git reset --hard backup_history_YYYYMMDD_HHMMSS

# Option B: Restore from the backup bundle
git pull .git_backup_YYYYMMDD_HHMMSS.bundle main
```

---

## 🌐 Portability & Cross-Machine Setup

When moving to another machine:
1. Clone the repository:
   ```bash
   git clone https://github.com/davtoh/git-history-purger.git C:\src\git-history-purger
   ```
2. Copy or symlink this skill file to the user's Antigravity config directory:
   ```powershell
   Copy-Item -Path C:\src\git-history-purger\skills\git-history-purger\SKILL.md -Destination ~/.gemini/config/skills/git-history-purger/SKILL.md -Force
   ```
3. The tool is ready immediately on the new machine with standard Python 3.
