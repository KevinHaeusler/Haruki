__all__ = ()

from hata import Embed, Role
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle, abort
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
PLEX_FIX_MISSING_PAGE_NEXT = "plex_fix_missing_page_next"
PLEX_FIX_MISSING_PAGE_PREV = "plex_fix_missing_page_prev"
PLEX_FIX_MISSING_EP_PAGE_NEXT = "plex_fix_missing_ep_page_next"
PLEX_FIX_MISSING_EP_PAGE_PREV = "plex_fix_missing_ep_page_prev"

instances = {}

MEDIA_TYPES = ["tv", "movie"]
LISTING_MODES = ["missing only", "all files"]
PAGE_SIZE = 25

# Precreate Plex role
ROLE_PLEX = Role.precreate(1228676841057816707)

@Kiruha.interactions(is_global=True, name="plex-fix-missing")
async def initiate_plex_fix_missing(
    client,
    event,
    media_type: (MEDIA_TYPES, "Pick Media Type"),
    media: ("str", "Enter the media to search for"),
    listing_mode: (LISTING_MODES, "Choose listing mode: missing only or all files") = "missing only",
):
    """Fix missing Plex media (missing only or all files)."""
    # Role check
    if not event.user.has_role(ROLE_PLEX):
        return abort("You need the Plex role to use this command.")
    await client.interaction_response_message_create(event, content='Searching...')
    ic(media_type, media, listing_mode)
    is_movie = (media_type == "movie")
    # fetch search_results
    if is_movie:
        if listing_mode == "all files":
            movie_list = await get_from_radarr_api(client, "movie") or []
        else:
            radarr_resp = await get_from_radarr_api(
                client, "wanted/missing?page=1&pageSize=1000&monitored=true"
            ) or {}
            movie_list = radarr_resp.get('records', [])
        search_results = [m for m in movie_list if media.lower() in (m.get('title') or '').lower()]
    else:
        series_list = await get_from_sonarr_api(client, "series") or []
        search_results = [s for s in series_list if media.lower() in (s.get('title') or '').lower()]
    if not search_results:
        await client.interaction_response_message_edit(
            event,
            content=(f"No {'missing ' if listing_mode=='missing only' else ''}results found for '{media}'.")
        )
        return
    # init paging for media
    instances[event.user_id] = {
        'is_movie': is_movie,
        'listing_mode': listing_mode,
        'search_results': search_results,
        'page': 0,
    }
    await _send_media_page(client, event, event.user_id)

async def _send_media_page(client, event, user_id):
    session = instances[user_id]
    results = session['search_results']
    page = session.get('page', 0)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    slice_ = results[start:end]
    options = []
    for item in slice_:
        title = item.get('title', 'Unknown')
        label = title if len(title) <= 100 else title[:97] + '...'
        options.append(Option(str(item['id']), label))
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_MEDIA)
    nav = []
    if page > 0:
        nav.append(Button('Prev', custom_id=PLEX_FIX_MISSING_PAGE_PREV, style=ButtonStyle.gray))
    if end < len(results):
        nav.append(Button('Next', custom_id=PLEX_FIX_MISSING_PAGE_NEXT, style=ButtonStyle.gray))
    components = [select, nav + [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]]
    embed = Embed('Select Media', description=f'Page {page+1} of {(len(results)-1)//PAGE_SIZE+1}')
    await client.interaction_response_message_edit(event, embed=embed, components=components)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_PAGE_NEXT, PLEX_FIX_MISSING_PAGE_PREV])
async def handle_media_paging(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    if not session:
        return
    if event.custom_id == PLEX_FIX_MISSING_PAGE_NEXT:
        session['page'] += 1
    else:
        session['page'] = max(session['page'] - 1, 0)
    await _send_media_page(client, event, event.user_id)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_MEDIA])
async def handle_media_selection(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    is_movie = session['is_movie']
    listing_mode = session['listing_mode']
    choice = event.values[0]
    item = next((i for i in session['search_results'] if str(i.get('id')) == choice), None)
    if not item:
        await client.interaction_response_message_edit(event, content="Media not found.")
        return
    session['selected_media'] = item
    if is_movie:
        await show_movie_releases(client, event, item)
    else:
        all_eps = await get_from_sonarr_api(client, f"episode?seriesId={item['id']}") or []
        if listing_mode == "missing only":
            eps = [ep for ep in all_eps if not ep.get('hasFile', False)]
        else:
            eps = all_eps
        session['missing_episodes'] = eps
        # init paging for episodes of first selected season
        # seasons list handled later
        options = []
        seasons = sorted({ep['seasonNumber'] for ep in eps})
        for se in seasons:
            options.append(Option(str(se), f"Season {se}"))
        embed = Embed('Select Season', description='Select season to inspect')
        select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_SEASON)
        await client.interaction_response_message_edit(event, embed=embed,
            components=[select, [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]])

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_SEASON])
async def handle_season_selection(client, event):
    await client.interaction_component_acknowledge(event)
    season = int(event.values[0])
    session = instances.get(event.user_id)
    eps = session['missing_episodes']
    season_eps = [ep for ep in eps if ep['seasonNumber'] == season]
    session['current_season_eps'] = season_eps
    session['episode_page'] = 0
    await _send_episode_page(client, event, event.user_id)

