from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import re
import unicodedata
from typing import Iterable
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
import requests


CHILE_TZ = ZoneInfo("America/Santiago")
SNAPSHOT_PATHS = (
    Path(__file__).resolve().parents[1] / ".cache" / "market_snapshot.json",
    Path("/tmp/radar_minero_market_snapshot.json"),
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1 "
        "RadarMinero/0.5"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9",
    "Cache-Control": "no-cache",
}

MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


@dataclass(frozen=True)
class SeriesSpec:
    key: str
    label: str
    unit: str
    decimals: int
    urls: tuple[str, ...]


SERIES = (
    SeriesSpec(
        key="dollar",
        label="DÓLAR OBS.",
        unit="clp",
        decimals=2,
        urls=(
            "https://si3.bcentral.cl/indicadoressiete/secure/Serie.aspx?gcode=PRE_TCO&param=RABmAFYAWQB3AGYAaQBuAEkALQAzADUAbgBNAGgAaAAkADUAVwBQAC4AbQBYADAARwBOAGUAYwBjACMAQQBaAHAARgBhAGcAUABTAGUAdwA1ADQAMQA0AE0AawBLAF8AdQBDACQASABzAG0AXwA2AHQAawBvAFcAZwBKAEwAegBzAF8AbgBMAHIAYgBDAC4ARQA3AFUAVwB4AFIAWQBhAEEAOABkAHkAZwAxAEEARAA%3D",
            "https://si3.bcentral.cl/Bdemovil/BDE/Series/MOV_ID_TC1",
        ),
    ),
    SeriesSpec(
        key="copper",
        label="COBRE",
        unit="usd_lb",
        decimals=2,
        urls=(
            "https://si3.bcentral.cl/indicadoressiete/secure/Serie.aspx?gcode=LIBRA_COBRE&param=cgBnAE8AOQBlAGcAIwBiAFUALQBsAEcAYgBOAEkASQBCAEcAegBFAFkAeABkADgASAA2AG8AdgB2AFMAUgBYADIAQwBzAEEAMQBJAG8ATwBzAEgATABGAE4AagB1AFcAYgB2AFAAZwBhADIAbABWAHcAXwBXAGgATAAkAFIAVAB1AEIAbAB3AFoAdQBRAFgAZwA5AHgAdgAwACQATwBZADcAMwAuAGIARwBFAFIASwAuAHQA",
            "https://si3.bcentral.cl/bdemovil/BDE/Series/MOV_ID_PR1",
        ),
    ),
    SeriesSpec(
        key="gold",
        label="ORO",
        unit="usd_oz",
        decimals=2,
        urls=(
            "https://si3.bcentral.cl/indicadoressiete/secure/Serie.aspx?gcode=ONZA_ORO&param=SwBqAGEAMAAyAGoAbwBjAFIALQBGAEoAYwBYAEEAQQB4AEoARQBXAHEAJABOADkAXwBkAGkAYgBiADEASQBNAHcAbABPAGgAIwBBAGkAYQBPAF8AUwAzAFgAZgByAGEATwB5AGYAQgBwADMAeABUAEoAUQBqADEAegBBAF8ASwAkADMAVABiAEsAdABaAGYAWQBtAGMAcQB6AFYALgA5AHMAUgBuADUAUABBAEwAUgByAA%3D%3D",
            "https://si3.bcentral.cl/Bdemovil/BDE/Series/MOV_ID_PR2",
        ),
    ),
)


def _normalize(value: str) -> str:
    text = " ".join((value or "").split()).lower()
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def _parse_chilean_number(value: str) -> float | None:
    cleaned = (value or "").strip()
    if not cleaned or cleaned.upper() in {"NA", "ND", "N.D.", "-"}:
        return None

    cleaned = re.sub(r"[^\d,.\-]", "", cleaned)
    if not cleaned:
        return None

    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        # A dot in these official tables can be a decimal separator only when
        # there is a single dot and at most four digits after it.
        if cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        elif cleaned.count(".") == 1:
            left, right = cleaned.split(".", 1)
            if len(right) == 3 and len(left) >= 1:
                cleaned = left + right

    try:
        return float(cleaned)
    except ValueError:
        return None


