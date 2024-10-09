__all__ = ()

from optparse import Option

from hata import Embed
from hata.ext.slash import Select, Option, InteractionResponse, Button, ButtonStyle
from icecream import ic

from haruki.bots import Kiruha
from haruki.plugins.overseerr.overseerr_search import OverseerrTvSearch, OverseerrMovieSearch, OverseerrSearch
from hata.ext.slash import abort

PLEX_REQUEST_ID = "plex_request"
PLEX_REQUEST_ABORT = "plex_request_abort"
PLEX_REQUEST_REQUEST = "plex_request_request"

MEDIA_TYPES = [
    "tv",
    "movie",
]

BUTTON_REQUEST = Button("Request", custom_id=PLEX_REQUEST_REQUEST, style=ButtonStyle.green)
BUTTON_ABORT = Button("Abort", custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red)

instances = {}

global_results = {}
last_selected_media = {}

tmdb_image_url = "https://image.tmdb.org/t/p/w300_and_h450_face"


def build_embed_list(results, selected_media):
    options = []
    for element in results:
        name = element["title"]
        year = element["year"]
        id = element["id"]
        if name:
            title = f"{name} ({year})"
            if str(id) == str(selected_media):
                options.append(Option(str(id), title, default=True))
                selected_id = id

            else:
                options.append(Option(str(id), title))
    if selected_media is None:
        select = [
            Select(
                options,
                custom_id=PLEX_REQUEST_ID,
            ),
            [
                Button("Abort", custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red),
            ],
        ]
    else:
        select = [
            Select(
                options,
                custom_id=PLEX_REQUEST_ID,
            ),
            [
                Button("Request", custom_id=PLEX_REQUEST_REQUEST, style=ButtonStyle.green),
                Button("Abort", custom_id=PLEX_REQUEST_ABORT, style=ButtonStyle.red),
            ],
        ]
    return select


@Kiruha.interactions(is_global=True, name="plex-request")
async def initiate_plex_request(client,
                                event, media_type: (MEDIA_TYPES, "Pick Media Type"),
                                media: ("str", 'Enter the media to search for')
                                ):
    if media_type == "tv":
        media_search = OverseerrTvSearch()
    elif media_type == "movie":
        media_search = OverseerrMovieSearch()
    else:
        return abort(f"Something went wrong with the search: {media_type} {media}")

    results = await media_search.get_search_results(media, media_type)
    if len(results) == 0:
        return abort(f"No results found for {media}!")
    global_results[event.user_id] = results  # use user_id as key
    instances[event.user_id] = media_search

    embed = Embed(f'Requesting {media}')
    embed.description = 'Please select your desired media from the list below'
    select = build_embed_list(results, selected_media=None)
    return InteractionResponse(embed=embed, components=select)


@Kiruha.interactions(custom_id=[PLEX_REQUEST_REQUEST, PLEX_REQUEST_ID])
async def handle_media_selection(event):
    # Only allow the original interaction user to interact with the buttons
    if event.message.interaction.user_id != event.user_id:
        return

    selected_media_list = event.values

    # Ensure valid media selection
    if not selected_media_list:
        return

    media_search = instances.get(event.user_id)  # Retrieve the cached media_search instance
    selected_media = selected_media_list[0]
    media_list = media_search.get_media_list()

    last_selected_media[event.user_id] = selected_media  # Store the last selected media

    # Rebuild the selection list
    select = build_embed_list(media_list, selected_media=selected_media)

    # Fetch detailed media info using cache mechanism
    for element in media_list:
        if str(element["id"]) == str(selected_media):
            media_type = element["media_type"]
            break

    media_info = await media_search.get_media_info(media_type, selected_media)  # Cache used here

    # Handle media poster image
    if media_info["posterPath"] is None:
        url = "https://www.niwrc.org/sites/default/files/images/resource/missing_persons_flyer.jpeg"
    else:
        url = tmdb_image_url + media_info["posterPath"]

    # Create embed with media information
    embed = Embed(f'{media_info["title"]} ({media_info["year"].split("-")[0]})')
    embed.add_image(url)
    embed.description = f'{media_info["overview"]} \n'

    yield InteractionResponse(embed=embed, components=select)


@Kiruha.interactions(custom_id=[PLEX_REQUEST_REQUEST])
async def send_plex_request(client, event):
    ic(event)
    # Allow closing for the source user
    if event.user is not event.message.interaction.user:
        return
    overseer_instance = OverseerrSearch()
    overseer_id = await overseer_instance.discord_user_to_overseerr_user(
        event.user_id)  # media_search = instances.get(event.user_id)

    # Retrieve the last selected media for this user
    selected_media = last_selected_media.get(event.user_id)
    media_search = instances.get(event.user_id)  # Retrieve the cached media_search instance
    media_list = media_search.get_media_list()
    # ic the last selected media value for debugging
    ic(f"Last selected media: {selected_media}")

    for element in media_list:
        if str(element["id"]) == str(selected_media):
            media_type = element["media_type"]
            break

    media_info = await media_search.get_media_info(media_type, selected_media)
    request = await overseer_instance.request_selected_media(media_type, selected_media, overseer_id)

    # Handle media poster image
    if media_info["posterPath"] is None:
        url = "https://www.niwrc.org/sites/default/files/images/resource/missing_persons_flyer.jpeg"
    else:
        url = tmdb_image_url + media_info["posterPath"]

    # Create embed with media information
    embed = Embed(f'Request sent for: {media_info["title"]} ({media_info["year"].split("-")[0]})', color=0x9c5db3)
    embed.add_thumbnail(url)
    embed.description = f'{media_info["overview"]} \n'
    embed.add_field("Requested By", event.user.name, True)
    embed.add_field("Request Status", "Processing", True)
    embed.add_field("Total Requests", request.get('requestedBy', {}).get('requestCount'), True)

    return InteractionResponse(embed, components=None)


@Kiruha.interactions(custom_id=[PLEX_REQUEST_ABORT])
async def abort_plex_request(client, event):
    # Allow closing for the source user
    if event.user is not event.message.interaction.user:
        return

    # We can use `yield` as well for acknowledging it.
    await client.interaction_component_acknowledge(event)
    await client.interaction_response_message_delete(event)


@Kiruha.interactions(is_global=True)
async def get_overseerr_id(event,
                           user: ('user', 'To who?'),
                           ):
    overseer_instance = OverseerrSearch()
    overseerr_id = await overseer_instance.discord_user_to_overseerr_user(user.id)
    if overseerr_id == 34:
        return 'This user does not have his DiscordID mapped to Overseerr'
    return f'The Overseer ID for {user:f} is: {overseerr_id}'
