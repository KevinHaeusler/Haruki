__all__ = ()

from typing import Annotated

from hata import Embed
from hata.ext.slash import P

from .tautulli_api import get_stats_info
from ...bots import Kiruha

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
        stat_choice: (STAT_CHOICES, "Pick which stats you want to see"),
        stat_specification: (STAT_SPECIFICATION, "Choose which stats you want to see"),
        results: Annotated[int, P('int', 'How many results?', min_value=1, max_value=10)] = 3,
        days: Annotated[int, P('int', 'From how many days?', min_value=1, max_value=1000)] = 30,
):
    embed = await build_activity_embed(client, stat_choice, stat_specification, results, days)
    return embed


async def build_activity_embed(client, stat_choice, stat_specification, results, days):
    data_index = stat_choice + stat_specification
    stat_infos = await get_stats_info(client, data_index, results, days)
    embeds = []
    count = 1
    TRIPLE_GRAVE = "`" * 3

    for info in stat_infos:
        embed = Embed(
            f'#{count} {TITLE[data_index]} in the last {days} days'
        )
        for name, value, inline in info.iter_embed_field_values():
            embed.add_field(name, f"{TRIPLE_GRAVE}\n{value}\n{TRIPLE_GRAVE}", inline)
        embed.add_image("https://i.imgur.com/BABpmZ3.png")
        embeds.append(embed)
        count += 1

    return embeds
