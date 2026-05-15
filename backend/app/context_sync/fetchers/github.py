"""GitHub issues/PRs fetcher for Context Sync."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.context_sync.models import FetchedItem
from app.integrations.transport import integration_request

_GH = "https://api.github.com"
_MAX_REPOS = 30
_MAX_BODY = 8000


def _parse_github_dt(val: str | None) -> datetime:
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


async def fetch_github_items(
    access_token: str,
    *,
    cursor_json: dict[str, Any],
) -> tuple[list[FetchedItem], dict[str, Any], str | None]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    new_cursor = dict(cursor_json)
    items: list[FetchedItem] = []

    since_raw = cursor_json.get("github_since")
    if since_raw:
        since = _parse_github_dt(str(since_raw))
    else:
        since = datetime.now(timezone.utc) - timedelta(days=30)
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        repos_resp = await integration_request(
            "GET",
            f"{_GH}/user/repos",
            provider="github_oauth",
            headers=headers,
            params={"per_page": 100, "sort": "pushed", "affiliation": "owner,collaborator,organization_member"},
        )
        if repos_resp.status_code == 401:
            return [], new_cursor, "token_expired"
        if repos_resp.status_code != 200:
            return [], new_cursor, f"github_http_{repos_resp.status_code}"

        repos = (repos_resp.json() or [])[:_MAX_REPOS]
        latest_updated = since

        for repo in repos:
            full_name = str(repo.get("full_name") or "")
            if not full_name:
                continue
            owner, name = full_name.split("/", 1)
            for kind, path in (("issue", "issues"), ("pr", "pulls")):
                page_resp = await integration_request(
                    "GET",
                    f"{_GH}/repos/{owner}/{name}/{path}",
                    provider="github_oauth",
                    headers=headers,
                    params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 30},
                )
                if page_resp.status_code != 200:
                    continue
                for it in page_resp.json() or []:
                    updated = _parse_github_dt(str(it.get("updated_at") or it.get("created_at")))
                    if updated < since:
                        continue
                    if updated > latest_updated:
                        latest_updated = updated
                    num = it.get("number")
                    title = str(it.get("title") or "(no title)")
                    body = str(it.get("body") or "")[:_MAX_BODY]
                    body_text = f"Repo: {full_name}\nType: {kind}\nTitle: {title}\n\n{body}"
                    ext = f"{full_name}#{kind}#{num}"
                    items.append(
                        FetchedItem(
                            external_id=ext,
                            source="github",
                            title=title[:500],
                            body_text=body_text,
                            occurred_at=updated,
                            url=it.get("html_url"),
                            raw_meta={"repo": full_name, "kind": kind, "number": num},
                        )
                    )

        new_cursor["github_since"] = latest_updated.strftime("%Y-%m-%dT%H:%M:%SZ")
        new_cursor["github_last_sync_at"] = datetime.now(timezone.utc).isoformat()
        return items, new_cursor, None
    except Exception as e:
        return items, new_cursor, str(e)[:500]
