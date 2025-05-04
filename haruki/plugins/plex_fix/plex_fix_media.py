__all__ = ()

import scarletio
from dataclasses import dataclass
from hata import Embed, Role
from hata.ext.slash import Button, ButtonStyle, Select, Option, abort

from ...bots import Kiruha
from ..api_helpers.sonarr_api import get_from_sonarr_api, post_to_sonarr_api, put_to_sonarr_api

# Precreate Plex role
ROLE_PLEX = Role.precreate(1228676841057816707)

# Interaction custom IDs
PLEX_FIX_MEDIA_SELECT = "plex_fix_media_select_media"
PLEX_FIX_MEDIA_ABORT = "plex_fix_media_abort"
PLEX_FIX_MEDIA_SELECT_PROFILE = "plex_fix_media_select_profile"
PLEX_FIX_MEDIA_SELECT_TYPE = "plex_fix_media_select_type"
PLEX_FIX_MEDIA_RESYNC_MISSING = "plex_fix_media_resync_missing"

# Per-user session state
@dataclass
class FixSession:
    series_list: list
    selected_series: dict | None = None

_sessions: dict[int, FixSession] = {}

# Buttons
BUTTON_ABORT = Button("Abort", custom_id=PLEX_FIX_MEDIA_ABORT, style=ButtonStyle.red)

# Helper: schedule auto-timeout for 5 minutes
def _schedule_timeout(user_id: int, client, event):
    async def _timeout():
        await scarletio.sleep(180)
        session = _sessions.pop(user_id, None)
        if session is not None:
            try:
                await client.interaction_response_message_delete(event)
            except:
                pass
    scarletio.create_task(_timeout())

@Kiruha.interactions(is_global=True, name="plex-fix-media")
async def initiate_plex_fix_media(client, event,
                                  media_type: (["tv","movie"], "Pick Media Type"),
                                  media: ("str", "Enter the media to search for")):
    """Start a fix-media session for Sonarr (Plex role required)."""
    # Role restriction
    if not event.user.has_role(ROLE_PLEX):
        return abort("You need the Plex role to use this command.")
    # Initial response and timeout
    await client.interaction_response_message_create(event, content="🔍 Searching Sonarr...")
    _schedule_timeout(event.user_id, client, event)

    if media_type != "tv":
        return await client.interaction_response_message_edit(event, content="Currently only TV search is supported.")

    # Fetch and filter series
    all_series = await get_from_sonarr_api(client, "series")
    matches = [s for s in all_series if media.lower() in (s.get("title") or "").lower()]
    if not matches:
        return await client.interaction_response_message_edit(event, content=f"No results found for '{media}'.")

    # Store session
    _sessions[event.user_id] = FixSession(series_list=matches)

    # Build select options
    options = [Option(str(s["id"]), f"{s.get('title')} ({s.get('year','Unknown')})") for s in matches]
    select = Select(options, custom_id=PLEX_FIX_MEDIA_SELECT)
    embed = Embed('Select Media', description='Choose the series to fix')
    return await client.interaction_response_message_edit(event, embed=embed, components=[select, [BUTTON_ABORT]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT])
async def handle_media_selection(client, event):
    """Handle the selection of a series."""
    await client.interaction_component_acknowledge(event)
    session = _sessions.get(event.user_id)
    if session is None:
        return
    series_id = int(event.values[0])
    # Find and set selected series
    session.selected_series = next((s for s in session.series_list if s.get("id") == series_id), None)
    if session.selected_series is None:
        return
    # Show overview
    await send_series_overview(client, event, session.selected_series)

