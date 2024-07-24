__all__ = ()

from io import BytesIO
from typing import Annotated
from PIL import Image

from hata import Embed
from hata.ext.slash import P, abort

from .tautulli_api import get_stats_info
from ...bots import Kiruha
from ...constants import TAUTULLI_IMAGE

STAT_CHOICES = {
    "movies": 0,
    "tv": 2,
    "music": 4,
}

STAT_SPECIFICATION = {"top": 0, "popular": 1}

TITLE = {0: "Most Watched Movie",
         1: "Most Popular Movie",
         2: "Most Watched TV Series",
         3: "Most Popular TV Series",
         4: "Most Played Artist",
         5: "Most Popular Artist", }


@Kiruha.interactions(is_global=True)
async def plex_stats(
        client,
        event,
        stat_choice: (STAT_CHOICES, "Pick which stats you want to see"),
        stat_specification: (STAT_SPECIFICATION, "Choose which stats you want to see"),
        results: Annotated[int, P('int', 'How many results?', min_value=1, max_value=10)] = 3,
        days: Annotated[int, P('int', 'From how many days?', min_value=1, max_value=1000)] = 30,
):
    print(event.channel.id)
    yield
    messages = await build_activity_embed(client, event, stat_choice, stat_specification, results, days)
    for message in messages:
        yield message


async def build_activity_embed(client, event, stat_choice, stat_specification, results, days):
    data_index = stat_choice + stat_specification
    stat_infos = await get_stats_info(client, data_index, results, days)
    messages = []
    count = 1

    for info in stat_infos:
        async with Kiruha.http.get(f'{TAUTULLI_IMAGE}{info.thumb}/pms_image_proxy.png') as response:
            if response.status == 200:
                data = await response.read()
            else:
                data = None

        if data is None:
            return abort("Oopsie Woopsie")
        else:
            image = Image.open(BytesIO(data))
            image.save(f'thumb_{count}.png', "PNG")
            image_url = f'attachment://thumb_{count}.png'
            embed = Embed(
                f'#{count} {TITLE[data_index]} in the last {days} days'
            )
            embed.add_image(image_url)
            for name, value, inline in info.iter_embed_field_values():
                embed.add_field(name, f"```\n{value}\n```", inline)
            # embed.add_image(f'{TAUTULLI_IMAGE}{info.thumb}')
            print(f'{TAUTULLI_IMAGE}{info.thumb}')
            messages.append(await Kiruha.message_create(event.channel.id, embed, file=(f'thumb_{count}.png', data)))
            # embeds.append(embed)
            count += 1

    return messages
