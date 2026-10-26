"""
Entry point for running git-history-purger as a directory or module:
  python C:\\src\\git-history-purger [args]
"""
import sys
from pathlib import Path

# Ensure local imports work cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent))
from purge_git_history import main

if __name__ == "__main__":
    main()
