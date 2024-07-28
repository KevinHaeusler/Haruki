import urllib.parse

from hata.ext.slash import abort
from icecream import ic

from .search_result import SearchResult
from ...constants import OVERSEER_URL, OVERSEER_TOKEN


async def make_api_call(client, media_type, media, api_call):
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


def _process_search_result(result):
    media_type = result.get("mediaType")
    year = result.get("firstAirDate") if media_type == "tv" else result.get("releaseDate")
    name = result.get("name") if media_type == "tv" else result.get("title")

    resultData = [
        result.get("id"),
        year,
        media_type,
        name,
        result.get("originCountry"),
        result.get("originalLanguage"),
        result.get("overview"),
        result.get("posterPath"),
    ]
    media_info = result.get("mediaInfo", {})
    if media_info:
        resultData.append(True)
        resultData += [
            media_info.get("downloadStatus"),
            media_info.get("id"),
            media_info.get("tmdbId"),
            media_info.get("tvdbId"),
            media_info.get("imdbId"),
            media_info.get("status"),
            media_info.get("createdAt"),
            media_info.get("updatedAt"),
            media_info.get("lastSeasonChange"),
            media_info.get("mediaAddedAt"),
            media_info.get("plexUrl"),
        ]
        resultData.append([
            {'id': season.get("id"), 'number': season.get("seasonNumber"), 'status': season.get("status")}
            for season in media_info.get("seasons", [])  # Normalizing the season data
        ])
    else:
        resultData.append(False)
        resultData += [None] * 12  # Padding the resultData to align with SearchResult's dataclass structure

    return SearchResult.from_list(resultData)


async def search_media_by_name(client, media_type, media):
    ic()
    api_call = "/search"
    response = await make_api_call(client, media_type, media, api_call)
    if not response.get("results"):
        return abort(f"Did not find anything for {media}")
    results = response.get("results")
    search_results = []
    for result in results:
        if media_type == result.get("mediaType"):
            search_results.append(_process_search_result(result))
    ic(search_results)
    return response
