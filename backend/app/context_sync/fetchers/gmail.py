"""Gmail fetcher for Context Sync."""
from __future__ import annotations

import base64
import email.utils
from datetime import datetime, timedelta, timezone
from typing import Any

from app.context_sync.models import FetchedItem
from app.integrations.transport import integration_request

_GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me"
_MAX_BODY = 256 * 1024


def _header(headers: list[dict[str, str]], name: str) -> str:
    key = name.lower()
    for h in headers:
        if (h.get("name") or "").lower() == key:
            return str(h.get("value") or "")
    return ""


def _decode_body(data: str) -> str:
    if not data:
        return ""
    pad = "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(data + pad)
    return raw.decode("utf-8", errors="replace")


def _extract_body(payload: dict[str, Any]) -> str:
    if payload.get("body", {}).get("data"):
        return _decode_body(str(payload["body"]["data"]))
    parts = payload.get("parts") or []
    for part in parts:
        mime = (part.get("mimeType") or "").lower()
        if mime == "text/plain" and part.get("body", {}).get("data"):
            return _decode_body(str(part["body"]["data"]))
    for part in parts:
        nested = _extract_body(part)
        if nested:
            return nested
    return str(payload.get("snippet") or "")


def _parse_date(hdr: str) -> datetime:
    try:
        ts = email.utils.parsedate_to_datetime(hdr)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


async def fetch_gmail_items(
    access_token: str,
    *,
    lookback_days: int,
    cursor_json: dict[str, Any],
) -> tuple[list[FetchedItem], dict[str, Any], str | None]:
    headers = {"Authorization": f"Bearer {access_token}"}
    new_cursor = dict(cursor_json)
    items: list[FetchedItem] = []

    try:
        prof = await integration_request(
            "GET",
            f"{_GMAIL}/profile",
            provider="google_workspace_oauth",
            headers=headers,
        )
        if prof.status_code == 401:
            return [], new_cursor, "token_expired"
        prof_data = prof.json()
        history_id = prof_data.get("historyId")
        if history_id:
            new_cursor["gmail_history_id"] = str(history_id)

        start_history = cursor_json.get("gmail_history_id")
        message_ids: list[str] = []

        if start_history:
            hist = await integration_request(
                "GET",
                f"{_GMAIL}/history",
                provider="google_workspace_oauth",
                headers=headers,
                params={"startHistoryId": start_history, "historyTypes": "messageAdded"},
            )
            if hist.status_code == 401:
                return [], new_cursor, "token_expired"
            if hist.status_code == 404:
                start_history = None
            elif hist.status_code == 200:
                for block in hist.json().get("history") or []:
                    for added in block.get("messagesAdded") or []:
                        mid = (added.get("message") or {}).get("id")
                        if mid:
                            message_ids.append(str(mid))

        if not start_history or not message_ids:
            since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            q = f"after:{since.strftime('%Y/%m/%d')}"
            for label in ("INBOX", "SENT"):
                lst = await integration_request(
                    "GET",
                    f"{_GMAIL}/messages",
                    provider="google_workspace_oauth",
                    headers=headers,
                    params={"labelIds": label, "q": q, "maxResults": 50},
                )
                if lst.status_code == 401:
                    return [], new_cursor, "token_expired"
                if lst.status_code != 200:
                    continue
                for m in lst.json().get("messages") or []:
                    mid = m.get("id")
                    if mid:
                        message_ids.append(str(mid))

        seen: set[str] = set()
        for mid in message_ids:
            if mid in seen:
                continue
            seen.add(mid)
            msg = await integration_request(
                "GET",
                f"{_GMAIL}/messages/{mid}",
                provider="google_workspace_oauth",
                headers=headers,
                params={"format": "full"},
            )
            if msg.status_code != 200:
                continue
            data = msg.json()
            payload = data.get("payload") or {}
            hdrs = payload.get("headers") or []
            subject = _header(hdrs, "Subject") or "(no subject)"
            from_ = _header(hdrs, "From")
            date_hdr = _header(hdrs, "Date")
            body = _extract_body(payload)
            if len(body) > _MAX_BODY:
                body = body[:_MAX_BODY] + "\n…[truncated]…"
            body_text = f"From: {from_}\nSubject: {subject}\n\n{body}"
            items.append(
                FetchedItem(
                    external_id=str(mid),
                    source="gmail",
                    title=subject[:500],
                    body_text=body_text,
                    occurred_at=_parse_date(date_hdr),
                    url=f"https://mail.google.com/mail/u/0/#inbox/{mid}",
                    raw_meta={"label_ids": data.get("labelIds") or []},
                )
            )

        new_cursor["gmail_last_sync_at"] = datetime.now(timezone.utc).isoformat()
        return items, new_cursor, None
    except Exception as e:
        return items, new_cursor, str(e)[:500]
