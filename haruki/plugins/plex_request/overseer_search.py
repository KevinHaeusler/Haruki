__all__ = ()

from json import dumps
import urllib.parse

from ...bots import Kiruha
from ...constants import OVERSEER_TOKEN, OVERSEER_URL


class MediaSearch:
    def __init__(self):
        self.headers = {"x-api-key": OVERSEER_TOKEN, "content-type": "application/json"}
        self.media_list = []

    async def get_search_results(self, media_type, media):
        params = {
            "page": 1,
            "language": "en",
            "query": urllib.parse.quote(media),
        }
        async with Kiruha.http.get(f"{OVERSEER_URL}/api/v1/search", self.headers, params=params) as response:
            api_response = await response.json()
        self.media_list = []
        print(api_response)
        for result in api_response.get("results", []):
            if result.get("mediaType") == media_type:
                if media_type == "tv":
                    search_result = {
                        "id": result.get("id"),
                        "title": result.get("name")[:30],
                        "year": result.get("firstAirDate", "")[:4],
                        "media_type": result.get("mediaType"),
                    }
                else:
                    search_result = {
                        "id": result.get("id"),
                        "title": result.get("title")[:30],
                        "year": result.get("releaseDate", "")[:4],
                        "media_type": result.get("mediaType"),
                    }
                self.media_list.append(search_result)
        return self.media_list

    async def get_selected_media_info(self, selected_id):
        for media in self.media_list:
            if media["id"] == selected_id:
                return await self.get_media_info(media["type"], selected_id)
        return None

    def get_media_list(self):
        return self.media_list

    async def get_media_info(self, media_type, media_id):
        params = {
            "language": "en",
        }
        async with Kiruha.http.get(
                f"{OVERSEER_URL}/api/v1/{media_type}/{media_id}", self.headers, params=params
        ) as response:
            api_response = await response.json()
            media_info = []

            if media_type == "tv":
                media_info = {
                    "id": api_response.get("id"),
                    "title": api_response.get("name"),
                    "year": api_response.get("firstAirDate", "")[:4],
                    "media_type": media_type,
                    "posterPath": api_response.get("posterPath"),
                    "genres": [genre["name"] for genre in api_response.get("genres", [])],
                    "overview": api_response.get("overview"),
                }
            else:
                media_info = {
                    "id": api_response.get("id"),
                    "title": api_response.get("title"),
                    "year": api_response.get("releaseDate", "")[:4],
                    "media_type": media_type,
                    "posterPath": api_response.get("posterPath"),
                    "genres": [genre["name"] for genre in api_response.get("genres", [])],
                    "overview": api_response.get("overview"),
                }

            return media_info

    async def request_selected_media(self, media_type, media_id):
        data = {
            "mediaType": media_type,
            "mediaId": int(media_id),
            "tvdbId": int(media_id),
            "seasons": "all",
            "is4k": False,
            "serverId": 0,
            "profileId": 0,
            "rootFolder": "string",
            "languageProfileId": 0,
            "userId": 0,
        }
        async with Kiruha.http.post(f"{OVERSEER_URL}/api/v1/request", self.headers, data=dumps(data)) as response:
            api_response = await response.json()
            print(api_response)
        return "yay"
