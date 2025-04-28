__all__ = ()

from hata import Embed
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle
from icecream import ic

from ...bots import Kiruha
from ..api_helpers.sonarr_api import post_to_sonarr_api, get_from_sonarr_api
from ..api_helpers.radarr_api import post_to_radarr_api, get_from_radarr_api

PLEX_FIX_MISSING_SELECT_MEDIA = "plex_fix_missing_select_media"
PLEX_FIX_MISSING_SELECT_SEASON = "plex_fix_missing_select_season"
PLEX_FIX_MISSING_SELECT_EPISODE = "plex_fix_missing_select_episode"
PLEX_FIX_MISSING_SELECT_RELEASE = "plex_fix_missing_select_release"
PLEX_FIX_MISSING_CHANGE_RELEASE = "plex_fix_missing_change_release"
PLEX_FIX_MISSING_APPROVE = "plex_fix_missing_approve"
PLEX_FIX_MISSING_ABORT = "plex_fix_missing_abort"

instances = {}

MEDIA_TYPES = ["tv", "movie"]

@Kiruha.interactions(is_global=True, name="plex-fix-missing")
async def initiate_plex_fix_missing(client, event,
    media_type: (MEDIA_TYPES, "Pick Media Type"),
    media: ("str", "Enter the media to search for")):
    # Initial search: series or missing movies
    await client.interaction_response_message_create(event, content='Searching...')
    ic(media_type, media)
    is_movie = (media_type == "movie")
    search_results = []

    if not is_movie:
        series_list = await get_from_sonarr_api(client, "series") or []
        search_results = [s for s in series_list if media.lower() in s.get('title', '').lower()]
    else:
        radarr_response = await get_from_radarr_api(
            client,
            "wanted/missing?page=1&pageSize=1000&monitored=true"
        ) or {}
        movie_list = radarr_response.get('records', [])
        search_results = [m for m in movie_list if media.lower() in (m.get('title', '') or '').lower()]

    if not search_results:
        await client.interaction_response_message_edit(event,
            content=f"No results found for '{media}'.")
        return

    options = []
    for item in search_results[:25]:
        title = item.get('title', 'Unknown')
        label = title if len(title) <= 100 else title[:97] + '...'
        options.append(Option(str(item['id']), label))

    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_MEDIA)
    embed = Embed('Select Media', description='Choose media to fix')
    instances[event.user_id] = {'is_movie': is_movie, 'search_results': search_results}

    await client.interaction_response_message_edit(event, embed=embed,
        components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_MEDIA])
async def handle_media_selection(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id, {})
    search_results = session.get('search_results', [])
    is_movie = session.get('is_movie', False)
    choice = event.values[0]
    item = next((i for i in search_results if str(i.get('id')) == choice), None)
    if not item:
        await client.interaction_response_message_edit(event, content="Media not found.")
        return
    session['selected_media'] = item

    if is_movie:
        await show_movie_releases(client, event, item)
    else:
        eps = await get_from_sonarr_api(client, f"episode?seriesId={item.get('id')}&missing=true") or []
        session['missing_episodes'] = eps
        seasons = sorted({ep.get('seasonNumber') for ep in eps})
        options = [Option(str(se), f"Season {se}") for se in seasons]
        embed = Embed('Select Season', description='Select season to inspect')
        select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_SEASON)
        await client.interaction_response_message_edit(event, embed=embed,
            components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_SEASON])
async def handle_season_selection(client, event):
    await client.interaction_component_acknowledge(event)
    season = int(event.values[0])
    session = instances.get(event.user_id, {})
    eps = session.get('missing_episodes', [])
    selected_eps = [ep for ep in eps if ep['seasonNumber'] == season]
    options = [Option(str(ep['id']), f"S{ep['seasonNumber']:02}E{ep['episodeNumber']:02} - {ep['title']}")
               for ep in selected_eps[:25]]
    embed = Embed('Select Episode', description='Choose an episode')
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_EPISODE)
    await client.interaction_response_message_edit(event, embed=embed,
        components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_EPISODE])
