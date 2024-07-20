__all__ = ()

from hata import Embed
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle, Row
from haruki.bots import Kiruha
from haruki.plugins.plex_request.overseer_search import MediaSearch

tmdb_image_url = 'https://image.tmdb.org/t/p/w300_and_h450_face'

PLEX_REQUEST_ID = 'plex_request'
PLEX_REQUEST_ABORT = 'plex_request_abort'
PLEX_REQUEST_REQUEST = 'plex_request_request'

MEDIA_TYPES = [
    'tv',
    'movie',
]

BUTTON_REQUEST = Button('Request', custom_id=PLEX_REQUEST_REQUEST, style=ButtonStyle.green)
BUTTON_ABORT = Button('Abort', custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red)

instances = {}


@Kiruha.interactions(is_global=True, name='plex_request')
async def initiate_plex_request(
        event, media_type: (MEDIA_TYPES, 'Pick Media Type'), media: ('str', 'Enter the media to search for')
):
    media_search = MediaSearch()
    instances[event.user_id] = media_search
    media_list = await media_search.get_search_results(media_type, media)
    embed = Embed(f'Searching for {media_type.title()}: {media.title()}')
    options = []
    print(media_list)
    for element in media_list:
        name = element['title']
        year = element['year']
        id = element['id']
        if name:
            title = f"{name} ({year})"
            options.append(Option(str(id), title))
    # Create the Select
    select = [
        Select(
            options,
            custom_id=PLEX_REQUEST_ID,
        ),
        [
            Button('Request', custom_id=PLEX_REQUEST_REQUEST, style=ButtonStyle.green),
            Button('Abort', custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red)
        ]
    ]
    return InteractionResponse(embed=embed, components=select)


@Kiruha.interactions(custom_id=[PLEX_REQUEST_REQUEST, PLEX_REQUEST_ID])
async def handle_media_selection(event):
    # We filter out 3rd party users based on original and current invoking user.
    if event.message.interaction.user_id != event.user_id:
        return
    selected_media_list = event.values
    # Second we filter out incorrect selected values.
    if selected_media_list is None:
        return
    media_search = instances.get(event.user_id)
    selected_media = selected_media_list[0]

    media_list = media_search.get_media_list()
    options = []
    for element in media_list:
        name = element['title']
        year = element['year']
        id = element['id']
        media_type = element['media_type']
        if name:
            title = f"{name} ({year})"
            if str(id) == str(selected_media):
                options.append(Option(str(id), title, default=True))
                selected_id = id

            else:
                options.append(Option(str(id), title))
    select = [
        Select(
            options,
            custom_id=PLEX_REQUEST_ID,
        ),
        [
            Button('Request', custom_id=PLEX_REQUEST_REQUEST, style=ButtonStyle.green),
            Button('Abort', custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red)
        ]
    ]
    media_info = await media_search.get_media_info(media_type, selected_media)
    url = tmdb_image_url + media_info['posterPath']
    embed = Embed(f'{media_info["title"]} - {media_info["year"].split("-")[0]}')
    embed.add_image(url)
    embed.add_author(f'{media_type} {selected_id}')
    embed.description = (
        f'{media_info["overview"]} \n')

    yield InteractionResponse(embed=embed, components=select)


@Kiruha.interactions(custom_id=[PLEX_REQUEST_REQUEST])
async def send_plex_request(client, event):
    # Allow closing for the source user
    if event.user is not event.message.interaction.user:
        return
    media_search = instances.get(event.user_id)
    media_type, id = event.message.embed.author.name.split()
    print(f'{media_type}: {id}')
    await media_search.request_selected_media(media_type, id)
    return


@Kiruha.interactions(custom_id=[PLEX_REQUEST_ABORT])
async def abort_plex_request(client, event):
    # Allow closing for the source user
    if event.user is not event.message.interaction.user:
        return

    # We can use `yield` as well for acknowledging it.
    await client.interaction_component_acknowledge(event)
    await client.interaction_response_message_delete(event)
