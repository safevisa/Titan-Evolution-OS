"""Dispatch chat/social capabilities using tenant integration_connections."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.connection_tokens import get_connection_secret
from app.integrations.connections_repo import decrypt_row_secret, get_connection_row
from app.integrations.providers import (
    PROVIDER_DISCORD_WEBHOOK,
    PROVIDER_FACEBOOK_GRAPH_OAUTH,
    PROVIDER_FEISHU_WEBHOOK,
    PROVIDER_GOOGLE_YOUTUBE_OAUTH,
    PROVIDER_LINKEDIN_OAUTH,
    PROVIDER_REDDIT_OAUTH,
    PROVIDER_SLACK_INCOMING_WEBHOOK,
    PROVIDER_SLACK_OAUTH,
    PROVIDER_TELEGRAM_BOT,
    PROVIDER_TWITTER_OAUTH,
    PROVIDER_WECHAT_MP_CREDENTIALS,
    PROVIDER_WECHAT_WORK_WEBHOOK,
    PROVIDER_WEIBO_OAUTH,
    PROVIDER_WHATSAPP_CLOUD,
)
from app.integrations.social_more import (
    facebook_page_feed_post,
    instagram_publish_single_image,
    reddit_submit_post,
    telegram_send_message,
    wechat_mp_template_send,
    weibo_post_update,
    whatsapp_send_text_message,
    youtube_comment_thread_insert,
)
from app.integrations.social_send import (
    post_discord_webhook,
    post_feishu_text_webhook,
    post_linkedin_text_post,
    post_slack_chat_message,
    post_slack_incoming_webhook,
    post_twitter_create_tweet,
    post_wechat_work_markdown,
)
from app.integrations.token_vault import IntegrationVaultError


async def invoke_external_capability(
    capability_id: str,
    params: dict[str, Any],
    session: AsyncSession,
    tenant_id: UUID,
) -> dict[str, Any]:
    try:
        if capability_id == "discord_post_message":
            row = await get_connection_row(session, tenant_id, PROVIDER_DISCORD_WEBHOOK)
            if not row:
                return {"ok": False, "error": "missing_discord_webhook_connection"}
            url = decrypt_row_secret(row).get("webhook_url")
            if not url:
                return {"ok": False, "error": "invalid_discord_connection_payload"}
            content = str(params.get("content", params.get("text", "")))
            data = await post_discord_webhook(url, content)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "feishu_lark_notify":
            row = await get_connection_row(session, tenant_id, PROVIDER_FEISHU_WEBHOOK)
            if not row:
                return {"ok": False, "error": "missing_feishu_webhook_connection"}
            url = decrypt_row_secret(row).get("webhook_url")
            if not url:
                return {"ok": False, "error": "invalid_feishu_connection_payload"}
            text = str(params.get("text", params.get("content", "")))
            data = await post_feishu_text_webhook(url, text)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "wechat_work_notify":
            row = await get_connection_row(session, tenant_id, PROVIDER_WECHAT_WORK_WEBHOOK)
            if not row:
                return {"ok": False, "error": "missing_wechat_work_webhook_connection"}
            url = decrypt_row_secret(row).get("webhook_url")
            if not url:
                return {"ok": False, "error": "invalid_wechat_work_connection_payload"}
            md = str(params.get("markdown", params.get("text", params.get("content", ""))))
            data = await post_wechat_work_markdown(url, md)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "slack_post_message":
            row_oauth = await get_connection_row(session, tenant_id, PROVIDER_SLACK_OAUTH)
            if row_oauth:
                sec = await get_connection_secret(session, tenant_id, PROVIDER_SLACK_OAUTH) or {}
                token = str(sec.get("access_token", ""))
                if not token:
                    return {"ok": False, "error": "invalid_slack_oauth_token"}
                channel = str(params.get("channel", "")).strip()
                text = str(params.get("text", params.get("content", "")))
                if not channel:
                    return {"ok": False, "error": "slack_post_requires_channel"}
                data = await post_slack_chat_message(token, channel, text)
                return {"ok": bool(data.get("ok")), "data": data}

            row_wh = await get_connection_row(session, tenant_id, PROVIDER_SLACK_INCOMING_WEBHOOK)
            if row_wh:
                url = decrypt_row_secret(row_wh).get("webhook_url")
                if not url:
                    return {"ok": False, "error": "invalid_slack_webhook_payload"}
                text = str(params.get("text", params.get("content", "")))
                data = await post_slack_incoming_webhook(url, text)
                return {"ok": bool(data.get("ok")), "data": data}

            return {"ok": False, "error": "missing_slack_connection"}

        if capability_id == "twitter_x_post":
            row = await get_connection_row(session, tenant_id, PROVIDER_TWITTER_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_twitter_oauth_connection"}
            sec = await get_connection_secret(session, tenant_id, PROVIDER_TWITTER_OAUTH) or {}
            token = str(sec.get("access_token", ""))
            if not token:
                return {"ok": False, "error": "invalid_twitter_token"}
            text = str(params.get("text", params.get("content", "")))
            data = await post_twitter_create_tweet(token, text)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "linkedin_share":
            row = await get_connection_row(session, tenant_id, PROVIDER_LINKEDIN_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_linkedin_oauth_connection"}
            sec = await get_connection_secret(session, tenant_id, PROVIDER_LINKEDIN_OAUTH) or {}
            token = str(sec.get("access_token", ""))
            meta = row.meta if isinstance(row.meta, dict) else {}
            author = str(meta.get("linkedin_person_urn", "")).strip()
            if not token or not author:
                return {"ok": False, "error": "linkedin_missing_person_urn_reauthorize"}
            text = str(params.get("text", params.get("content", "")))
            data = await post_linkedin_text_post(token, author, text)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "telegram_send_message":
            row = await get_connection_row(session, tenant_id, PROVIDER_TELEGRAM_BOT)
            if not row:
                return {"ok": False, "error": "missing_telegram_bot_connection"}
            sec = decrypt_row_secret(row)
            token = str(sec.get("bot_token", ""))
            if not token:
                return {"ok": False, "error": "invalid_telegram_payload"}
            chat_id = str(params.get("chat_id", "")).strip()
            text = str(params.get("text", params.get("message", params.get("content", ""))))
            if not chat_id:
                return {"ok": False, "error": "telegram_requires_chat_id"}
            data = await telegram_send_message(token, chat_id, text)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "whatsapp_cloud_text":
            row = await get_connection_row(session, tenant_id, PROVIDER_WHATSAPP_CLOUD)
            if not row:
                return {"ok": False, "error": "missing_whatsapp_cloud_connection"}
            sec = decrypt_row_secret(row)
            at = str(sec.get("access_token", ""))
            pn = str(sec.get("phone_number_id", ""))
            if not at or not pn:
                return {"ok": False, "error": "invalid_whatsapp_payload"}
            to = str(params.get("to", params.get("phone", ""))).strip()
            text = str(params.get("text", params.get("content", "")))
            if not to:
                return {"ok": False, "error": "whatsapp_requires_to"}
            data = await whatsapp_send_text_message(at, pn, to, text)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "facebook_page_feed_post":
            row = await get_connection_row(session, tenant_id, PROVIDER_FACEBOOK_GRAPH_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_facebook_oauth_connection"}
            sec = decrypt_row_secret(row)
            page_token = str(sec.get("page_access_token", ""))
            meta = row.meta if isinstance(row.meta, dict) else {}
            page_id = str(meta.get("facebook_page_id", "")).strip()
            if not page_token or not page_id:
                return {"ok": False, "error": "facebook_missing_page_token_or_id"}
            message = str(params.get("message", params.get("text", params.get("content", ""))))
            link = params.get("link")
            link_s = str(link).strip() if link else None
            data = await facebook_page_feed_post(page_token, page_id, message, link_s)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "instagram_publish_image":
            row = await get_connection_row(session, tenant_id, PROVIDER_FACEBOOK_GRAPH_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_facebook_oauth_connection"}
            sec = decrypt_row_secret(row)
            page_token = str(sec.get("page_access_token", ""))
            meta = row.meta if isinstance(row.meta, dict) else {}
            ig_id = str(meta.get("instagram_business_account_id", "")).strip()
            if not page_token or not ig_id:
                return {"ok": False, "error": "instagram_requires_linked_business_account"}
            image_url = str(params.get("image_url", "")).strip()
            caption = str(params.get("caption", params.get("text", "")))
            if not image_url:
                return {"ok": False, "error": "instagram_requires_image_url"}
            data = await instagram_publish_single_image(page_token, ig_id, image_url, caption)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "weibo_status_post":
            row = await get_connection_row(session, tenant_id, PROVIDER_WEIBO_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_weibo_oauth_connection"}
            sec = decrypt_row_secret(row)
            token = str(sec.get("access_token", ""))
            if not token:
                return {"ok": False, "error": "invalid_weibo_token"}
            status = str(params.get("status", params.get("text", params.get("content", ""))))
            data = await weibo_post_update(token, status)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "reddit_submit_post":
            row = await get_connection_row(session, tenant_id, PROVIDER_REDDIT_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_reddit_oauth_connection"}
            sec = await get_connection_secret(session, tenant_id, PROVIDER_REDDIT_OAUTH) or {}
            token = str(sec.get("access_token", ""))
            if not token:
                return {"ok": False, "error": "invalid_reddit_token"}
            sub = str(params.get("subreddit", "")).strip()
            title = str(params.get("title", "")).strip()
            kind = str(params.get("kind", "self")).strip().lower()
            text = params.get("text")
            text_s = str(text) if text is not None else None
            url = params.get("url")
            url_s = str(url).strip() if url else None
            if not sub or not title:
                return {"ok": False, "error": "reddit_requires_subreddit_and_title"}
            data = await reddit_submit_post(token, sub, title, kind, text_s, url_s)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "youtube_top_comment":
            row = await get_connection_row(session, tenant_id, PROVIDER_GOOGLE_YOUTUBE_OAUTH)
            if not row:
                return {"ok": False, "error": "missing_youtube_oauth_connection"}
            sec = await get_connection_secret(session, tenant_id, PROVIDER_GOOGLE_YOUTUBE_OAUTH) or {}
            token = str(sec.get("access_token", ""))
            meta = row.meta if isinstance(row.meta, dict) else {}
            channel_id = str(meta.get("youtube_channel_id", "")).strip()
            if not token or not channel_id:
                return {"ok": False, "error": "youtube_missing_token_or_channel_reauthorize"}
            video_id = str(params.get("video_id", "")).strip()
            text = str(params.get("text", params.get("comment", params.get("content", ""))))
            if not video_id:
                return {"ok": False, "error": "youtube_requires_video_id"}
            data = await youtube_comment_thread_insert(token, channel_id, video_id, text)
            return {"ok": bool(data.get("ok")), "data": data}

        if capability_id == "wechat_mp_template_message":
            row = await get_connection_row(session, tenant_id, PROVIDER_WECHAT_MP_CREDENTIALS)
            if not row:
                return {"ok": False, "error": "missing_wechat_mp_credentials"}
            sec = decrypt_row_secret(row)
            app_id = str(sec.get("app_id", ""))
            app_secret = str(sec.get("app_secret", ""))
            if not app_id or not app_secret:
                return {"ok": False, "error": "invalid_wechat_mp_payload"}
            touser = str(params.get("touser", params.get("openid", ""))).strip()
            template_id = str(params.get("template_id", "")).strip()
            raw_td = params.get("template_data", params.get("data", {}))
            if isinstance(raw_td, str):
                try:
                    template_data = json.loads(raw_td)
                except json.JSONDecodeError:
                    return {"ok": False, "error": "wechat_mp_invalid_template_data_json"}
            elif isinstance(raw_td, dict):
                template_data = raw_td
            else:
                return {"ok": False, "error": "wechat_mp_template_data_must_be_object"}
            if not touser or not template_id:
                return {"ok": False, "error": "wechat_mp_requires_touser_and_template_id"}
            data = await wechat_mp_template_send(app_id, app_secret, touser, template_id, template_data)
            return {"ok": bool(data.get("ok")), "data": data}

        return {"ok": False, "error": "capability_not_routed"}
    except IntegrationVaultError as e:
        return {"ok": False, "error": "vault_error", "message": str(e)}
