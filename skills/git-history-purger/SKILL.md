---
name: git-history-purger
description: Inspect, analyze, and purge oversized historical files, binary bloat, or accidental credentials from Git history using git-filter-repo. Use when repositories have bloated .git directories, slow clone times, large historical commits, when open-sourcing or modernizing projects, or when the user asks to clean up, curate, or shrink a Git repository.
---

# Git History Purger: Agent Skill Guide

This skill guides AI agents on when and how to safely inspect, analyze, and purge historical binary bloat or sensitive artifacts from any Git repository using the universal `git-history-purger` utility.

---

## 📍 Dynamic Tool Resolution (Zero Hardcoded Paths)

The tool is completely portable across Windows, macOS, and Linux. When executing commands, AI agents should resolve the tool in the following order:

1. **System Command (Preferred)**:
   If installed in `PATH` or virtual environment (via `pip install -e .`):
   ```bash
   purge-history [args]
   ```
2. **Skill's Bundled Script (Self-Contained)**:
   Every installed instance of this skill contains its own scripts directory:
   ```bash
   python "<path-to-this-skill-dir>/scripts/purge_git_history.py" [args]
   ```
   *(Antigravity agents receive the exact directory path of this `SKILL.md` in the system prompt).*
3. **Repository Standalone**:
   If running inside or referencing the cloned `git-history-purger` repository:
   ```bash
   python purge_git_history.py [args]
   # Or directory module execution:
   python <path-to-cloned-repo> [args]
   ```

Because `git_filter_repo.py` is bundled directly alongside `purge_git_history.py`, **no `pip install` or external Git plugins are required**.

---

## 🎯 When to Activate This Skill

Trigger this workflow whenever:
1. **User asks about `.git/` size**: e.g., *"Why is my .git folder so big?"*, *"Can we shrink this repo?"*, *"How to make git light?"*
2. **Repository clone bloat**: A project has large historical binaries (PDFs, PPTX, videos, datasets, caches, `.zip`, `.npy`, raw image dumps) committed in past revisions.
3. **Open-sourcing / Modernization**: Transitioning a private or legacy research repository to a public GitHub repo where fast clone speeds and light footprint are essential.
4. **Accidental credentials / leaks**: Stripping accidental API keys, tokens, or private credentials across all historical commits.

---

## 🛡️ Built-in Safety Protocol

`purge_git_history.py` enforces safety automatically on the target repository:
- **Clean Working Tree**: Aborts if uncommitted changes exist.
- **Safety Backup Branch**: Automatically creates `backup_history_YYYYMMDD_HHMMSS`.
- **Full Safety Bundle**: Automatically creates a complete `.git_backup_*.bundle` archive before rewriting history.
- **Automatic Remote Restoration**: Preserves and re-attaches remote origin post-filtering.
- **Immediate GC**: Automatically executes `git reflog expire --expire=now --all && git gc --prune=now --aggressive` to reclaim disk space immediately.

---

## 📋 Standard Agent Execution Workflow

Follow these steps sequentially when helping a user curate a repository:

### Step 1: Diagnose & Inspect
Always begin with a non-destructive scan of the largest objects in the repository:

```bash
purge-history --inspect --top 15
# Or: python "<skill-dir>/scripts/purge_git_history.py" --inspect --top 15
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

```bash
purge-history --dry-run --strip-blobs-bigger 3M
```

### Step 4: Execute the History Purge
Run the command against the target repository:

```bash
purge-history \
  --strip-blobs-bigger 3M \
  --purge-path results/ thesis/ \
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
   git clone https://github.com/davtoh/git-history-purger.git
   ```
2. Install the skill into Antigravity with a single command:
   ```bash
   python git-history-purger/purge_git_history.py --install-skill
   ```
   *(Or optionally install as a global CLI command: `pip install -e ./git-history-purger`)*
