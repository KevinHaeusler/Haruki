__all__ = ()


from hata import Embed
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle
from icecream import ic


from ...bots import Kiruha
from ..api_helpers.sonarr_api import get_from_sonarr_api, post_to_sonarr_api, put_to_sonarr_api

PLEX_FIX_MEDIA_SELECT_MEDIA = "plex_fix_media_select_media"
PLEX_FIX_MEDIA_ABORT = "plex_fix_media_abort"
PLEX_FIX_MEDIA_SELECT_PROFILE = "plex_fix_media_select_profile"
PLEX_FIX_MEDIA_SELECT_TYPE = "plex_fix_media_select_type"
PLEX_FIX_MEDIA_RESYNC_MISSING = "plex_fix_media_resync_missing"
PLEX_FIX_MEDIA_BACK_OVERVIEW = "plex_fix_media_back_overview"

instances = {}
last_selected_media = {}
profiles_cache = {}

MEDIA_TYPES = ["tv", "movie"]

@Kiruha.interactions(is_global=True, name="plex-fix-media")
async def initiate_plex_fix_media(client, event, media_type: (MEDIA_TYPES, "Pick Media Type"), media: ("str", "Enter the media to search for")):
    await client.interaction_response_message_create(event, content='Searching...')
    ic(media_type, media)
    search_results = []

    if media_type == "tv":
        series_list = await get_from_sonarr_api(client, "series")
        search_results = [series for series in series_list if media.lower() in series.get("title", "").lower()]
    else:
        await client.interaction_response_message_edit(event, content="Currently only TV search is supported.")
        return

    if not search_results:
        await client.interaction_response_message_edit(event, content=f"No results found for '{media}'.")
        return

    global profiles_cache
    profiles = await get_from_sonarr_api(client, "qualityprofile")
    profiles_cache = {profile['id']: profile['name'] for profile in profiles}

    options = [Option(str(series['id']), f"{series['title']} ({series.get('year', 'Unknown')})") for series in search_results]

    embed = Embed('Select Media', description='Select the media you want to fix')
    select = Select(options, custom_id=PLEX_FIX_MEDIA_SELECT_MEDIA)

    instances[event.user_id] = search_results

    await client.interaction_response_message_edit(event, embed=embed, components=[select, [Button('Abort', custom_id=PLEX_FIX_MEDIA_ABORT, style=ButtonStyle.red)]])

async def send_series_overview(client, event, series):
    files = await get_from_sonarr_api(client, f"episodefile?seriesId={series['id']}")
    disk_size = sum(file.get('size', 0) for file in files)

    profile_name = profiles_cache.get(series.get('qualityProfileId'), 'Unknown')

    embed = Embed(f"{series['title']}", description='Media Details')
    embed.add_field('Profile', profile_name, inline=True)
    embed.add_field('Type', series.get('seriesType', 'Unknown'), inline=True)
    embed.add_field('Disk Path', series.get('path', 'Unknown'), inline=False)
    embed.add_field('Disk Size', f"{disk_size / (1024 ** 3):.2f} GB", inline=True)
    embed.add_field('Status', series.get('status', 'Unknown'), inline=True)

    fix_profile_button = Button('Fix Profile', custom_id='plex_fix_media_fix_profile', style=ButtonStyle.green)
    fix_type_button = Button('Fix Type (Anime/Standard/Daily)', custom_id='plex_fix_media_fix_type', style=ButtonStyle.green)
    resync_button = Button('Search Missing', custom_id=PLEX_FIX_MEDIA_RESYNC_MISSING, style=ButtonStyle.green)
    abort_button = Button('Abort', custom_id=PLEX_FIX_MEDIA_ABORT, style=ButtonStyle.red)

    await client.interaction_response_message_edit(event, embed=embed, components=[[fix_profile_button, fix_type_button, resync_button, abort_button]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_MEDIA])
