#!/usr/bin/env python3
"""
Termux Master Ultra - Resilient Task Scheduler
Zero-dependency background task scheduler with file locking and atomic state persistence.
"""

import os
import sys
import time
import json
import fcntl
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# --- Configuration & Hardening ---
MASTER_STORAGE = Path(os.environ.get("MASTER_STORAGE", Path.home() / ".termux_master")).resolve()
TASKS_DIR = MASTER_STORAGE / "tasks"
LOGS_DIR = MASTER_STORAGE / "logs"
LOCKS_DIR = MASTER_STORAGE / "locks"
STATE_FILE = MASTER_STORAGE / "scheduler_state.json"

for p in (MASTER_STORAGE, TASKS_DIR, LOGS_DIR, LOCKS_DIR):
    p.mkdir(mode=0o700, parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def atomic_write_json(filepath: Path, data: dict):
    """Write dictionary atomically using temporary file and rename with 0600 permissions."""
    tmp_file = filepath.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, indent=2))
    tmp_file.chmod(0o600)
    os.replace(tmp_file, filepath)

def run_task(task_name: str, command: str):
    """Execute a scheduled task with file locking and output redirection."""
    lock_path = LOCKS_DIR / f"{task_name}.lock"
    log_path = LOGS_DIR / f"{task_name}.log"

    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logging.warning(f"Task '{task_name}' is already running. Skipping overlap.")
            return

        logging.info(f"Executing task: {task_name} -> {command}")
        start_time = time.time()
        
        try:
            with open(log_path, "a") as log_out:
                result = subprocess.run(
                    command,
                    shell=True,
                    stdout=log_out,
                    stderr=subprocess.STDOUT,
                    cwd=MASTER_STORAGE
                )
            duration = time.time() - start_time
            status = "success" if result.returncode == 0 else "failed"
            logging.info(f"Task '{task_name}' completed with status '{status}' in {duration:.2f}s")
        except Exception as e:
            logging.error(f"Failed to execute task '{task_name}': {e}")
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)

def main_loop():
    logging.info("Starting TMU Scheduler loop...")
    while True:
        # Example tick: Check scheduled tasks or execute registered workflows
        time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run-once":
        if len(sys.argv) < 3:
            print("Usage: scheduler.py run-once <task_name> '<command>'")
            sys.exit(2)
        run_task(sys.argv[2], sys.argv[3])
    else:
        main_loop()
