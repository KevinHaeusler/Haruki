__all__ = ()

from hata import Embed
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle, Row
from haruki.bots import Kiruha
from haruki.plugins.plex_request.overseer_search import get_search_results, get_media_info

tmdb_image_url = 'https://image.tmdb.org/t/p/w300_and_h450_face'

PLEX_REQUEST_ID = 'plex_request'
PLEX_REQUEST_MEDIA = 'plex_request_media'
PLEX_REQUEST_ABORT = 'plex_request_abort'

MEDIA_TYPES = [
    'tv',
    'movie',
]

BUTTON_REQUEST = Button('Request', custom_id=PLEX_REQUEST_MEDIA, style=ButtonStyle.green)
BUTTON_ABORT = Button('Abort', custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red)


@Kiruha.interactions(is_global=True)
async def plex_request(media_type: (MEDIA_TYPES, 'Pick Media Type'), media: ('str', 'Enter the media to search for')):
    media_list = await get_search_results(media_type, media)
    embed = Embed(f'Searching for {media_type.title()}: {media.title()}')
    options = []
    for element in media_list:
        name = element['title']
        year = element['year']
        id = element['id']
        if name:
            title = f"{name} ({year})"
            options.append(Option(str(id), title))
    # Create the Select
    select = [
        Row(
            Select(
                options,
                custom_id=PLEX_REQUEST_ID, )
        ),
        Row(
            Button('Request', custom_id=PLEX_REQUEST_MEDIA, style=ButtonStyle.green),
            Button('Abort', custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red))]

    return InteractionResponse(embed=embed, components=select)


@Kiruha.interactions(custom_id=[PLEX_REQUEST_ID, PLEX_REQUEST_MEDIA, PLEX_REQUEST_ABORT])
async def handle_media_selection(event):
    # We filter out 3rd party users based on original and current invoking user.
    if event.message.interaction.user_id != event.user_id:
        return
    selected_media_list = event.values
    # Second we filter out incorrect selected values.
    if selected_media_list is None:
        return
    selected_media = selected_media_list[0]
    print(event.interaction.custom_id)
    if event.interaction.custom_id == "plex_request_abort":
        print("RIP")
    elif event.interaction.custom_id == "plex_request_media":
        print("Yay")

    movie_info = await get_media_info("movie", selected_media)
    url = tmdb_image_url + movie_info['posterPath']
    embed = Embed(f'{movie_info["title"]} - {movie_info["releaseDate"].split("-")[0]}')
    embed.add_image(url)
    embed.description = (
        f'{movie_info["overview"]} \n'

    )
    yield InteractionResponse(embed=embed)


