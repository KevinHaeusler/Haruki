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


def process_episode_params(data):
    return data[0], data[1], data[2], data[3], data[4]


def process_movie_params(data):
    return data[0], data[1], data[4]


class StatisticInfo:
    __slots__ = 'stat_id'

    def __init__(self, stat_id):
        self.stat_id = stat_id

    @classmethod
    def from_data(cls, data):
        return cls(data.get('stat_id', ''))


class StatsInfo:
    __slots__ = ('stat_id', 'stat_title', 'title')

    def __init__(self, stat_id, stat_title, title):
        self.stat_id = stat_id
        self.stat_title = stat_title
        self.title = title

    def iter_embed_field_values(self):
        yield 'Stat', self.stat_id, True
        yield 'Stat Title', self.stat_title, True
        yield 'Title', self.title, True

    @classmethod
    def from_data(cls, stat, stat_title, title):
        return cls(stat, stat_title, title)


def process_top_movie_params(data):
    return data[0], data[1], data[2]


# shared: title, year, thumb, media_type
# Popular: title, year, users_watched, total_plays, thumb, media_type
# Top: title, year, total_plays, total_duration, thumb, media_type
# last_watched: user, user_id, title, year, media_type
# top_libraries: total_plays, total_duration, section_name, title, year, media_type, thumb
# top_users: user, userid, total_plays, total_duration, title, year, thumb, media_type


# top_platforms; platform

media_type_to_class = {
    'track':   (MusicActivityInfo.from_data, process_track_params),
    'episode': (TVShowActivityInfo.from_data, process_episode_params),
    'movie':   (TVMovieActivityInfo.from_data, process_movie_params),
}

stat_id_to_class = {
    'top_movies': (StatsInfo.from_data, process_top_movie_params),
    'popular_movies': (StatsInfo.from_data, process_top_movie_params),
}


async def make_api_call(client, api_call):
    url = f"{TAUTULLI_URL}/api/v2?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data


async def get_activity_info(client):
    response = await make_api_call(client, 'get_activity&time_range=365')
    if response is None or not response.get('response', {}).get('data', {}).get('sessions'):
        return abort('No active sessions.')

    activity_info = []
    sessions = response['response']['data']['sessions']
    for session in sessions:
        if not isinstance(session, dict):
            continue
        activity_info.append(_process_session_info(session))
    return activity_info


def _process_session_info(session):
    user = session.get('user', 'Unknown User')
    quality_profile = session.get('quality_profile', '')
    grandparent_title = session.get('grandparent_title', '')
    parent_title = session.get('parent_title', '')
    title = session.get('title', 'Unknown Title')
    media_type = session.get('media_type', '')

    data = [user, quality_profile, grandparent_title, parent_title, title]
    if media_type not in media_type_to_class:
        raise ValueError(f'Unknown media type: {media_type}')

    ActivityClass, params_processor = media_type_to_class[media_type]
    return ActivityClass(*params_processor(data))


async def get_stats_info(client, stat):
    response = await make_api_call(client, 'get_home_stats')
    if response is None or not response.get('response', {}).get('data', {}):
        return abort('No stats available.')

    stats_info = []
    stats_data = response['response']['data']
    for stats in stats_data:
        if not isinstance(stats, dict):
            continue
        stats_info.append(_process_stats_info(stats))
    return stats_info


def _process_stats_info(stats):
    stat_id = stats.get('stat_id', '')
    stat_title = stats.get('stat_title', '')

    rows = stats.get('rows', [])
    if not rows:
        return None

    stats_info_list = []  # to store all the statisticInfos

    for row in rows:  # rows is a list here, looping over it to get each dictionary
        title = row.get('title', '')  # get the title from each dictionary
        data = [stat_id, stat_title, title]

        if stat_id in stat_id_to_class:
            StatsClass, params_processor = stat_id_to_class[stat_id]
            stats_info_list.append(StatsClass(*params_processor(data)))
        else:
            print(f"Warning: {stat_id} does not exist in stat_id_to_class")

    return stats_info_list