async def send_series_overview(client, event, series):
    files = await get_from_sonarr_api(client, f"episodefile?seriesId={series['id']}")
    disk_size = sum(f.get('size', 0) for f in files)
    size_gb = disk_size / (1024 ** 3)

    profiles = await get_from_sonarr_api(client, "qualityprofile")
    profile_map = {p['id']: p['name'] for p in profiles}

    embed = Embed(series.get('title'), description='Media Details')
    embed.add_field('Profile', profile_map.get(series.get('qualityProfileId'), 'Unknown'), inline=True)
    embed.add_field('Type', series.get('seriesType', 'Unknown'), inline=True)
    embed.add_field('Disk Path', series.get('path', 'Unknown'), inline=False)
    embed.add_field('Disk Size', f"{size_gb:.2f} GB", inline=True)
    embed.add_field('Status', series.get('status', 'Unknown'), inline=True)

    btns = [
        Button('Fix Profile', custom_id=PLEX_FIX_MEDIA_SELECT_PROFILE, style=ButtonStyle.green),
        Button('Fix Type', custom_id=PLEX_FIX_MEDIA_SELECT_TYPE, style=ButtonStyle.green),
        Button('Search Missing', custom_id=PLEX_FIX_MEDIA_RESYNC_MISSING, style=ButtonStyle.green),
        BUTTON_ABORT,
    ]
    return await client.interaction_response_message_edit(event, embed=embed, components=[btns])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_PROFILE])
async def handle_fix_profile(client, event):
    """Allow changing the quality profile."""
    await client.interaction_component_acknowledge(event)
    session = _sessions.get(event.user_id)
    if not session or session.selected_series is None:
        return await client.interaction_response_message_edit(event, content="No series selected.")

    profiles = await get_from_sonarr_api(client, "qualityprofile")
    current = session.selected_series.get('qualityProfileId')
    options = [Option(str(p['id']), ("[CURRENT] " if p['id']==current else "")+p['name']) for p in profiles]
    select = Select(options, custom_id=PLEX_FIX_MEDIA_SELECT_PROFILE)
    embed = Embed('Select New Profile', description='Choose a new quality profile')
    return await client.interaction_response_message_edit(event, embed=embed, components=[select])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_PROFILE])
async def handle_profile_selected(client, event):
    """Apply the selected profile."""
    await client.interaction_component_acknowledge(event)
    session = _sessions.get(event.user_id)
    if not session or session.selected_series is None:
        return
    prof_id = int(event.values[0])
    if prof_id == session.selected_series.get('qualityProfileId'):
        return await client.interaction_response_message_edit(event, content="No change.")
    session.selected_series['qualityProfileId'] = prof_id
    await put_to_sonarr_api(client, f"series/{session.selected_series['id']}", session.selected_series)
    return await client.interaction_response_message_edit(event, embed=Embed('Profile Updated', description='Quality profile updated'), components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_TYPE])
async def handle_fix_type(client, event):
    """Allow changing the series type."""
    await client.interaction_component_acknowledge(event)
    options = [Option('standard','Standard'), Option('anime','Anime'), Option('daily','Daily')]
    select = Select(options, custom_id=PLEX_FIX_MEDIA_SELECT_TYPE)
    embed = Embed('Select Series Type', description='Choose a new series type')
    return await client.interaction_response_message_edit(event, embed=embed, components=[select])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_TYPE])
async def handle_type_selected(client, event):
    """Apply the selected series type."""
    await client.interaction_component_acknowledge(event)
    session = _sessions.get(event.user_id)
    if not session or session.selected_series is None:
        return
    selected_type = event.values[0]
    new_path = session.selected_series['path']
    if selected_type == 'anime' and '/tv-shows/' in new_path:
        new_path = new_path.replace('/tv-shows/','/anime-shows/')
    session.selected_series['seriesType'] = selected_type
    session.selected_series['path'] = new_path
    await put_to_sonarr_api(client, f"series/{session.selected_series['id']}", session.selected_series)
    return await client.interaction_response_message_edit(event, embed=Embed('Type Updated', description='Series type updated'), components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_RESYNC_MISSING])
async def handle_resync_missing(client, event):
    """Trigger a missing episode search."""
    await client.interaction_component_acknowledge(event)
    session = _sessions.get(event.user_id)
    if not session or session.selected_series is None:
        return
    await post_to_sonarr_api(client, "command", {"name":"MissingEpisodeSearch","seriesId":session.selected_series['id']})
    return await client.interaction_response_message_edit(event, embed=Embed('Rescan Started', description='Searching missing episodes.'), components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_ABORT])
async def abort_plex_fix_media(client, event):
    """Abort and delete the interaction (user or admin)."""
    # Allow original user or administrator
    if event.user_id != event.message.interaction.user_id and not event.user_permissions.administrator:
        return
    await client.interaction_component_acknowledge(event)
    _sessions.pop(event.user_id, None)
    await client.interaction_response_message_delete(event)
