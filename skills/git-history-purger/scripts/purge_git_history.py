#!/usr/bin/env python3
"""
git-history-purger / purge_git_history.py

Universal automated CLI tool to inspect, analyze, and safely purge large historical
blobs, files, and directories from any Git repository using git-filter-repo.

Features:
- Completely standalone: bundles git-filter-repo (no pip install or PATH setup needed).
- Universal: Works on ANY git repository (defaults to current directory or --repo <path>).
- Zero hardcoded paths: Fully portable across Windows, Linux, and macOS.
- Safety-first: Verifies clean working tree, creates backup branch & full .git bundle.
- Size reporting: Shows before & after .git folder sizes and calculated reduction.
- Automatic remote restoration: Preserves all git remotes after filter-repo executes.
- Flexible filtering: Strip by size (--strip-blobs-bigger), path (--purge-path), or glob (--purge-glob).
- Inspection mode: Fast top-N largest historical blobs report.

Usage:
  # Inspect top 20 largest blobs in current repo:
  purge-history --inspect
  # (or: python purge_git_history.py --inspect)

  # Inspect in another repo:
  purge-history --repo /path/to/repo --inspect

  # Dry-run stripping blobs bigger than 3MB:
  purge-history --dry-run --strip-blobs-bigger 3M

  # Purge blobs bigger than 3MB and specific file types:
  purge-history --strip-blobs-bigger 3M --purge-glob "*.pdf" "*.zip"

  # Purge specific paths:
  purge-history --purge-path results thesis temp
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
BUNDLED_FILTER_REPO = TOOL_DIR / "git_filter_repo.py"


def get_git_size_bytes(repo_root: Path) -> int:
    """Calculate the total size in bytes of the .git directory."""
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return 0
    total = 0
    try:
        for entry in git_dir.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total


def format_size(bytes_val: float) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    if bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{int(bytes_val)} bytes"


def run_cmd(cmd, cwd: Path, check=True, capture=True):
    """Run a shell or list command and return subprocess.CompletedProcess."""
    if isinstance(cmd, list):
        shell = False
    else:
        shell = True
    res = subprocess.run(
        cmd,
        cwd=cwd,
        shell=shell,
        text=True,
        capture_output=capture,
    )
    if check and res.returncode != 0:
        print(f"\n[ERROR] Command failed with exit code {res.returncode}:")
        if isinstance(cmd, list):
            print(f"  {' '.join(cmd)}")
        else:
            print(f"  {cmd}")
        if res.stderr:
            print(res.stderr.strip())
        sys.exit(res.returncode)
    return res


def verify_repo(repo_root: Path) -> Path:
    """Verify that the target path is a valid Git repository."""
    repo_root = repo_root.resolve()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        print(f"[ERROR] Target path is not a Git repository (no .git directory found):\n  {repo_root}")
        sys.exit(1)
    return repo_root


def check_working_tree(repo_root: Path):
    """Ensure working tree is clean before rewriting history."""
    res = run_cmd("git status --porcelain", cwd=repo_root)
    if res.stdout.strip():
        print("[WARNING] Target repository has uncommitted or untracked changes:")
        print(res.stdout)
        print("Please commit or stash your changes before running a history rewrite.")
        sys.exit(1)


def create_safety_backup(repo_root: Path):
    """Create a backup branch and git bundle before rewriting history."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_branch = f"backup_history_{timestamp}"
    print(f"[*] Creating safety backup branch: {backup_branch}")
    run_cmd(f"git branch {backup_branch}", cwd=repo_root)

    backup_bundle = repo_root / f".git_backup_{timestamp}.bundle"
    print(f"[*] Creating full safety Git bundle: {backup_bundle.name}")
    run_cmd(f'git bundle create "{backup_bundle}" --all', cwd=repo_root)
    print(f"[OK] Safety backup verified.")
    print(f"     Restore instruction if ever needed: git pull {backup_bundle.name} HEAD\n")
    return backup_branch, backup_bundle


def inspect_large_blobs(repo_root: Path, top_n: int = 20):
    """Inspect and list the largest blobs in the Git commit history."""
    print(f"[*] Scanning Git object database in: {repo_root}")
    print(f"[*] Listing top {top_n} largest historical objects...\n")

    ps_cmd = (
        'git rev-list --objects --all | '
        'git cat-file --batch-check="%(objecttype) %(objectname) %(objectsize) %(rest)"'
    )
    res = run_cmd(ps_cmd, cwd=repo_root, check=False)
    if not res.stdout:
        print("No Git objects found or command failed.")
        return

    blobs = []
    for line in res.stdout.splitlines():
        parts = line.strip().split(maxsplit=3)
        if len(parts) >= 3 and parts[0] == "blob":
            try:
                size = int(parts[2])
                path = parts[3] if len(parts) > 3 else "unknown"
                blobs.append((size, parts[1], path))
            except ValueError:
                continue

    blobs.sort(key=lambda x: x[0], reverse=True)

    print(f"{'Size':<14} {'Object Hash':<14} {'File Path'}")
    print("-" * 80)
    seen_paths = set()
    count = 0
    for size, obj_hash, path in blobs:
        if path in seen_paths and path != "unknown":
            continue
        seen_paths.add(path)
        size_str = format_size(size)
        print(f"{size_str:<14} {obj_hash[:10]:<14} {path}")
        count += 1
        if count >= top_n:
            break
    print("-" * 80)

    total_git_size = get_git_size_bytes(repo_root)
    print(f"Total .git directory size: {format_size(total_git_size)}\n")