async def _send_episode_page(client, event, user_id):
    session = instances[user_id]
    eps = session['current_season_eps']
    page = session.get('episode_page', 0)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    slice_eps = eps[start:end]
    options = []
    for ep in slice_eps:
        # Prefix status emoji based on file existence
        status = '✅' if ep.get('hasFile', False) else '❓'
        title = ep.get('title', '')
        label = f"{status} S{ep['seasonNumber']:02}E{ep['episodeNumber']:02} - {title}"
        if len(label) > 100:
            label = label[:97] + '...'
        options.append(Option(str(ep['id']), label))
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_EPISODE)
    nav = []
    if page > 0:
        nav.append(Button('Prev', custom_id=PLEX_FIX_MISSING_EP_PAGE_PREV, style=ButtonStyle.gray))
    if end < len(eps):
        nav.append(Button('Next', custom_id=PLEX_FIX_MISSING_EP_PAGE_NEXT, style=ButtonStyle.gray))
    components = [select, nav + [Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)]]
    embed = Embed('Select Episode', description=f'Page {page+1} of {(len(eps)-1)//PAGE_SIZE+1}')
    await client.interaction_response_message_edit(event, embed=embed, components=components)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_EP_PAGE_NEXT, PLEX_FIX_MISSING_EP_PAGE_PREV])
async def handle_episode_paging(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    if not session:
        return
    if event.custom_id == PLEX_FIX_MISSING_EP_PAGE_NEXT:
        session['episode_page'] += 1
    else:
        session['episode_page'] = max(session['episode_page'] - 1, 0)
    await _send_episode_page(client, event, event.user_id)

@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_EPISODE])
async def handle_episode_selection(client, event):
    await client.interaction_component_acknowledge(event)
    ep_id = event.values[0]
    session = instances.get(event.user_id)
    releases = await get_from_sonarr_api(client, f"release?episodeId={ep_id}") or []
    session['releases'] = releases
    await display_release_options(client, event, releases, is_movie=False)



async def display_release_options(client, event, releases, is_movie):
    options = []
    key_func = (lambda r: r.get('qualityWeight', 0)) if not is_movie else (lambda r: r.get('customFormatScore', 0))
    for rel in sorted(releases, key=key_func, reverse=True)[:25]:
        emoji = '✅' if rel.get('approved') else '❌'
        title = rel.get('title') or (rel.get('movieTitles') or [''])[0]
        label = f"{emoji} {title}"
        if len(label) > 100:
            label = label[:97] + '...'
        options.append(Option(rel['guid'], label))
    embed = Embed(
        'Select Movie Release' if is_movie else 'Select Release',
        description='Choose a release to download'
    )
    select = Select(options, custom_id=PLEX_FIX_MISSING_SELECT_RELEASE)
    session = instances[event.user_id]  
    session['select_component'] = select
    await client.interaction_response_message_edit(
        event,
        embed=embed,
        components=[
            select,
            [
                Button('Change', custom_id=PLEX_FIX_MISSING_CHANGE_RELEASE, style=ButtonStyle.blue),
                Button('Abort', custom_id=PLEX_FIX_MISSING_ABORT, style=ButtonStyle.red)
            ]
        ]
    )


async def show_movie_releases(client, event, movie):
    releases = await get_from_radarr_api(client, f"release?movieId={movie['id']}") or []
    valid = [r for r in releases if not r.get('rejected') or r.get('customFormatScore', 0) > 0] or releases
    instances[event.user_id]['releases'] = valid
    await display_release_options(client, event, valid, is_movie=True)


@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_SELECT_RELEASE])
async def handle_release_selection(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    rels = session['releases']
    guid = event.values[0]
    rel = next((r for r in rels if r['guid'] == guid), None)
    if not rel:
        await client.interaction_response_message_edit(event, content="Release not found.")
        return
    session['selected_release'] = rel
    embed = Embed('Release Info', description=rel.get('title') or (rel.get('movieTitles') or [''])[0])
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
    
    select = session['select_component']
    await client.interaction_response_message_edit(
        event,
        embed=embed,
        components=[
            select,
            [ 
              Button('Approve', custom_id=PLEX_FIX_MISSING_APPROVE, style=ButtonStyle.green),
              Button('Abort',   custom_id=PLEX_FIX_MISSING_ABORT,   style=ButtonStyle.red)
            ]
        ]
    )


@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_CHANGE_RELEASE])
async def handle_change_release(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    releases = session['releases']
    is_movie = session['is_movie']
    await display_release_options(client, event, releases, is_movie)


@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_APPROVE])
async def handle_approve_download(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    rel = session.get('selected_release')
    is_movie = session.get('is_movie')
    if not rel:
        await client.interaction_response_message_edit(event, content="No release selected.")
        return
    payload = {
        'guid': rel['guid'],
        'indexerId': rel['indexerId'],
        'title': rel.get('title') or (rel.get('movieTitles') or [''])[0],
        'protocol': rel['protocol'],
    }
    if is_movie:
        await post_to_radarr_api(client, 'release', payload)
    else:
        await post_to_sonarr_api(client, 'release', payload)
    await client.interaction_response_message_edit(
        event,
        embed=Embed('Download Started', description=f"Downloading: {payload['title']}"),
        components=None
    )


@Kiruha.interactions(custom_id=[PLEX_FIX_MISSING_ABORT])
async def abort_plex_fix_missing(client, event):
    if event.user_id != event.message.interaction.user_id and not event.user_permissions.administrator:
        return
    await client.interaction_component_acknowledge(event)
    await client.interaction_response_message_delete(event)
