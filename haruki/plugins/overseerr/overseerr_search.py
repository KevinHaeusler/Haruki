__all__ = ()

import urllib.parse

from icecream import ic

from ...bots import Kiruha
from ...constants import OVERSEER_TOKEN, OVERSEER_URL
import json
from scarletio import sleep


class OverseerrSearch:
    def __init__(self):
        self.headers = {"x-api-key": OVERSEER_TOKEN, "Content-Type": "application/json", "charset": "utf-8"}
        self.media_list = []
        self.cache = {}  # Cache to store media information

    async def get_search_results(self, media, media_type=None):
        params = {
            "page": 1,
            "language": "en",
            "query": urllib.parse.quote(media),
        }
        async with Kiruha.http.get(f"{OVERSEER_URL}/api/v1/search", self.headers, params=params) as response:
            api_response = await response.json()
        self.media_list = []
        self.process_search_results(api_response, media_type)
        return self.media_list

    async def get_users(self):
        params = {
            "take": 100,
        }
        async with Kiruha.http.get(f"{OVERSEER_URL}/api/v1/user", self.headers, params=params) as response:
            api_response = await response.json()
        return api_response.get("results")

    async def discord_user_to_overseerr_user(self, discord_id):
        for attempt in range(3):
            try:
                users = await self.get_users()
                for user in users:
                    try:
                        # Attempt to fetch and cast discord_id_mapped to int
                        discord_id_mapped = await self.get_discord_id_from_overseerr_id(user.get("id"))
                        if discord_id_mapped is None:
                            continue  # If discord_id_mapped is None, skip to the next user

                        # Convert to int and compare with discord_id
                        if int(discord_id_mapped) == discord_id:
                            return user.get("id")

                    except (TypeError, ValueError):
                        # If there's a casting issue, just skip to the next user
                        continue

                return 34  # Return default value if no user matches

            except ConnectionError:
                # Log the exception (or use an appropriate logging mechanism)
                print(f"Connection error occurred, retrying... ({attempt + 1}/{3})")
                await sleep(1)  # Introduce a delay before retrying

        # After retries, return a fallback value or raise an exception
        return None  # or raise an error if needed

    async def request_selected_media(self, media_type, selected_id, overseer_id, seasons=1):
        data = {
            "mediaType": media_type,
            "mediaId": int(selected_id),
            "userId": int(overseer_id),
            "seasons": "all"
        }

        encoded_data = json.dumps(data)
        async with Kiruha.http.post(f"{OVERSEER_URL}/api/v1/request", self.headers, data=encoded_data) as response:
            api_response = await response.json()
            ic(response.headers)
            ic(api_response)
        return api_response

    async def get_discord_id_from_overseerr_id(self, overseer_id):
        async with Kiruha.http.get(f"{OVERSEER_URL}/api/v1/user/{overseer_id}/settings/notifications",
                                   self.headers) as response:
            api_response = await response.json()
            discord_id = api_response.get("discordId")
            return discord_id

    def process_search_results(self, api_response, media_type):
        raise NotImplementedError("This method should be implemented by subclasses")

    async def get_selected_media_info(self, selected_id):
        for media in self.media_list:
            if media["id"] == selected_id:
                return await self.get_media_info(media["media_type"], selected_id)
        return None

    def get_media_list(self):
        return self.media_list

    async def get_media_info(self, media_type, media_id):
        # Check if the media info is already cached
        cache_key = f"{media_type}_{media_id}"
        if cache_key in self.cache:
            ic("Returning cached result")
            ic(self.cache[cache_key])
            return self.cache[cache_key]

        # Fetch media info from the API if not cached
        params = {
            "language": "en",
        }
        async with Kiruha.http.get(
                f"{OVERSEER_URL}/api/v1/{media_type}/{media_id}", self.headers, params=params
        ) as response:
            api_response = await response.json()
            ic(api_response)
            media_info = {
                "id": api_response.get("id"),
                "title": api_response.get("title") if media_type == "movie" else api_response.get("name"),
                "year": api_response.get("releaseDate", "")[:4] if media_type == "movie" else api_response.get(
                    "firstAirDate", "")[:4],
                "media_type": media_type,
                "posterPath": api_response.get("posterPath"),
                "overview": api_response.get("overview"),
            }

            # Cache the result
            self.cache[cache_key] = media_info
            ic("Media info cached")

            return media_info


class OverseerrMovieSearch(OverseerrSearch):
    def process_search_results(self, api_response, media_type="movie"):
        for result in api_response.get("results", []):
            if result.get("mediaType") == media_type:
                search_result = {
                    "id": result.get("id"),
                    "title": result.get("title")[:30],
                    "year": result.get("releaseDate", "")[:4],
                    "media_type": result.get("mediaType"),
                    "posterPath": result.get("posterPath"),
                    "overview": result.get("overview", ""),
                }
                # Check if 'year' or 'overview' is empty
                if not search_result["year"] or not search_result["overview"]:
                    continue  # Skip appending if either field is empty

                self.media_list.append(search_result)

                # Cache the media info immediately
                cache_key = f"{media_type}_{search_result['id']}"
                self.cache[cache_key] = search_result


class OverseerrTvSearch(OverseerrSearch):
    def process_search_results(self, api_response, media_type="tv"):
        for result in api_response.get("results", []):
            if result.get("mediaType") == media_type:
                search_result = {
                    "id": result.get("id"),
                    "title": result.get("name")[:30],
                    "year": result.get("firstAirDate", "")[:4],
                    "media_type": result.get("mediaType"),
                    "posterPath": result.get("posterPath"),
                    "overview": result.get("overview"),

                }

                self.media_list.append(search_result)

                # Cache the media info immediately
                cache_key = f"{media_type}_{search_result['id']}"
                self.cache[cache_key] = search_result
