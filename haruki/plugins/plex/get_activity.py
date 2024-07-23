__all__ = ()

from hata import Embed, Color

from ...bots import Kiruha
from .tautulli_api import get_activity_info

media_type_to_color = {
    "MusicActivityInfo": Color(0x3498DB),  # Blue
    "TVShowActivityInfo": Color(0x2ECC71),  # Green
    "TVMovieActivityInfo": Color(0xE74C3C),  # Red
}


@Kiruha.interactions(is_global=True)
async def plex_activity(client):
    embed = await build_activity_embed(client)
    return embed


async def build_activity_embed(client):
    activity_infos = await get_activity_info(client)
    embeds = []
    TRIPLE_GRAVE = "`" * 3

    for activity_info in activity_infos:
        media_type = activity_info.__class__.__name__
        color = media_type_to_color.get(media_type, Color(0xFFFFFF))
        embed = Embed("Active Plex Session", color=color)

        for name, value, inline in activity_info.iter_embed_field_values():
            embed.add_field(name, f"{TRIPLE_GRAVE}\n{value}\n{TRIPLE_GRAVE}", inline)

        embed.add_image("https://i.imgur.com/BABpmZ3.png")
        embeds.append(embed)

    return embeds
