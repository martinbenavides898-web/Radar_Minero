from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT_PATHS = (
    PROJECT_ROOT / ".cache" / "news_snapshot.json",
    Path("/tmp/radar_minero_news_snapshot.json"),
)
BOOTSTRAP_PATH = PROJECT_ROOT / "data" / "bootstrap_news.json"


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _deserialize_item(item: dict) -> dict:
    restored = dict(item)
    restored["published_at"] = _parse_datetime(restored.get("published_at"))
    return restored


def _read_payload(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    chile = payload.get("chile")
    world = payload.get("world")
    if not isinstance(chile, list) or not isinstance(world, list):
        return None

    payload["chile"] = [_deserialize_item(item) for item in chile if isinstance(item, dict)]
    payload["world"] = [_deserialize_item(item) for item in world if isinstance(item, dict)]
    payload["saved_at"] = _parse_datetime(payload.get("saved_at"))
    return payload


def save_news_snapshot(
    *,
    chile: list[dict],
    world: list[dict],
    saved_at: datetime,
    ranking_mode: str,
    paths: tuple[Path, ...] | None = None,
) -> bool:
    if len(chile) < 3 or len(world) < 2:
        return False

    payload = {
        "schema_version": 1,
        "saved_at": saved_at,
        "ranking_mode": ranking_mode,
        "chile": chile,
        "world": world,
    }
    encoded = json.dumps(
        _serialize(payload),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    wrote_any = False
    for path in paths or DEFAULT_SNAPSHOT_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            os.replace(temporary, path)
            wrote_any = True
        except OSError:
            continue

    return wrote_any


def load_news_snapshot(
    *,
    now: datetime,
    max_age_hours: float = 96.0,
    paths: tuple[Path, ...] | None = None,
) -> dict | None:
    candidates: list[dict] = []

    for path in paths or DEFAULT_SNAPSHOT_PATHS:
        payload = _read_payload(path)
        if payload:
            payload["_origin"] = "runtime"
            candidates.append(payload)

    if not candidates:
        return None

    candidates.sort(
        key=lambda payload: payload.get("saved_at") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    newest = candidates[0]
    saved_at = newest.get("saved_at")

    if saved_at is None:
        return None
    if saved_at.tzinfo is None:
        saved_at = saved_at.replace(tzinfo=timezone.utc)

    age_hours = max(
        0.0,
        (now.astimezone(timezone.utc) - saved_at.astimezone(timezone.utc)).total_seconds() / 3600,
    )
    if age_hours > max_age_hours:
        return None

    newest["age_hours"] = round(age_hours, 2)
    return newest


def load_bootstrap_snapshot(
    *,
    now: datetime,
    path: Path | None = None,
) -> dict | None:
    payload = _read_payload(path or BOOTSTRAP_PATH)
    if not payload:
        return None

    saved_at = payload.get("saved_at")
    if saved_at is None:
        saved_at = now
        payload["saved_at"] = saved_at

    if saved_at.tzinfo is None:
        saved_at = saved_at.replace(tzinfo=timezone.utc)

    payload["_origin"] = "bootstrap"
    payload["age_hours"] = max(
        0.0,
        (now.astimezone(timezone.utc) - saved_at.astimezone(timezone.utc)).total_seconds() / 3600,
    )
    return payload