def get_all_remotes(repo_root: Path):
    """Retrieve all configured git remotes and their URLs."""
    res = run_cmd("git remote -v", cwd=repo_root, check=False)
    remotes = {}
    if res.returncode == 0 and res.stdout.strip():
        for line in res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name, url = parts[0], parts[1]
                if name not in remotes:
                    remotes[name] = url
    return remotes


def resolve_filter_repo_cmd() -> list:
    """Find the best command invocation for git-filter-repo."""
    # 1. Check if git-filter-repo is in system PATH
    system_tool = shutil.which("git-filter-repo")
    if system_tool:
        return [system_tool]

    # 2. Check bundled script relative to this file
    if BUNDLED_FILTER_REPO.exists():
        return [sys.executable, str(BUNDLED_FILTER_REPO)]

    # 3. Fallback to python module
    return [sys.executable, "-m", "git_filter_repo"]


def run_filter_repo(repo_root: Path, filter_flags: list, dry_run: bool = False, run_gc: bool = True):
    """Execute history rewrite on target repo with safety protections."""
    check_working_tree(repo_root)
    remotes = get_all_remotes(repo_root)
    initial_git_size = get_git_size_bytes(repo_root)

    filter_cmd_base = resolve_filter_repo_cmd()

    full_cmd = filter_cmd_base + ["--force"] + filter_flags

    if dry_run:
        full_cmd_dry = filter_cmd_base + ["--dry-run", "--force"] + filter_flags
        print("\n" + "=" * 80)
        print("[DRY RUN] Simulating git-filter-repo execution:")
        print(f"  Command: {' '.join(full_cmd_dry)}")
        print(f"  Working Directory: {repo_root}")
        print("=" * 80)
        res = subprocess.run(full_cmd_dry, cwd=repo_root)
        print("\n[OK] Dry-run complete. (No permanent changes were made to Git history.)")
        return

    print("\n" + "=" * 80)
    print("STARTING GIT HISTORY PURGE")
    print(f"Target repository: {repo_root}")
    print(f"Initial .git size: {format_size(initial_git_size)}")
    print("=" * 80)

    backup_branch, backup_bundle = create_safety_backup(repo_root)

    print(f"[*] Executing:\n    {' '.join(full_cmd)}\n")
    res = subprocess.run(full_cmd, cwd=repo_root)
    if res.returncode != 0:
        print(f"\n[ERROR] git-filter-repo exited with code {res.returncode}")
        print("Your repository history was NOT modified or has been preserved in your backup.")
        return

    # git-filter-repo automatically strips remotes for safety; restore them
    if remotes:
        print("\n[*] Restoring Git remotes:")
        for name, url in remotes.items():
            print(f"    - {name}: {url}")
            run_cmd(f"git remote add {name} {url}", cwd=repo_root, check=False)

    if run_gc:
        print("\n[*] Running aggressive Git garbage collection to prune unreferenced objects...")
        run_cmd("git reflog expire --expire=now --all", cwd=repo_root, check=False)
        run_cmd("git gc --prune=now --aggressive", cwd=repo_root, check=False)

    final_git_size = get_git_size_bytes(repo_root)
    saved_bytes = max(0, initial_git_size - final_git_size)
    reduction_pct = (saved_bytes / initial_git_size * 100) if initial_git_size > 0 else 0

    print("\n" + "=" * 80)
    print("PURGE SUMMARY & RESULTS:")
    print(f"  Initial .git size: {format_size(initial_git_size)}")
    print(f"  Final .git size:   {format_size(final_git_size)}")
    print(f"  Reclaimed space:   {format_size(saved_bytes)} ({reduction_pct:.1f}% reduction)")
    print("=" * 80)

    print("\nVERIFICATION & NEXT STEPS:")
    print("1. Inspect commit log to verify history is clean:")
    print(f"     cd {repo_root}")
    print("     git log --oneline -n 10")
    print("2. Verify working tree status and run your test suite:")
    print("     git status")
    print("3. When you are ready to publish the clean history to remote, force-push:")
    default_branch = "main"
    res_branch = run_cmd("git branch --show-current", cwd=repo_root, check=False)
    if res_branch.returncode == 0 and res_branch.stdout.strip():
        default_branch = res_branch.stdout.strip()
    print(f"     git push --force origin {default_branch}")
    print("=" * 80 + "\n")


