import json
from ...constants import OVERSEER_URL, OVERSEER_TOKEN

async def get_from_overseerr_api(client, api_call, params=None):
    headers = {
        "x-api-key": OVERSEER_TOKEN,
        "accept": "application/json",
    }
    url = f"{OVERSEER_URL}/api/v1/{api_call.lstrip('/')}"
    async with client.http.get(url, headers=headers, params=params) as resp:
        return await resp.json()

async def post_to_overseerr_api(client, api_call, payload):
    headers = {
        "x-api-key": OVERSEER_TOKEN,
        "content-type": "application/json",
        "accept": "application/json",
    }
    url = f"{OVERSEER_URL}/api/v1/{api_call.lstrip('/')}"
    async with client.http.post(url, headers=headers, data=json.dumps(payload)) as resp:
        return await resp.json()
