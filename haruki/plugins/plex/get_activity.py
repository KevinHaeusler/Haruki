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

    for activity_info in activity_infos:
        if 'Artist' in activity_info:
            embed = Embed(
                title="Active Plex Session",
                fields=[
                    EmbedField(
                        'Activity Details for: ',
                        f'{block("User", activity_info["User"])}'
                        f'{block("Artist", activity_info["Artist"])}'
                        f'{block("Album", activity_info["Album"])}'
                        f'{block("Song", activity_info["Song"])}'
                        f'{block("Quality", activity_info["Quality"])}',
                        inline=True,
                    )
                ]
            )
        else:
            embed = Embed(
                title="Active Plex Session",
                fields=[
                    EmbedField(
                        'Activity Details for: ',
                        f'{block("User", activity_info["User"])}'
                        f'{block("Show", activity_info["Show"])}'
                        f'{block("Season", activity_info["Season"])}'
                        f'{block("Episode", activity_info["Episode"])}'
                        f'{block("Quality", activity_info["Quality"])}',
                        inline=True,
                    )
                ]
            )
        embeds.append(embed)

    return embeds


def block(title, value):
    t = '`' * 3
    return f'**{title}**\n{t}\n{value}\n{t}'