def _download(url: str, timeout: int = 14) -> str:
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=(3.5, timeout),
                allow_redirects=True,
            )
            if response.status_code in {408, 425, 429, 500, 502, 503, 504} and attempt < 2:
                import time
                time.sleep(0.35 * (2**attempt))
                continue
            response.raise_for_status()
            return response.text
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_error = exc
            if attempt < 2:
                import time
                time.sleep(0.35 * (2**attempt))

    if last_error:
        raise last_error
    raise RuntimeError("Banco Central no respondió.")


def _extract_year(soup: BeautifulSoup) -> int:
    selected = soup.select_one("select option[selected]")
    if selected:
        match = re.search(r"\b(20\d{2})\b", selected.get_text(" ", strip=True))
        if match:
            return int(match.group(1))

    text = soup.get_text(" ", strip=True)
    match = re.search(r"\bAño\s+(20\d{2})\b", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))

    return datetime.now(CHILE_TZ).year


def _expanded_cells(row) -> list[str]:
    values: list[str] = []

    for cell in row.find_all(["th", "td"], recursive=False):
        text = " ".join(cell.get_text(" ", strip=True).split())
        try:
            colspan = max(1, int(cell.get("colspan", 1)))
        except (TypeError, ValueError):
            colspan = 1
        values.append(text)
        values.extend([""] * (colspan - 1))

    return values


def parse_year_grid(html: str) -> list[tuple[date, float]]:
    """Parse Banco Central's day × month annual matrix."""
    soup = BeautifulSoup(html, "html.parser")
    year = _extract_year(soup)
    observations: list[tuple[date, float]] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        header_index: int | None = None
        month_columns: dict[int, int] = {}

        for index, row in enumerate(rows):
            cells = _expanded_cells(row)
            normalized = [_normalize(cell) for cell in cells]

            if not normalized or normalized[0] not in {"dia", "día"}:
                continue

            for column, cell in enumerate(normalized[1:], start=1):
                month = MONTHS.get(cell)
                if month:
                    month_columns[column] = month

            if len(month_columns) >= 3:
                header_index = index
                break

        if header_index is None:
            continue

        for row in rows[header_index + 1 :]:
            cells = _expanded_cells(row)
            if not cells:
                continue

            day_match = re.fullmatch(r"\s*(\d{1,2})\s*", cells[0])
            if not day_match:
                continue

            day = int(day_match.group(1))
            for column, month in month_columns.items():
                if column >= len(cells):
                    continue

                value = _parse_chilean_number(cells[column])
                if value is None:
                    continue

                try:
                    observation_date = date(year, month, day)
                except ValueError:
                    continue

                observations.append((observation_date, value))

        if observations:
            break

    # Defensive deduplication in case the page contains a desktop and mobile table.
    unique = {observation_date: value for observation_date, value in observations}
    return sorted(unique.items(), key=lambda pair: pair[0])


def _latest_two(
    observations: Iterable[tuple[date, float]],
    *,
    today: date,
) -> list[tuple[date, float]]:
    valid = [
        (observation_date, value)
        for observation_date, value in observations
        if observation_date <= today
    ]
    valid.sort(key=lambda pair: pair[0], reverse=True)
    return valid[:2]


