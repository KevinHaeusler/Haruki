__all__ = ()

from hata import Embed
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle
from icecream import ic

from ...bots import Kiruha
from ..api_helpers.sonarr_api import post_to_sonarr_api, get_from_sonarr_api

PLEX_FIX_MISSING_SELECT_MEDIA = "plex_fix_missing_select_media"
PLEX_FIX_MISSING_SELECT_SEASON = "plex_fix_missing_select_season"
PLEX_FIX_MISSING_ABORT = "plex_fix_missing_abort"

instances = {}
last_selected_media = {}
last_selected_season = {}

MEDIA_TYPES = ["tv", "movie"]

@Kiruha.interactions(is_global=True, name="plex-fix-missing")
async def initiate_plex_fix_missing(client, event, media_type: (MEDIA_TYPES, "Pick Media Type"), media: ("str", "Enter the media to search for")):
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

    options = [Option(str(series['id']), f"{series['title']} ({series.get('year', 'Unknown')})") for series in search_results]

    embed = Embed('Select Media', description='Select the media you want to fix')
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_MEDIA)

    instances[event.user_id] = search_results

    await client.interaction_response_message_edit(event, embed=embed, components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_MEDIA])
async def handle_media_selection(client, event):
    await client.interaction_component_acknowledge(event)
    selected_media_id = event.values[0]
    last_selected_media[event.user_id] = selected_media_id

    media_list = instances.get(event.user_id, [])
    selected_series = next((series for series in media_list if str(series['id']) == selected_media_id), None)

    if not selected_series:
        await client.interaction_response_message_edit(event, content="Selected media not found.")
        return

    episodes = await get_from_sonarr_api(client, f"episode?seriesId={selected_series['id']}")
    missing_episodes = [ep for ep in episodes if not ep.get("hasFile")]

    if not missing_episodes:
        await client.interaction_response_message_edit(event, content=f"No missing episodes found for {selected_series['title']}.")
        return

    seasons = sorted(set(ep['seasonNumber'] for ep in missing_episodes))
    options = [Option(str(season), f"Season {season}") for season in seasons]

    embed = Embed('Select Season', description='Select a season to view missing episodes')
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_SEASON)

    instances[event.user_id] = missing_episodes

    await client.interaction_response_message_edit(event, embed=embed, components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_SEASON])
async def handle_season_selection(client, event):
    await client.interaction_component_acknowledge(event)
    selected_season = int(event.values[0])
    last_selected_season[event.user_id] = selected_season

    missing_episodes = instances.get(event.user_id, [])
    selected_episodes = [ep for ep in missing_episodes if ep['seasonNumber'] == selected_season]

    options = [Option(str(ep['id']), f"S{ep['seasonNumber']}E{ep['episodeNumber']} - {ep['title']}") for ep in selected_episodes]

    embed = Embed('Select Episode', description='Select an episode to search for releases')
    select = Select(options, custom_id="plex_fix_missing_select_episode")

    instances[event.user_id] = selected_episodes

    await client.interaction_response_message_edit(event, embed=embed, components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=["plex_fix_missing_select_episode"])
async def handle_episode_selection(client, event):
    await client.interaction_component_acknowledge(event)
    selected_episode_id = event.values[0]

    releases = await get_from_sonarr_api(client, f"release?episodeId={selected_episode_id}")

    valid_releases = []
    for release in releases:
        if release.get('customFormatScore', 0) >= 0:
            valid_releases.append(release)

    valid_releases = sorted(valid_releases, key=lambda r: r.get('qualityWeight', 0), reverse=True)[:20]

    if not valid_releases:
        await client.interaction_response_message_edit(event, content="No valid releases found.")
        return

    options = []
    for release in valid_releases:
        title = release['title']
        emoji = '✅' if release.get('approved') else '❌'
        display_title = f"{emoji} {title}"
        if len(display_title) > 100:
            display_title = display_title[:97] + "..."
        options.append(Option(release['guid'], display_title))

    embed = Embed('Select Release', description='Pick a release to view details')
    select = Select(options, custom_id="plex_fix_missing_select_release")

    instances[event.user_id] = valid_releases

    await client.interaction_response_message_edit(event, embed=embed, components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=["plex_fix_missing_select_release"])
async def handle_release_selection(client, event):
    await client.interaction_component_acknowledge(event)
    selected_guid = event.values[0]
    releases = instances.get(event.user_id, [])

    release = next((r for r in releases if r['guid'] == selected_guid), None)
    if not release:
        await client.interaction_response_message_edit(event, content="Selected release not found.")
        return

    instances[event.user_id] = release  # Save selected release separately

    embed = Embed('Release Information', description=release['title'])
    embed.add_field('Quality', release['quality']['quality']['name'], inline=True)
    embed.add_field('Size', f"{release['size'] / (1024 ** 3):.2f} GB", inline=True)
    embed.add_field('Indexer', release['indexer'], inline=True)

    languages = ', '.join(lang['name'] for lang in release.get('languages', [])) or 'Unknown'
    embed.add_field('Languages', languages, inline=True)

    custom_score = release.get('customFormatScore', 0)
    embed.add_field('Custom Format Score', str(custom_score), inline=True)

    if release.get('rejections'):
        embed.add_field('Rejections', '\n'.join(release['rejections']), inline=False)

    approve_button = Button('Approve Download', custom_id='plex_fix_missing_approve', style=ButtonStyle.green)
    abort_button = Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)

    await client.interaction_response_message_edit(event, embed=embed, components=[[approve_button, abort_button]])

@Kiruha.interactions(custom_id=["plex_fix_missing_approve"])
async def handle_approve_download(client, event):
    await client.interaction_component_acknowledge(event)
    release = instances.get(event.user_id, None)

    if not release:
        await client.interaction_response_message_edit(event, content="No release selected.")
        return

    payload = {
        "guid": release["guid"],
        "indexerId": release["indexerId"],
        "title": release["title"],
        "protocol": release["protocol"]
    }
    await post_to_sonarr_api(client, "release", payload)

    embed = Embed('Download Started', description=f"Downloading: {release['title']}")
    await client.interaction_response_message_edit(event, embed=embed, components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_ABORT])
async def abort_plex_fix_missing(client, event):
    if event.user is not event.message.interaction.user:
        return

    await client.interaction_component_acknowledge(event)
    await client.interaction_response_message_delete(event)
