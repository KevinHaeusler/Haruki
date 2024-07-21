from hata.ext.slash import abort

from ...constants import TAUTULLI_TOKEN, TAUTULLI_URL


class ActivityInfo:
    __slots__ = ('user', 'quality')

    def __init__(self, user, quality):
        self.user = user
        self.quality = quality

    def iter_embed_field_values(self):
        yield 'User', self.user, True
        yield 'Quality', self.quality, True


class TVShowActivityInfo(ActivityInfo):
    __slots__ = ('show', 'season', 'episode')

    def __init__(self, user, quality, show, season, episode):
        ActivityInfo.__init__(self, user, quality)
        self.show = show
        self.season = season
        self.episode = episode

    def iter_embed_field_values(self):
        yield from ActivityInfo.iter_embed_field_values(self)
        yield 'Show', self.show, False
        yield 'Season', self.season, False
        yield 'Episode', self.episode, False

    @classmethod
    def from_data(cls, user, quality_profile, grandparent_title, parent_title, title):
        return cls(user, quality_profile, grandparent_title, parent_title, title)


class TVMovieActivityInfo(ActivityInfo):
    __slots__ = 'movie'

    def __init__(self, user, quality, movie):
        ActivityInfo.__init__(self, user, quality)
        self.movie = movie

    def iter_embed_field_values(self):
        yield from ActivityInfo.iter_embed_field_values(self)
        yield 'Movie', self.movie, False

    @classmethod
    def from_data(cls, user, quality_profile, title):
        return cls(user, quality_profile, title)


class MusicActivityInfo(ActivityInfo):
    __slots__ = ('artist', 'album', 'song')

    def __init__(self, user, quality, artist, album, song):
        ActivityInfo.__init__(self, user, quality)
        self.artist = artist
        self.album = album
        self.song = song

    def iter_embed_field_values(self):
        yield from ActivityInfo.iter_embed_field_values(self)
        yield 'Artist', self.artist, False
        yield 'Album', self.album, False
        yield 'Song', self.song, False

    @classmethod
    def from_data(cls, user, quality_profile, grandparent_title, parent_title, title):
        return cls(user, quality_profile, grandparent_title, parent_title, title)


def process_track_params(data):
    return data[0], data[1], data[2], data[3], data[4]


# Function to prepare parameters for TVShowActivityInfo
def process_episode_params(data):
    return data[0], data[1], data[2], data[3], data[4]


# Function to prepare parameters for TVMovieActivityInfo
def process_movie_params(data):
    return data[0], data[1], data[4]


media_type_to_class = {
    'track':   (MusicActivityInfo.from_data, process_track_params),
    'episode': (TVShowActivityInfo.from_data, process_episode_params),
    'movie':   (TVMovieActivityInfo.from_data, process_movie_params),
}


async def get_activity_info(client):
    response = await make_api_call(client, 'get_activity')

    if response is None or not response.get('response', {}).get('data', {}).get('sessions'):
        return abort('No active sessions.')

    activity_info = []
    sessions = response['response']['data']['sessions']

    for session in sessions:

        if not isinstance(session, dict):
            continue

        user = session.get('user', 'Unknown User')
        quality_profile = session.get('quality_profile', '')
        grandparent_title = session.get('grandparent_title', '')
        parent_title = session.get('parent_title', '')
        title = session.get('title', 'Unknown Title')
        media_type = session.get('media_type', '')

        # Collect all data for the from_data method into a list.
        data = [user, quality_profile, grandparent_title, parent_title, title]

        if media_type not in media_type_to_class:
            return abort(f'Unknown media type: {media_type}')

        ActivityClass, params_processor = media_type_to_class[media_type]
        session_info = ActivityClass(*params_processor(data))

        activity_info.append(session_info)

    return activity_info


async def make_api_call(client, api_call):
    url = f"{TAUTULLI_URL}/api/v2?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data
