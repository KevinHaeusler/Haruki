__all__ = ()

from scarletio import sleep
from dataclasses import dataclass
from hata import Embed
from icecream import ic
from hata.ext.slash import Button, ButtonStyle, abort
from datetime import datetime
from ...bots import Kiruha
from ..api_helpers.overseerr_helper import OverseerrHelper

@dataclass
class RequestSession:
    embeds: list[Embed]
    page: int = 0

_req_sessions: dict[int, RequestSession] = {}

REQ_PAGE_PREV = "req_prev"
REQ_PAGE_NEXT = "req_next"
REQ_ABORT = "req_abort"

avail_map = {1: "❔", 2: "⌛", 3: "🔄", 4: "⚠️", 5: "✅", 6: "❌"}

@Kiruha.interactions(is_global=True, name="get-requests")
async def get_requests(
    client,
    event,
    include_finished: ("bool", "Include finished/completed requests") = False,
    user: ("user", "Discord user to query; defaults to you") = None,
):
    await client.interaction_response_message_create(
        event,
        content="🔍 Retrieving Overseerr requests...\n\n**########### Legend ###########**\n✅ = Available, ❔ = Unknown, ⌛ = Pending, 🔄 = Processing, ⚠️ = Partial, ❌ = Deleted \n\nMedia that is 🔄 = Processing usually needs to be downloaded manually, try /plex-fix-missing\nMedia that is ⚠️ = Partial usually means episodes are missing (can be running shows with future episodes)\n"
    )
    target_discord_id = user.id if user else event.user_id
    helper = OverseerrHelper(client)
    overseerr_id = await helper.discord_user_to_overseerr_user(target_discord_id)
    if overseerr_id is None:
        return await client.interaction_response_message_edit(
            event,
            content=f"❌ No Overseerr account linked for <@{target_discord_id}>."
        )

    requests_list, skip, take = [], 0, 100
    while True:
        resp = await helper._api_request(
            "GET", f"user/{overseerr_id}/requests", params={"take": take, "skip": skip}
        )
        batch = resp.get("results", [])
        if not batch:
            break
        requests_list.extend(batch)
        if len(batch) < take:
            break
        skip += take

    if not include_finished:
        requests_list = [r for r in requests_list if (r.get("media") or {}).get("status") != 5]

    if not requests_list:
        msg = (
            f"<@{target_discord_id}> has no requests."
            if include_finished else f"<@{target_discord_id}> has no open requests."
        )
        return await client.interaction_response_message_edit(event, content=msg)

    lines = []
    lines.append(f"**Status — Title — Requested Date**")
   
    for req in requests_list:
        media = req.get("media") or {}
        raw_type = (req.get("type") or media.get("mediaType") or "").lower()
        media_id = media.get("tmdbId")
        title, year = "Unknown", ""
        info = await fetch_media_info_with_retry(helper, raw_type, media_id)
        if info:
            title, year = info.title, info.year
        else:
            title = req.get("media", {}).get("title") or req.get("title") or "Unknown"
            year = req.get("media", {}).get("releaseDate", "")[:4] or ""

        created_raw = req.get("createdAt")
        if created_raw:
            try:
                created = datetime.strptime(created_raw, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d.%m.%y")
            except ValueError:
                created = "??.??.??"
        else:
            created = "??.??.??"
        availability = avail_map.get(media.get("status", 0), str(media.get("status")))
        lines.append(f"{availability} — **{title} ({year})** — {created}")
    CHUNK = 20
    target_user = user or event.user
    display_name = getattr(target_user, "display_name", None) or target_user.username
    embeds = []

    for i in range(0, len(lines), CHUNK):
        chunk = lines[i:i+CHUNK]
        description = "\n".join(chunk)
        embeds.append(
            Embed(
                title=f"Overseerr Requests for {display_name}",
                description=description
            )
        )

    session = RequestSession(embeds=embeds)
    _req_sessions[event.user_id] = session

    btn_prev = Button("Prev", custom_id=REQ_PAGE_PREV, style=ButtonStyle.gray)
    btn_next = Button("Next", custom_id=REQ_PAGE_NEXT, style=ButtonStyle.gray)
    btn_abort = Button("Abort", custom_id=REQ_ABORT, style=ButtonStyle.red)

    return await client.interaction_response_message_edit(
        event,
        embed=session.embeds[session.page],
        components=[[btn_prev, btn_next, btn_abort]]
    )

@Kiruha.interactions(custom_id=[REQ_PAGE_PREV, REQ_PAGE_NEXT, REQ_ABORT])
async def handle_request_buttons(client, event):
    session = _req_sessions.get(event.user_id)
    if not session:
        return abort("Session expired or not found.")

    if event.custom_id == REQ_ABORT:
        del _req_sessions[event.user_id]
        return await client.interaction_response_message_delete(event)

    if event.custom_id == REQ_PAGE_NEXT:
        session.page = min(session.page + 1, len(session.embeds) - 1)
    elif event.custom_id == REQ_PAGE_PREV:
        session.page = max(session.page - 1, 0)

    await client.interaction_component_acknowledge(event)
    return await client.interaction_response_message_edit(
        event,
        embed=session.embeds[session.page]
    )

@Kiruha.interactions(custom_id=[REQ_ABORT])
async def abort_overseerr_requests(client, event):
    if event.user_id != event.message.interaction.user_id and not event.user_permissions.administrator:
        return
    await client.interaction_component_acknowledge(event)
    _req_sessions.pop(event.user_id, None)
    await client.interaction_response_message_edit(
        event,
        content="❌ Request aborted.",
        embed=None,
        components=None
    )

async def fetch_media_info_with_retry(helper, raw_type, media_id, retries=3, delay=2.0):
    for attempt in range(retries):
        try:
            info = await helper.get_media_info(raw_type, media_id)
            if info and hasattr(info, "title"):
                return info
        except Exception as e:
            print(f"[Attempt {attempt+1}] Failed to get media info: {e}")
        await sleep(delay)
    return None