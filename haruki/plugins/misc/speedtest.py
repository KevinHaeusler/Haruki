__all__ = ()

from haruki.bots import Kiruha


@Kiruha.interactions(is_global=True, name="speedtest")
async def test_internet_speed():
    # TODO Download Speedtest Files, then calculate the time and speed and afterwards delete the file.
    return "todo"
