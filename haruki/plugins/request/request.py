__all__ = ()

from dataclasses import dataclass, field
import scarletio
from hata import Embed, Role
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle, abort

from ...bots import Haruki
from ...constants import TMDB_IMAGE_URL, MISSING_POSTER_URL
from ..api_helpers.overseerr_helper import OverseerrHelper, MediaSummary

# Precreate Plex role
ROLE_PLEX = Role.precreate(1228676841057816707)

# Interaction custom IDs
PLEX_REQUEST_SELECT = "plex_request_select"
PLEX_REQUEST_CONFIRM = "plex_request_confirm"
PLEX_REQUEST_ABORT = "plex_request_abort"
PLEX_REQUEST_NOTIFY = "plex_request_notify"

# Per-user session state
@dataclass
class RequestSession:
    helper: OverseerrHelper
    media_type: str
    results: list[MediaSummary]
    selected_id: int | None = None

sessions: dict[int, RequestSession] = {}

# Buttons
BUTTON_CONFIRM = Button("Request", custom_id=PLEX_REQUEST_CONFIRM, style=ButtonStyle.green)
BUTTON_ABORT = Button("Abort", custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red)
BUTTON_NOTIFY = Button("Notify Me", custom_id=PLEX_REQUEST_NOTIFY, style=ButtonStyle.blue)


@dataclass
class MediaSummary:
    id: int
    title: str
    year: str
    media_type: str
    overview: str
    poster_path: str
    extra: dict = field(default_factory=dict)

    def get_requester_ids(self):
        requests = self.extra.get("mediaInfo", {}).get("requests", [])
        return [r.get("requestedBy", {}).get("id") for r in requests if r.get("requestedBy")]

def build_results_select(results: list[MediaSummary], selected_id: int | None = None) -> Select:
    options = [
        Option(str(m.id), f"{m.title} ({m.year})", default=(m.id == selected_id))
        for m in results
    ]
    return Select(options, custom_id=PLEX_REQUEST_SELECT)


def build_detail_embed(detail: MediaSummary, media_type: str, user_name: str = None, response: dict = None) -> Embed:
    embed = Embed(f"{detail.title} ({detail.year})")
    embed.description = detail.overview
    embed.add_thumbnail(detail.poster_url or MISSING_POSTER_URL)
    if response:
        total = response.get('requestedBy', {}).get('requestCount', 0) + 1
        embed.color = 0x9c5db3
        embed.add_author(f"{media_type.title()} Request Sent")
        embed.add_field("Requested By", user_name or "Unknown", True)
        embed.add_field("Request Status", "Processing", True)
        embed.add_field("Total Requests", total, True)
    return embed


async def _schedule_timeout(user_id: int, client, event):
    await scarletio.sleep(180)
    if user_id in sessions:
        try:
            await client.interaction_response_message_delete(event)
        except:
            pass
        sessions.pop(user_id, None)


@Haruki.interactions(is_global=True, name="plex-request")
async def cmd_plex_request(client, event, media_type: (["tv","movie"], "Media Type"), media: ("str", "Search Query")):
    """Start a new Plex request interaction."""
    if not event.user.has_role(ROLE_PLEX):
        return abort("You need the Plex role to use this command.")
    await client.interaction_response_message_create(event, content="🔍 Searching Overseerr...")
    scarletio.create_task(_schedule_timeout(event.user_id, client, event))

    helper = OverseerrHelper(client)
    helper.media_type = media_type
    results = await helper.search(media, media_type)
    if not results:
        return await client.interaction_response_message_edit(event, content=f"No results for '{media}'.")

    sessions[event.user_id] = RequestSession(helper, media_type, results)

    embed = Embed(f"Results for '{media}'", description="Select an item to view details.")
    select = build_results_select(results)
    return await client.interaction_response_message_edit(event, embed=embed, components=[select, [BUTTON_ABORT]])


@Haruki.interactions(custom_id=[PLEX_REQUEST_SELECT])
async def on_select_media(client, event):
    await client.interaction_component_acknowledge(event)
    session = sessions.get(event.user_id)
    if not session:
        return
    session.selected_id = int(event.values[0])

    raw = await session.helper._api_request("GET", f"{session.media_type}/{session.selected_id}", params={"language": "en"})
    detail = MediaSummary(
        id=raw.get("id"),
        title=raw.get("title") if session.media_type == "movie" else raw.get("name"),
        year=(raw.get("releaseDate") or raw.get("firstAirDate") or "")[:4],
        media_type=session.media_type,
        overview=raw.get("overview", ""),
        poster_path=raw.get("posterPath"),
        extra=raw,
    )
    detail.poster_url = TMDB_IMAGE_URL + detail.poster_path if detail.poster_path else None

    select = build_results_select(session.results, selected_id=session.selected_id)
    embed = build_detail_embed(detail, session.media_type)
    return await client.interaction_response_message_edit(event, embed=embed, components=[select, [BUTTON_CONFIRM, BUTTON_ABORT]])


