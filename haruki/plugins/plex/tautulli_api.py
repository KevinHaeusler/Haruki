from hata.ext.slash import abort

from .activity_info import MusicActivityInfo, TVShowActivityInfo, TVMovieActivityInfo
from .stats_info import StatsInfo

from ...constants import TAUTULLI_TOKEN, TAUTULLI_URL

media_type_to_class = {
    "track": MusicActivityInfo.from_list,
    "episode": TVShowActivityInfo.from_list,
    "movie": TVMovieActivityInfo.from_list,
}


async def make_api_call(client, api_call):
    url = f"{TAUTULLI_URL}/api/v2?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data


async def get_activity_info(client):
    response = await make_api_call(client, "get_activity&time_range=365")
    if response is None or not response.get("response", {}).get("data", {}).get("sessions"):
        return abort("No active sessions.")

    activity_info = []
    sessions = response["response"]["data"]["sessions"]
    for session in sessions:
        if not isinstance(session, dict):
            continue
        activity_info.append(_process_session_info(session))
    return activity_info


def _process_session_info(session):
    user = session.get("user", "Unknown User")
    quality_profile = session.get("quality_profile", "")
    grandparent_title = session.get("grandparent_title", "")
    parent_title = session.get("parent_title", "")
    title = session.get("title", "Unknown Title")
    media_type = session.get("media_type", "")

    data = [user, quality_profile, grandparent_title, parent_title, title]
    if media_type not in media_type_to_class:
        raise ValueError(f"Unknown media type: {media_type}")

    ActivityClass = media_type_to_class[media_type]
    return ActivityClass(data)


async def get_stats_info(client, data_index):
    response = await make_api_call(client, "get_home_stats")

    if response is None or not response.get("response", {}).get("data", {}):
        return abort("No stats available.")

    stats_data = response["response"]["data"][data_index]  # directly select the relevant data

    return _process_stats_info(stats_data, data_index)


def _process_stats_info(stat_data, data_index):
    stat_row_data = stat_data.get("rows", [])
    stat_infos = []

    for row in stat_row_data:
        if 'total_plays' not in row:
            continue  # skip rows with missing 'total_plays'
        stat_infos.append(StatsInfo.from_row(row, data_index))

    return stat_infos
