from ...bots import Kiruha
from ...constants import OVERSEER_TOKEN, OVERSEER_URL

headers = {"x-api-key": OVERSEER_TOKEN, "content-type": "application/json"}


async def get_search_results(media_type, media):
    params = {
        "page":     1,
        "language": "en",
        "query":    media,
    }
    async with Kiruha.http.get(f'{OVERSEER_URL}/api/v1/search', headers, params=params) as response:
        api_response = await response.json()
    search_results = []
    for result in api_response.get('results', []):
        if result.get('mediaType') == media_type:
            if media_type == 'tv':
                search_result = {
                    "id":    result.get('id'),
                    "title": result.get('name'),
                    "year":  result.get('firstAirDate', '')[:4],
                }
            else:
                search_result = {
                    "id":    result.get('id'),
                    "title": result.get('title'),
                    "year":  result.get('releaseDate', '')[:4],

                }
            search_results.append(search_result)
    print(search_results)
    return search_results


async def get_media_info(media_type, media_id):
    params = {
        "language": "en",
    }
    async with Kiruha.http.get(f'{OVERSEER_URL}/api/v1/movie/{media_id}', headers, params=params) as response:
        print(response)
        api_response = await response.json()
        return api_response
