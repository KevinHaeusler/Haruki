import urllib.parse

from icecream import ic

from ...constants import OVERSEER_URL, OVERSEER_TOKEN


async def make_api_call(client, media, api_call):
    ic()
    params = {
        "page": 1,
        "language": "en",
        "query": urllib.parse.quote(media),
    }
    headers = {"x-api-key": OVERSEER_TOKEN, "content-type": "application/json"}
    url = f"{OVERSEER_URL}/api/v1{api_call}"
    async with client.http.get(url, headers, params=params) as response:
        api_response = await response.json()
    return api_response
