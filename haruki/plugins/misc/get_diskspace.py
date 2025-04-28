__all__ = ()

from icecream import ic

from ...bots import Kiruha
from ..api_helpers.sonarr_api import get_from_sonarr_api


@Kiruha.interactions(is_global=True, name="get-diskspace")
async def get_diskspace(client, event):
    ic(event)
    response = await get_from_sonarr_api(client, "diskspace")
    ic(response)

    for disk in response:
        if disk.get("path") == "/mnt/media":
            total = disk.get("totalSpace", 0)
            free = disk.get("freeSpace", 0)
            used = total - free

            # Convert bytes to TB
            used_tb = used / (1024 ** 4)
            total_tb = total / (1024 ** 4)

            return f"/mnt/media: {used_tb:.2f}TB / {total_tb:.2f}TB"

    return "Disk /mnt/media not found."