def _fetch_series(spec: SeriesSpec, today: date) -> dict:
    errors: list[str] = []

    for url in spec.urls:
        try:
            html = _download(url)
            latest = _latest_two(parse_year_grid(html), today=today)
            if not latest:
                raise ValueError("La tabla oficial no entregó observaciones.")

            current_date, current_value = latest[0]
            previous_date = latest[1][0] if len(latest) > 1 else None
            previous_value = latest[1][1] if len(latest) > 1 else None

            return {
                "key": spec.key,
                "label": spec.label,
                "unit": spec.unit,
                "decimals": spec.decimals,
                "current_date": current_date.isoformat(),
                "current_value": current_value,
                "previous_date": previous_date.isoformat() if previous_date else None,
                "previous_value": previous_value,
                "source_url": url,
            }
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {str(exc)[:90]}")

    raise RuntimeError(" | ".join(errors) or "Fuente no disponible.")


def _format_number(value: float, decimals: int = 2) -> str:
    standard = f"{value:,.{decimals}f}"
    return standard.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_value(series: dict) -> str:
    value = float(series["current_value"])
    decimals = int(series.get("decimals", 2))
    unit = series.get("unit")

    if unit == "clp":
        return f"${_format_number(value, decimals)}"
    if unit == "usd_lb":
        return f"US$ {_format_number(value, decimals)}/lb"
    if unit == "usd_oz":
        return f"US$ {_format_number(value, decimals)}/oz"
    return _format_number(value, decimals)


def _format_delta(series: dict) -> tuple[str, str]:
    current = float(series["current_value"])
    previous = series.get("previous_value")

    if previous in (None, 0):
        return "s/d", "flat"

    change = (current / float(previous) - 1.0) * 100.0
    direction = "up" if change > 0.0005 else "down" if change < -0.0005 else "flat"
    sign = "+" if change > 0 else ""
    label = f"{sign}{change:.2f}%".replace(".", ",")
    return label, direction


def _series_to_item(series: dict) -> dict:
    delta, direction = _format_delta(series)
    return {
        "key": series["key"],
        "label": series["label"],
        "value": _format_value(series),
        "delta": delta,
        "direction": direction,
        "data_date": series["current_date"],
        "source_url": series.get("source_url", ""),
    }


def _save_snapshot(payload: dict) -> None:
    encoded = json.dumps(payload, ensure_ascii=False)

    for path in SNAPSHOT_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            temporary.replace(path)
        except OSError:
            continue


def _load_snapshot() -> dict | None:
    candidates: list[dict] = []

    for path in SNAPSHOT_PATHS:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if isinstance(payload, dict) and payload.get("items"):
            candidates.append(payload)

    if not candidates:
        return None

    candidates.sort(
        key=lambda payload: str(payload.get("fetched_at", "")),
        reverse=True,
    )
    return candidates[0]


def fetch_official_markets() -> dict:
    now = datetime.now(CHILE_TZ)
    today = now.date()
    series_results: list[dict] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {
            executor.submit(_fetch_series, spec, today): spec.label
            for spec in SERIES
        }

        for future in as_completed(future_map):
            label = future_map[future]
            try:
                series_results.append(future.result())
            except Exception as exc:
                errors.append(f"{label}: {type(exc).__name__}")

    order = {"dollar": 0, "copper": 1, "gold": 2}
    series_results.sort(key=lambda item: order.get(item["key"], 99))
    items = [_series_to_item(series) for series in series_results]

    data_dates = [
        date.fromisoformat(item["data_date"])
        for item in items
        if item.get("data_date")
    ]
    data_date = max(data_dates).isoformat() if data_dates else None

    if items:
        payload = {
            "items": items,
            "data_date": data_date,
            "source_label": "Banco Central de Chile",
            "status": "official" if len(items) == len(SERIES) else "partial",
            "errors": errors,
            "fetched_at": now.isoformat(),
        }
        _save_snapshot(payload)
        return payload

    snapshot = _load_snapshot()
    if snapshot:
        snapshot["status"] = "snapshot"
        snapshot["errors"] = errors
        snapshot["source_label"] = "Banco Central de Chile · último dato guardado"
        return snapshot

    return {
        "items": [],
        "data_date": None,
        "source_label": "Banco Central de Chile",
        "status": "unavailable",
        "errors": errors,
        "fetched_at": now.isoformat(),
    }
