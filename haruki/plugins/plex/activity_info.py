__all__ = ()

from dataclasses import dataclass


@dataclass(slots=True)
class ActivityInfo:
    user: str
    quality: str

    def iter_embed_field_values(self):
        yield "User", self.user, True
        yield "Quality", self.quality, True


@dataclass(slots=True)
class TVShowActivityInfo(ActivityInfo):
    show: str
    season: str
    episode: str

    def iter_embed_field_values(self):
        yield from ActivityInfo.iter_embed_field_values(self)
        yield "Show", self.show, False
        yield "Season", self.season, False
        yield "Episode", self.episode, False

    @classmethod
    def from_list(cls, data):
        return cls(*data)


@dataclass(slots=True)
class TVMovieActivityInfo(ActivityInfo):
    movie: str

    def iter_embed_field_values(self):
        yield from ActivityInfo.iter_embed_field_values(self)
        yield "Movie", self.movie, False

    @classmethod
    def from_list(cls, data):
        return cls(*data[:2], data[4])


@dataclass(slots=True)
class MusicActivityInfo(ActivityInfo):
    artist: str
    album: str
    song: str

    def iter_embed_field_values(self):
        yield from ActivityInfo.iter_embed_field_values(self)
        yield "Artist", self.artist, False
        yield "Album", self.album, False
        yield "Song", self.song, False

    @classmethod
    def from_list(cls, data):
        return cls(*data)
