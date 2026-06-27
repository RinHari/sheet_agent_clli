import getpass
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_AUDIT_LOG_PATH = "logs/audit_log.jsonl"
READ_ONLY_FILE_MODE = 0o400
WRITABLE_FILE_MODE = 0o600


def get_current_actor(actor: Optional[str] = None) -> str:
    if actor:
        return actor

    env_actor = os.getenv("SHEET_AGENT_USER")
    if env_actor:
        return env_actor

    return getpass.getuser()


def get_audit_log_path() -> Path:
    return Path(os.getenv("AUDIT_LOG_PATH", DEFAULT_AUDIT_LOG_PATH))


def write_audit_log(event: dict[str, Any]) -> Path:
    log_path = get_audit_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if log_path.exists():
        os.chmod(log_path, WRITABLE_FILE_MODE)

    event_with_timestamp = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                json.dumps(event_with_timestamp, ensure_ascii=False, sort_keys=True)
            )
            log_file.write("\n")
    finally:
        os.chmod(log_path, READ_ONLY_FILE_MODE)

    return log_path
