from icecream import ic

from haruki.constants import SONARR_TOKEN, SONARR_URL


async def post_data_to_sonarr_api(client, api_call):
    ic()
    headers = {"x-api-key": SONARR_TOKEN, "content-type": "application/x-www-form-urlencoded", "accept": "*/*"}
    url = f"{SONARR_URL}/api{api_call}"
    ic(url)
    async with client.http.post(url, headers) as response:
        api_response = await response.json()
        ic(api_response)
    return api_response


async def get_data_from_sonarr_api(client):
    ic()
    headers = {"x-api-key": SONARR_TOKEN, "content-type": "application/json"}
    url = f"{SONARR_URL}/api"
    async with client.http.get(url, headers) as response:
        api_response = await response.json()
        ic(api_response)
    return api_response


async def check_indexers(client):
    ic()
    api_response = await post_data_to_sonarr_api(client, "/v3/indexer/testall")
    
    return api_response
