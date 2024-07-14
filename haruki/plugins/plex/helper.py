from ...constants import TAUTULLI_TOKEN, TAUTULLI_URL


def get_session_info(session):
    """
    Reads session data and returns the formatted string. Used for the get_activity
    """
    user = session.get('user', 'Unknown User')
    grandparent_title = session.get('grandparent_title', '')
    parent_title = session.get('parent_title', '')
    title = session.get('title', 'Unknown Title')
    quality_profile = session.get('quality_profile', '')
    media_type = session.get('media_type', '')
    if media_type == 'track':
        session_info = ("**User:**  `{:<10} `  **Artist:**  `{}`  **Album:**  `{}`  **Song:**  `{}`  **Quality:**  "
                        "`{}`".format(user, grandparent_title, parent_title, title, quality_profile))
    else:
        session_info = ("**User:**  `{:<10} `  **Show:**  `{}`  **Season:**  `{}`  **Episode:**  `{}`  **Quality:**  "
                        "`{}`").format(user, grandparent_title, parent_title, title, quality_profile)
    return session_info


async def make_api_call(client, api_call):
    """
    Makes API call and retrieves the JSON response.
    """
    url = f"{TAUTULLI_URL}/api/v2?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data