async def handle_media_selection(client, event):
    await client.interaction_component_acknowledge(event)
    selected_media_id = event.values[0]
    last_selected_media[event.user_id] = selected_media_id

    full_series = await get_from_sonarr_api(client, f"series/{selected_media_id}")
    instances[event.user_id] = full_series

    await send_series_overview(client, event, full_series)

@Kiruha.interactions(custom_id=['plex_fix_media_fix_profile'])
async def handle_fix_profile(client, event):
    await client.interaction_component_acknowledge(event)
    profiles = await get_from_sonarr_api(client, "qualityprofile")

    series = instances.get(event.user_id)
    if not series:
        await client.interaction_response_message_edit(event, content="Series not found in session.")
        return

    current_profile_id = series.get('qualityProfileId')

    options = []
    for profile in profiles:
        name = profile['name']
        if profile['id'] == current_profile_id:
            name = f"[CURRENT] {name}"
        options.append(Option(str(profile['id']), name))

    select = Select(options, custom_id=PLEX_FIX_MEDIA_SELECT_PROFILE)
    embed = Embed('Select New Profile', description='Choose a new quality profile')

    await client.interaction_response_message_edit(event, embed=embed, components=[select])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_PROFILE])
async def handle_profile_selected(client, event):
    await client.interaction_component_acknowledge(event)
    selected_profile_id = int(event.values[0])
    series = instances.get(event.user_id)

    if not series:
        await client.interaction_response_message_edit(event, content="Series not found in session.")
        return

    if selected_profile_id == series.get('qualityProfileId'):
        await client.interaction_response_message_edit(event, content="You selected the same profile. No changes made.")
        return

    series['qualityProfileId'] = selected_profile_id
    await put_to_sonarr_api(client, f"series/{series['id']}", series)

    embed = Embed('Profile Updated', description=f"{event.user:f} changed profile to {profiles_cache.get(selected_profile_id, 'Unknown')} for {series['title']}")
    await client.interaction_response_message_edit(event, embed=embed, components=None)

@Kiruha.interactions(custom_id=['plex_fix_media_fix_type'])
async def handle_fix_type(client, event):
    await client.interaction_component_acknowledge(event)
    options = [
        Option('standard', 'Standard (Season/Episode)'),
        Option('daily', 'Daily (Date)'),
        Option('anime', 'Anime (Absolute numbering)')
    ]
    select = Select(options, custom_id=PLEX_FIX_MEDIA_SELECT_TYPE)
    embed = Embed('Select New Series Type', description='Choose a new series type')

    await client.interaction_response_message_edit(event, embed=embed, components=[select])

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_SELECT_TYPE])
async def handle_type_selected(client, event):
    await client.interaction_component_acknowledge(event)
    selected_type = event.values[0]
    series = instances.get(event.user_id)

    if not series:
        await client.interaction_response_message_edit(event, content="Series not found in session.")
        return

    new_path = series['path']
    if selected_type == 'anime' and '/tv-shows/' in new_path:
        new_path = new_path.replace('/tv-shows/', '/anime-shows/')

    series['seriesType'] = selected_type
    series['path'] = new_path

    await put_to_sonarr_api(client, f"series/{series['id']}", series)

    embed = Embed('Type Updated', description=f"{event.user:f} changed type to {selected_type} for {series['title']}")
    await client.interaction_response_message_edit(event, embed=embed, components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_RESYNC_MISSING])
async def handle_resync_missing(client, event):
    await client.interaction_component_acknowledge(event)
    series = instances.get(event.user_id)

    if not series:
        await client.interaction_response_message_edit(event, content="Series not found in session.")
        return

    payload = {"name": "MissingEpisodeSearch", "seriesId": series['id']}
    await post_to_sonarr_api(client, "command", payload)

    embed = Embed('Rescan Started', description=f"Searching missing episodes for {series['title']}.")
    await client.interaction_response_message_edit(event, embed=embed, components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MEDIA_ABORT])
async def abort_plex_fix_media(client, event):
    if event.user is not event.message.interaction.user:
        return

    await client.interaction_component_acknowledge(event)
    await client.interaction_response_message_delete(event)