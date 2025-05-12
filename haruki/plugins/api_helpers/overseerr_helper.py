import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from typing import Optional, Dict
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
    extra: Dict = field(default_factory=dict)  

class OverseerrHelper:
    USER_CACHE_TTL = 3600  # seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF = [0.5, 1, 2]

    def __init__(self, client):
        self.client = client
        self.cache: Dict[str, MediaSummary] = {}
        self.user_map_cache: Dict[int, Tuple[int, float]] = {}

    async def _api_request(self, method: str, endpoint: str, params: Optional[Dict] = None, payload: Optional[Dict] = None) -> dict:
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
        from time import time
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
                settings = await self._api_request("GET", f"user/{overseerr_id}/settings/notifications")
                mapped = settings.get("discordId")
                try:
                    if mapped is not None and int(mapped) == discord_id:
                        self.user_map_cache[discord_id] = (overseerr_id, time())
                        return overseerr_id
                except (TypeError, ValueError):
                    continue
            skip += 100
        return None

    async def search(self, query: str, media_type: str) -> List[MediaSummary]:
        params = {"page": 1, "language": "en", "query": quote_plus(query)}
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

        # Extract requester IDs from mediaInfo.requests
        media_info = raw.get("mediaInfo", {})
        requests = media_info.get("requests", [])


        detail = MediaSummary(
            id=raw.get("id"),
            title=raw.get("title") if media_type == "movie" else raw.get("name"),
            year=(raw.get("releaseDate") or raw.get("firstAirDate") or "")[:4],
            media_type=media_type,
            overview=raw.get("overview", ""),
            poster_path=raw.get("posterPath"),
        )

        self.cache[key] = detail
        print(detail)
        return detail


    async def is_already_requested(self, media_type: str, media_id: int) -> bool:
        raw = await self._api_request("GET", f"{media_type}/{media_id}", params={"language": "en"})
        return bool(raw.get("mediaInfo", {}).get("status") in {1, 2, 3, 4, 5})

    async def get_media_status(self, media_type: str, media_id: int) -> Optional[int]:
        try:
            raw = await self._api_request("GET", f"{media_type}/{media_id}", params={"language": "en"})
            media_info = raw.get("mediaInfo")
            if media_info:
                return media_info.get("status")
            return None
        except RuntimeError as e:
            if "API error 404" in str(e):
                return None
            raise

    async def user_has_requested(self, media_id: int, user_id: int) -> bool:
        page = 1
        while True:
            params = {"take": 50, "filter": "all", "page": page}
            raw = await self._api_request("GET", "request", params=params)
            results = raw.get("results", [])
            if not results:
                break

            for req in results:
                media = req.get("media") or {}
                if media.get("id") == media_id and req.get("requestedBy", {}).get("id") == user_id:
                    return True

            if len(results) < 50:
                break
            page += 1

        return False

    async def request_media(self, media_type: str, media_id: int, overseerr_user_id: int) -> dict:
        payload = {
            "mediaType": media_type,
            "mediaId": media_id,
            "userId": overseerr_user_id,
            "seasons": "all",
        }
        return await self._api_request("POST", "request", payload=payload)
