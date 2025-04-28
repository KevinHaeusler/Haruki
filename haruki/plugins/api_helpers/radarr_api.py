import json
from icecream import ic
from haruki.constants import RADARR_TOKEN, RADARR_URL

async def get_from_radarr_api(client, api_call):
    headers = {"x-api-key": RADARR_TOKEN, "accept": "application/json"}
    url = f"{RADARR_URL}/api/v3/{api_call}"
    ic(f"GET {url}")
    async with client.http.get(url, headers=headers) as response:
        api_response = await response.json()
        ic(api_response)
        return api_response

async def post_to_radarr_api(client, api_call, payload):
    headers = {"x-api-key": RADARR_TOKEN, "content-type": "application/json", "accept": "application/json"}
    url = f"{RADARR_URL}/api/v3/{api_call}"
    ic(f"POST {url} Payload:", payload)
    async with client.http.post(url, headers=headers, data=json.dumps(payload)) as response:
        api_response = await response.json()
        ic(api_response)
        return api_response

async def put_to_radarr_api(client, api_call, payload):
    headers = {"x-api-key": RADARR_TOKEN, "content-type": "application/json", "accept": "application/json"}
    url = f"{RADARR_URL}/api/v3/{api_call}"
    ic(f"PUT {url} Payload:", payload)
    async with client.http.put(url, headers=headers, data=json.dumps(payload)) as response:
        api_response = await response.json()
        ic(api_response)
        return api_response
