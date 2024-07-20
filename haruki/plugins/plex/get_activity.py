__all__ = ()

from hata import Embed, EmbedField

from haruki.bots import Kiruha
from .tautulli_api import get_activity_info


@Kiruha.interactions(is_global=True)
async def plex_activity(client):
    embed = await build_activity_embed(client)
    return embed


async def build_activity_embed(client):
    activity_infos = await get_activity_info(client)
    embeds = []
    TRIPLE_GRAVE = '`' * 3

    for activity_info in activity_infos:
        embed = Embed("Active Plex Session")

        for name, value, inline in activity_info.iter_embed_field_values():
            embed.add_field(name, f'{TRIPLE_GRAVE}\n{value}\n{TRIPLE_GRAVE}', inline)

        embed.add_image('https://i.imgur.com/BABpmZ3.png')
        embeds.append(embed)

    return embeds
