__all__ = ()

from hata import Embed, EmbedField

from .tautulli_api import get_stats_info
from ...bots import Kiruha

STAT_CHOICES = [
    'tv',
    'movies',
    'music',
]

STAT_SPECIFICATION = [
    'top',
    'popular'
]


@Kiruha.interactions(is_global=True)
async def plex_stats(
        client,
        stat_choice: (STAT_CHOICES, 'Pick which stats you want to see'),
        stat_specification: (STAT_SPECIFICATION, 'Choose which stats you want to see'),
):
    embed = await build_activity_embed(client, stat_choice, stat_specification)
    return embed


async def build_activity_embed(client, stat_choice, stat_specification):
    stat_infos = await get_stats_info(client, stat_choice)

    # Flatten stat_infos to ensure we're dealing with StatsInfo instances
    flat_stat_infos = [item for sublist in stat_infos for item in sublist]
    if True:
        return await build_movies_embed(flat_stat_infos, stat_specification)

async def build_movies_embed(flat_stat_infos, stat_specification):
    fields = []
    counter = 0
    for stat_info in flat_stat_infos:
        if stat_info is None:
            continue

        if stat_specification in stat_info.stat_id:
            counter += 1
            field_data = ""
            for name, value, inline in list(stat_info.iter_embed_field_values())[2:]:
                field_data += f'{name}: \t\t{value}\n'

            fields.append(
                EmbedField(
                    f'#{counter} {"Most Watched" if stat_specification == "top" else "Most Popular"} Movie', field_data,
                    False
                )
            )

    embed = Embed(description=f'{stat_specification.title()}', fields=fields)
    embed.add_image('https://i.imgur.com/BABpmZ3.png')

    return embed
