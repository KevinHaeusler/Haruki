__all__ = ("Kiruha",)

from hata import Client

from ..constants import KIRUHA_TOKEN


Kiruha = Client(
    KIRUHA_TOKEN,
    extensions=["slash"],
)
