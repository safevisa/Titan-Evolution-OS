"""Google Calendar fetcher for Context Sync."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.context_sync.models import FetchedItem
from app.integrations.transport import integration_request

_CAL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def _parse_iso(val: str | None) -> datetime:
    if not val:
        return datetime.now(timezone.utc)
    try:
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _event_body(ev: dict[str, Any]) -> str:
    start = (ev.get("start") or {}).get("dateTime") or (ev.get("start") or {}).get("date") or ""
    end = (ev.get("end") or {}).get("dateTime") or (ev.get("end") or {}).get("date") or ""
    parts = [
        str(ev.get("summary") or "(no title)"),
        str(ev.get("description") or ""),
        f"{start} — {end}",
        str(ev.get("location") or ""),
    ]
    return "\n".join(p for p in parts if p.strip())


async def fetch_calendar_items(
    access_token: str,
    *,
    cursor_json: dict[str, Any],
) -> tuple[list[FetchedItem], dict[str, Any], str | None]:
    headers = {"Authorization": f"Bearer {access_token}"}
    new_cursor = dict(cursor_json)
    items: list[FetchedItem] = []
    params: dict[str, Any] = {
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 100,
    }
    sync_token = cursor_json.get("gcal_sync_token")
    if sync_token:
        params["syncToken"] = sync_token
    else:
        now = datetime.now(timezone.utc)
        params["timeMin"] = (now - timedelta(days=14)).isoformat()
        params["timeMax"] = (now + timedelta(days=14)).isoformat()

    try:
        resp = await integration_request(
            "GET",
            _CAL,
            provider="google_workspace_oauth",
            headers=headers,
            params=params,
        )
        if resp.status_code == 401:
            return [], new_cursor, "token_expired"
        if resp.status_code == 410 and sync_token:
            new_cursor.pop("gcal_sync_token", None)
            return await fetch_calendar_items(access_token, cursor_json=new_cursor)
        if resp.status_code != 200:
            return [], new_cursor, f"gcal_http_{resp.status_code}"

        data = resp.json()
        next_sync = data.get("nextSyncToken")
        if next_sync:
            new_cursor["gcal_sync_token"] = str(next_sync)

        for ev in data.get("items") or []:
            eid = str(ev.get("id") or "")
            if not eid:
                continue
            start_raw = (ev.get("start") or {}).get("dateTime") or (ev.get("start") or {}).get("date")
            items.append(
                FetchedItem(
                    external_id=eid,
                    source="gcal",
                    title=str(ev.get("summary") or "(no title)")[:500],
                    body_text=_event_body(ev)[:8000],
                    occurred_at=_parse_iso(str(start_raw) if start_raw else None),
                    url=ev.get("htmlLink"),
                    raw_meta={"status": ev.get("status")},
                )
            )

        new_cursor["gcal_last_sync_at"] = datetime.now(timezone.utc).isoformat()
        return items, new_cursor, None
    except Exception as e:
        return items, new_cursor, str(e)[:500]
