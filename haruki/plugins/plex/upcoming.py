__all__ = ()

from datetime import datetime, timedelta
from hata import Embed
from hata.ext.slash import InteractionResponse, Button, ButtonStyle

from ...bots import Kiruha
from ..api_helpers.sonarr_api import get_from_sonarr_api
from ..api_helpers.radarr_api import get_from_radarr_api

MEDIA_TYPES = ["all", "tv", "movie"]
UPCOMING_CALENDAR_COMMAND = 'plex_upcoming_calendar'

# store per-user pagination state
instances = {}

@Kiruha.interactions(is_global=True, name="upcoming-calendar")
async def upcoming_calendar(
    client,
    event,
    media_type: (MEDIA_TYPES, "Pick type: all, tv, or movie") = "all",
    days: (int, "Number of days ahead to show (max 30)") = 7,
):
    """Show upcoming TV episodes and/or movie releases over the next X days."""
    days = max(1, min(days, 30))
    # date window
    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=days)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    await client.interaction_response_message_create(event, content='Fetching upcoming items...')

    tv_items = []
    movie_items = []
    series_map = {}

    if media_type in ("all", "tv"):
        # Sonarr calendar
        tv_items = await get_from_sonarr_api(
            client,
            f"calendar?start={start_str}&end={end_str}"
        ) or []
        # map seriesId to title
        all_series = await get_from_sonarr_api(client, "series") or []
        series_map = {s['id']: s.get('title', 'Unknown') for s in all_series}

    if media_type in ("all", "movie"):
        # Radarr calendar for movie releases
        movie_items = await get_from_radarr_api(
            client,
            f"calendar?start={start_str}&end={end_str}"
        ) or []
        # Filter movies by release date window
        filtered_movies = []
        for m in movie_items:
            raw_mdate = (m.get('inCinemas') or m.get('physicalRelease') or m.get('digitalRelease') or '').split('T')[0]
            try:
                md = datetime.strptime(raw_mdate, '%Y-%m-%d').date()
            except Exception:
                continue
            if start_date.date() <= md <= end_date.date():
                                filtered_movies.append(m)
        # assign filtered list after collecting
        movie_items = filtered_movies

    # Combine based on selection
    items = []
    if media_type == "all":
        # tag each with type
        items = [dict(entry, _type='tv') for entry in tv_items]
        items += [dict(entry, _type='movie') for entry in movie_items]
    elif media_type == "tv":
        items = [dict(entry, _type='tv') for entry in tv_items]
    else:
        items = [dict(entry, _type='movie') for entry in movie_items]

    if not items:
        await client.interaction_response_message_edit(
            event,
            content=f"No upcoming {media_type} items in the next {days} days."
        )
        return

    # build paginated embeds
    pages = []
    per_page = 10
        # set dynamic title header
    if media_type == 'movie':
        title_prefix = f'Upcoming Movies in the next {days} days'
    elif media_type == 'tv':
        title_prefix = f'Upcoming Episodes in the next {days} days'
    else:
        title_prefix = f'Upcoming TV & Movies in the next {days} days'
    for idx in range(0, len(items), per_page):
        slice_ = items[idx:idx+per_page]
        embed = Embed(f'{title_prefix} (Page {idx//per_page+1})')
        for obj in slice_:
            raw_date = (
                obj.get('airDateUtc') or obj.get('airDate') or
                obj.get('inCinemas') or obj.get('physicalRelease') or ''
            ).split('T')[0]
            try:
                dt = datetime.strptime(raw_date, '%Y-%m-%d')
                display_date = dt.strftime('%d.%m.%Y')
            except:
                display_date = raw_date

            if obj.get('_type') == 'tv':
                series = series_map.get(obj.get('seriesId'), 'Unknown')
                season = obj.get('seasonNumber')
                number = obj.get('episodeNumber')
                title = obj.get('title') or 'Unknown'
                name = f"{display_date} - {series} S{season:02}E{number:02}"
                value = f"||{title}||"
            else:
                title = obj.get('title') or obj.get('movieTitle') or 'Unknown'
                name = f"{display_date} - {title}"
                value = f"Release"  
            embed.add_field(name=name, value=value, inline=False)
        pages.append(embed)

    # Save pagination state
    instances[event.user_id] = {'pages': pages, 'index': 0}
    buttons = [
        Button('Prev', custom_id='upcoming_prev', style=ButtonStyle.gray),
        Button('Next', custom_id='upcoming_next', style=ButtonStyle.gray),
    ]
    await client.interaction_response_message_edit(event, embed=pages[0], components=[buttons])

@Kiruha.interactions(custom_id=['upcoming_prev', 'upcoming_next'])
async def upcoming_paging(client, event):
    await client.interaction_component_acknowledge(event)
    session = instances.get(event.user_id)
    if not session:
        return
    if event.custom_id == 'upcoming_next':
        session['index'] = (session['index'] + 1) % len(session['pages'])
    else:
        session['index'] = (session['index'] - 1) % len(session['pages'])
    buttons = [
        Button('Prev', custom_id='upcoming_prev', style=ButtonStyle.gray),
        Button('Next', custom_id='upcoming_next', style=ButtonStyle.gray),
    ]
    await client.interaction_response_message_edit(
        event,
        embed=session['pages'][session['index']],
        components=[buttons]
    )