@Haruki.interactions(custom_id=[PLEX_REQUEST_CONFIRM])
async def on_confirm_request(client, event):
    await client.interaction_component_acknowledge(event)
    session = sessions.get(event.user_id)
    if not session or session.selected_id is None:
        return

    raw = await session.helper._api_request("GET", f"{session.media_type}/{session.selected_id}", params={"language": "en"})
    detail = MediaSummary(
        id=raw.get("id"),
        title=raw.get("title") if session.media_type == "movie" else raw.get("name"),
        year=(raw.get("releaseDate") or raw.get("firstAirDate") or "")[:4],
        media_type=session.media_type,
        overview=raw.get("overview", ""),
        poster_path=raw.get("posterPath"),
        extra=raw,
    )
    detail.poster_url = TMDB_IMAGE_URL + detail.poster_path if detail.poster_path else None

    status = await session.helper.get_media_status(session.media_type, session.selected_id)
    if status and status in (2, 3):
        embed = Embed(f"{detail.title} ({detail.year})", color=0x66ccff)
        embed.add_author("🔄 Already Requested")
        embed.add_thumbnail(detail.poster_url or MISSING_POSTER_URL)
        embed.description = detail.overview
        return await client.interaction_response_message_edit(event, embed=embed, components=[[BUTTON_NOTIFY, BUTTON_ABORT]])
    elif status and status in (4, 5):
        sessions.pop(event.user_id, None)
        label = "⚠️ Partial Availability" if status == 4 else "✅ Media Already Available"
        color = 0xff9966 if status == 4 else 0x00cc66
        embed = Embed(f"{detail.title} ({detail.year})", color=color)
        embed.add_author(label)
        embed.add_thumbnail(detail.poster_url or MISSING_POSTER_URL)
        embed.description = detail.overview
        return await client.interaction_response_message_edit(event, embed=embed, components=None)

    overseerr_user_id = await session.helper.discord_user_to_overseerr_user(event.user_id)
    if overseerr_user_id is None:
        return await client.interaction_response_message_edit(event, content="Your Discord ID is not linked in Overseerr.")

    requester_ids = detail.get_requester_ids()
    print(f"Checking if user {overseerr_user_id} has already requested: {requester_ids}")
    already_requested = overseerr_user_id in requester_ids

    if already_requested:
        embed = Embed("ℹ️ Already Requested")
        embed.description = "You’ve already requested this media."
        return await client.interaction_response_message_edit(event, embed=embed, components=None)

    response = await session.helper.request_media(session.media_type, session.selected_id, overseerr_user_id)
    embed = build_detail_embed(detail, session.media_type, event.user.name, response)

    sessions.pop(event.user_id, None)
    return await client.interaction_response_message_edit(event, embed=embed, components=None)


@Haruki.interactions(custom_id=[PLEX_REQUEST_NOTIFY])
async def on_notify_request(client, event):
    await client.interaction_component_acknowledge(event)
    session = sessions.get(event.user_id)
    if not session or session.selected_id is None:
        return

    overseerr_user_id = await session.helper.discord_user_to_overseerr_user(event.user_id)
    if overseerr_user_id is None:
        return await client.interaction_response_message_edit(event, content="Your Discord ID is not linked in Overseerr.")

    raw = await session.helper._api_request("GET", f"{session.media_type}/{session.selected_id}", params={"language": "en"})
    detail = MediaSummary(
        id=raw.get("id"),
        title=raw.get("title") if session.media_type == "movie" else raw.get("name"),
        year=(raw.get("releaseDate") or raw.get("firstAirDate") or "")[:4],
        media_type=session.media_type,
        overview=raw.get("overview", ""),
        poster_path=raw.get("posterPath"),
        extra=raw,
    )
    requester_ids = detail.get_requester_ids()
    print(f"Checking if user {overseerr_user_id} has already requested: {requester_ids}")
    already_requested = overseerr_user_id in requester_ids

    if already_requested:
        embed = Embed("ℹ️ Already Requested")
        embed.description = "You’ve already requested this media."
        return await client.interaction_response_message_edit(event, embed=embed, components=None)

    await session.helper.request_media(session.media_type, session.selected_id, overseerr_user_id)

    embed = Embed("🔔 Notification Requested")
    embed.description = "You'll be notified when the media is available."
    sessions.pop(event.user_id, None)
    return await client.interaction_response_message_edit(event, embed=embed, components=None)


@Haruki.interactions(custom_id=[PLEX_REQUEST_ABORT])
async def on_abort(client, event):
    if event.user_id != event.message.interaction.user_id and not event.user_permissions.administrator:
        return
    await client.interaction_component_acknowledge(event)
    sessions.pop(event.user_id, None)
    await client.interaction_response_message_delete(event)
