from dataclasses import dataclass
from typing import Optional

SECTION_ID_MAPPING = {1: "TV Movie", 8: "TV Show", 5: "Music"}


@dataclass(slots=True)
class StatsInfo:
    data_index: int
    title: str
    year: int
    users_watched: int
    rating_key: int
    grandparent_rating_key: str
    last_play: int
    total_plays: int
    grandparent_thumb: str
    thumb: str
    art: str
    section_id: int
    media_type: str
    content_rating: str
    labels: list
    user: str
    friendly_name: str
    platform: str
    live: int
    guid: str
    row_id: int
    total_duration: Optional[int] = None  # <-- this field is optional now

    @classmethod
    def from_row(cls, row: dict, data_index: int):
        return cls(**row, data_index=data_index)

    def get_section(self):
        return SECTION_ID_MAPPING.get(self.section_id, "Unknown")

    def iter_embed_field_values(self):
        """Form data for custom embedding."""
        yield "Title", self.title, True
        yield "Year", self.year, True
        yield "Library", self.get_section(), False
        if self.data_index % 2 == 0:  # even index
            yield "Total Duration", self.total_duration, True
        else:
            yield "Users Watched", self.users_watched, True
        yield "Total Plays", self.total_plays, True
