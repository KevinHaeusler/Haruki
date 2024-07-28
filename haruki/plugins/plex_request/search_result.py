__all__ = ()

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(slots=True)
class SearchResult:
    id: int
    year: str
    media_type: str
    name: str
    origin_country: str
    origin_language: str
    overview: str
    poster_path: str
    media_info: bool
    mi_download_status: str = None
    mi_id: int = None
    mi_tmdbId: int = None
    mi_tvdbId: int = None
    mi_imdbId: int = None
    mi_status: int = None
    mi_created_date: str = None
    mi_updated_date: str = None
    mi_lastSeasonChange: str = None
    mi_mediaAddedAt: str = None
    mi_plex_url: str = None
    seasons: List[Dict] = field(default_factory=list)

    def iter_embed_field_values(self):
        yield "ID", self.id, False
        yield "Year", self.year, False
        yield "MediaType", self.media_type, False
        yield "Name", self.name, False
        yield "Origin Country", self.origin_country, False
        yield "Origin Language", self.origin_language, False
        yield "Overview", self.overview, False

    @classmethod
    def from_list(cls, data):
        return cls(*data)
