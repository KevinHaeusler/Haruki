import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from scarletio import sleep
from urllib.parse import quote_plus
from ...constants import OVERSEER_URL, OVERSEER_TOKEN

@dataclass
class MediaSummary:
    id: int
    title: str
    year: str
    media_type: str
    overview: str
    poster_path: str

class OverseerrHelper:
    """
    A helper client for interacting with the Overseerr API.
    Provides methods to search media, fetch details, request media,
    and map Discord user IDs to Overseerr user IDs.
    """

    # Cache and retry settings
    USER_CACHE_TTL = 3600  # seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF = [0.5, 1, 2]

    def __init__(self, client):
        self.client = client
        # media and detail cache: {"{media_type}_{id}": MediaSummary}
        self.cache: Dict[str, MediaSummary] = {}
        # discord->overseerr user id cache: {discord_id: (overseerr_id, timestamp)}
        self.user_map_cache: Dict[int, Tuple[int, float]] = {}

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        payload: Optional[Dict] = None,
    ) -> dict:
        headers = {
            "x-api-key": OVERSEER_TOKEN,
            "accept": "application/json",
            "content-type": "application/json",
        }
        url = f"{OVERSEER_URL}/api/v1/{endpoint.lstrip('/')}"
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                if method.upper() == "GET":
                    resp = await self.client.http.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    resp = await self.client.http.post(url, headers=headers, data=json.dumps(payload))
                else:
                    raise ValueError(f"Unsupported HTTP method {method}")

                # Retry on specific status codes
                if resp.status == 400 and attempt < self.MAX_RETRIES - 1:
                    await sleep(self.RETRY_BACKOFF[attempt])
                    continue

                if resp.status < 200 or resp.status >= 300:
                    raise RuntimeError(f"API error {resp.status} on {method} {endpoint}")

                return await resp.json()

            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    await sleep(self.RETRY_BACKOFF[attempt])

        raise last_error


    async def discord_user_to_overseerr_user(self, discord_id: int) -> Optional[int]:
        """
        Map a Discord user ID to an Overseerr user ID by scanning all users.
        Caches results for USER_CACHE_TTL seconds.
        """
        from time import time
        # check cache
        cached = self.user_map_cache.get(discord_id)
        if cached:
            overseerr_id, ts = cached
            if time() - ts < self.USER_CACHE_TTL:
                return overseerr_id

        skip = 0
        while True:
            params = {"take": 100, "skip": skip}
            raw = await self._api_request("GET", "user", params=params)
            users = raw.get("results", [])
            if not users:
                break
            for user in users:
                overseerr_id = user.get("id")
                settings = await self._api_request(
                    "GET", f"user/{overseerr_id}/settings/notifications"
                )
                mapped = settings.get("discordId")
                try:
                    if mapped is not None and int(mapped) == discord_id:
                        # cache and return
                        self.user_map_cache[discord_id] = (overseerr_id, time())
                        return overseerr_id
                except (TypeError, ValueError):
                    continue
            skip += 100
        return None

    async def search(self, query: str, media_type: str) -> List[MediaSummary]:
        """
        Search Overseerr for media of given type ('movie' or 'tv').
        Returns a list of MediaSummary objects.
        """
        params = {
        "page": 1,
        "language": "en",
        "query": quote_plus(query)
        }
        raw = await self._api_request("GET", "search", params=params)
        results: List[MediaSummary] = []
        for item in raw.get("results", []):
            if item.get("mediaType") != media_type:
                continue
            summary = MediaSummary(
                id=item.get("id"),
                title=(item.get("title") or item.get("name") or "")[:30],
                year=(item.get("releaseDate") or item.get("firstAirDate") or "")[:4],
                media_type=media_type,
                overview=item.get("overview", ""),
                poster_path=item.get("posterPath"),
            )
            if summary.overview and summary.year:
                results.append(summary)
                self.cache[f"{media_type}_{summary.id}"] = summary
        return results

    async def get_media_info(self, media_type: str, media_id: int) -> MediaSummary:
        """
        Get detailed media info, using cache if available.
        """
        key = f"{media_type}_{media_id}"
        if key in self.cache:
            return self.cache[key]
        raw = await self._api_request("GET", f"{media_type}/{media_id}", params={"language": "en"})
        detail = MediaSummary(
            id=raw.get("id"),
            title=raw.get("title") if media_type == "movie" else raw.get("name"),
            year=(raw.get("releaseDate") or raw.get("firstAirDate") or "")[:4],
            media_type=media_type,
            overview=raw.get("overview", ""),
            poster_path=raw.get("posterPath"),
        )
        self.cache[key] = detail
        return detail
    
    async def is_already_requested(self, media_type: str, media_id: int) -> bool:
        raw = await self._api_request("GET", f"{media_type}/{media_id}", params={"language": "en"})
        print(f"Checking if already requested: {media_type}/{media_id}")
        print(raw)
        return bool(raw.get("mediaInfo", {}).get("status") in {1, 2, 3, 4, 5})


    async def get_media_status(self, media_type: str, media_id: int) -> Optional[int]:
        """
        Fetch current media status. Returns status 1–6 or None if not found.
        """
        try:
            raw = await self._api_request("GET", f"{media_type}/{media_id}", params={"language": "en"})
            media_info = raw.get("mediaInfo")
            if media_info:
                return media_info.get("status")
            return None  # Not yet requested
        except RuntimeError as e:
            if "API error 404" in str(e):
                return None
            raise




    async def request_media(self, media_type: str, media_id: int, overseerr_user_id: int) -> dict:
        """
        Send a media request on behalf of a user.
        """
        payload = {
            "mediaType": media_type,
            "mediaId": media_id,
            "userId": overseerr_user_id,
            "seasons": "all",
        }
        return await self._api_request("POST", "request", payload=payload)
