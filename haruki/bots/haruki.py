# bots/haruki.py

__all__ = ("Haruki",)

from hata import Client
from scarletio import create_task, sleep
from ..constants import HARUKI_TOKEN, UPTIME_KUMA_URL

Haruki = Client(
    HARUKI_TOKEN,
    extensions=["slash"],
)

async def ping_uptime_service(client):
    url = UPTIME_KUMA_URL
    
    while True:
        try:
            async with client.http.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        print('[Haruki] Uptime Kuma Ping successful: ok=true')
                    else:
                        print('[Haruki] Uptime Kuma Ping responded, but not ok')
                else:
                    print(f'[Haruki] Uptime Kuma Ping failed with status: {resp.status}')
        except Exception as e:
            print(f'[Haruki] Uptime Kuma Ping error: {e}')
        
        await sleep(60.0)



@Haruki.events
async def ready(client):
    print(f'{client:f} is ready!')
    create_task(ping_uptime_service(client))
