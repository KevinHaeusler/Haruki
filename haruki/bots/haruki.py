__all__ = ("Haruki",)

from hata import Client

from ..constants import HARUKI_TOKEN


Haruki = Client(
    HARUKI_TOKEN,
    extensions=["slash"],
)