def install_agent_skill():
    """Install the git-history-purger skill into the user's Antigravity config directory."""
    home_dir = Path.home()
    target_skill_dir = home_dir / ".gemini" / "config" / "skills" / "git-history-purger"
    source_skill_dir = TOOL_DIR / "skills" / "git-history-purger"

    if not source_skill_dir.exists():
        print(f"[ERROR] Source skill directory not found: {source_skill_dir}")
        return

    target_skill_dir.mkdir(parents=True, exist_ok=True)
    # Copy SKILL.md
    shutil.copy2(source_skill_dir / "SKILL.md", target_skill_dir / "SKILL.md")
    # Copy scripts/
    target_scripts_dir = target_skill_dir / "scripts"
    target_scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TOOL_DIR / "purge_git_history.py", target_scripts_dir / "purge_git_history.py")
    if BUNDLED_FILTER_REPO.exists():
        shutil.copy2(BUNDLED_FILTER_REPO, target_scripts_dir / "git_filter_repo.py")

    print(f"[OK] Agent skill successfully installed into:")
    print(f"     {target_skill_dir}")
    print("[*] All Antigravity AI agents on this machine will now automatically discover and use this tool.")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect and purge large historical files/blobs from any Git repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Inspect largest blobs in current repository:
  purge-history --inspect
  python purge_git_history.py --inspect

  # Inspect a specific repository:
  purge-history --repo /path/to/project --inspect

  # Purge blobs larger than 3MB in current repo:
  purge-history --strip-blobs-bigger 3M

  # Purge multiple file patterns:
  purge-history --purge-glob "*.pdf" "*.pptx" "*.zip"

  # Purge specific historical paths:
  purge-history --purge-path results/ thesis/ temp/

  # Install skill for AI agents on this machine:
  python purge_git_history.py --install-skill
        """,
    )
    parser.add_argument(
        "--repo",
        "-C",
        type=str,
        default=None,
        help="Path to the target Git repository (defaults to current working directory).",
    )
    parser.add_argument(
        "--inspect",
        "-i",
        action="store_true",
        help="List the largest historical objects in Git history without changing anything.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of objects to display in --inspect mode (default: 20).",
    )
    parser.add_argument(
        "--analyze",
        "-a",
        action="store_true",
        help="Run git-filter-repo --analyze to generate detailed reports in .git/filter-repo/analysis.",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate a history purge without modifying Git objects.",
    )
    parser.add_argument(
        "--strip-blobs-bigger",
        type=str,
        default=None,
        help="Purge any historical blob larger than specified size (e.g., '1M', '3M', '10M', '500K').",
    )
    parser.add_argument(
        "--purge-path",
        nargs="+",
        default=[],
        help="One or more historical paths or directories to purge (e.g., 'results' 'thesis/draft.pdf').",
    )
    parser.add_argument(
        "--purge-glob",
        nargs="+",
        default=[],
        help="One or more filename glob patterns to purge across all commits (e.g., '*.pdf' '*.zip').",
    )
    parser.add_argument(
        "--no-gc",
        action="store_true",
        help="Skip aggressive git gc and reflog expiration after filtering.",
    )
    parser.add_argument(
        "--install-skill",
        action="store_true",
        help="Install the git-history-purger skill into ~/.gemini/config/skills/ for AI agents.",
    )

    args = parser.parse_args()

    # Install skill option
    if args.install_skill:
        install_agent_skill()
        return

    repo_dir = Path(args.repo).resolve() if args.repo else Path.cwd()
    repo_root = verify_repo(repo_dir)

    # 1. Analyze mode
    if args.analyze:
        filter_cmd_base = resolve_filter_repo_cmd()
        print(f"[*] Generating detailed git-filter-repo analysis in: {repo_root}")
        subprocess.run(filter_cmd_base + ["--analyze"], cwd=repo_root)
        print(f"[OK] Reports written to: {repo_root / '.git' / 'filter-repo' / 'analysis'}")
        return

    # 2. Inspect mode (default if no purge actions specified)
    no_actions = not args.strip_blobs_bigger and not args.purge_path and not args.purge_glob and not args.dry_run
    if args.inspect or no_actions:
        inspect_large_blobs(repo_root, top_n=args.top)
        return

    # 3. Build filter-repo arguments
    filter_flags = []
    if args.strip_blobs_bigger:
        filter_flags.extend(["--strip-blobs-bigger", args.strip_blobs_bigger])

    for p in args.purge_path:
        filter_flags.extend(["--path", p, "--invert-paths"])

    for g in args.purge_glob:
        filter_flags.extend(["--path-glob", g, "--invert-paths"])

    if not filter_flags and args.dry_run:
        filter_flags.extend(["--strip-blobs-bigger", "3M"])

    run_filter_repo(
        repo_root=repo_root,
        filter_flags=filter_flags,
        dry_run=args.dry_run,
        run_gc=not args.no_gc,
    )


if __name__ == "__main__":
    main()
