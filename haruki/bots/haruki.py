# bots/haruki.py

__all__ = ("Haruki",)

from hata import Client
from scarletio import create_task, sleep
from ..constants import HARUKI_TOKEN

Haruki = Client(
    HARUKI_TOKEN,
    extensions=["slash"],
)


@Haruki.events
async def ready(client):
    print(f'{client:f} is ready!')