async def handle_episode_selection(client, event):
    await client.interaction_component_acknowledge(event)
    ep_id = event.values[0]
    releases = await get_from_sonarr_api(client, f"release?episodeId={ep_id}") or []
    instances[event.user_id]['releases'] = releases
    await display_release_options(client, event, releases, is_movie=False)

async def display_release_options(client, event, releases, is_movie):
    options = []
    for rel in sorted(releases, key=lambda r: r.get('qualityWeight', 0) if not is_movie else r.get('customFormatScore', 0), reverse=True)[:25]:
        emoji = '✅' if rel.get('approved') else '❌'
        label = f"{emoji} {rel.get('title') or rel.get('movieTitles','')[0]}"
        if len(label) > 100:
            label = label[:97] + '...'
        options.append(Option(rel['guid'], label))
    title = 'Select Movie Release' if is_movie else 'Select Release'
    desc = 'Choose a release to download'
    embed = Embed(title, description=desc)
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_RELEASE)
    await client.interaction_response_message_edit(event, embed=embed,
        components=[select, [
            Button('Change', custom_id=PLEX_FIX_MISSING_CHANGE_RELEASE, style=ButtonStyle.blue),
            Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)
        ]])

async def show_movie_releases(client, event, movie):
    releases = await get_from_radarr_api(client, f"release?movieId={movie['id']}") or []
    valid = [r for r in releases if not r.get('rejected') or r.get('customFormatScore', 0) > 0] or releases
    instances[event.user_id]['releases'] = valid
    await display_release_options(client, event, valid, is_movie=True)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_RELEASE])
async def handle_release_selection(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id, {})
    rels = session.get('releases', [])
    guid = event.values[0]
    rel = next((r for r in rels if r['guid'] == guid), None)
    if not rel:
        await client.interaction_response_message_edit(event, content="Release not found.")
        return
    session['selected_release'] = rel
    embed = Embed('Release Info', description=rel.get('title') or rel.get('movieTitles','')[0])
    quality = rel.get('quality', {}).get('quality', {}).get('name')
    if quality:
        embed.add_field('Quality', quality, inline=True)
    size = rel.get('size', 0)
    embed.add_field('Size', f"{size/(1024**3):.2f} GB", inline=True)
    embed.add_field('Indexer', rel.get('indexer', 'Unknown'), inline=True)
    langs = ', '.join(l.get('name') for l in rel.get('languages', [])) or 'Unknown'
    embed.add_field('Languages', langs, inline=True)
    score = rel.get('customFormatScore')
    if score is not None:
        embed.add_field('Score', str(score), inline=True)
    if rel.get('rejections'):
        embed.add_field('Rejections', '\n'.join(rel['rejections']), inline=False)
    await client.interaction_response_message_edit(event, embed=embed,
        components=[[
            Button('Approve', custom_id=PLEX_FIX_MISSING_APPROVE, style=ButtonStyle.green),
            Button('Change', custom_id=PLEX_FIX_MISSING_CHANGE_RELEASE, style=ButtonStyle.blue),
            Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)
        ]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_CHANGE_RELEASE])
async def handle_change_release(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id, {})
    releases = session.get('releases', [])
    is_movie = session.get('is_movie', False)
    await display_release_options(client, event, releases, is_movie)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_APPROVE])
async def handle_approve_download(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id, {})
    rel = session.get('selected_release')
    is_movie = session.get('is_movie', False)
    if not rel:
        await client.interaction_response_message_edit(event, content="No release selected.")
        return
    payload = {'guid': rel['guid'], 'indexerId': rel['indexerId'],'title': rel.get('title') or rel.get('movieTitles','')[0],'protocol': rel['protocol']}
    if is_movie:
        await post_to_radarr_api(client, 'release', payload)
    else:
        await post_to_sonarr_api(client, 'release', payload)
    await client.interaction_response_message_edit(event,
        embed=Embed('Download Started', description=f"Downloading: {rel.get('title') or rel.get('movieTitles','')[0]}"),
        components=None)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_ABORT])
async def abort_plex_fix_missing(client, event):
    if event.user is not event.message.interaction.user:
        return
    await client.interaction_component_acknowledge(event)
    await client.interaction_response_message_delete(event)
