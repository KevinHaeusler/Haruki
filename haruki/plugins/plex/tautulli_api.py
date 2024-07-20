from ...constants import TAUTULLI_TOKEN, TAUTULLI_URL


async def get_activity_info(client):
    response = await make_api_call(client, 'get_activity')

    if response is None:
        return "Invalid request."

    response_data = response.get('response', {}).get('data', {})
    sessions = response_data.get('sessions')

    if not sessions:
        return "No active sessions."

    activity_info = []
    for session in sessions:
        if isinstance(session, dict):
            user = session.get('user', 'Unknown User')
            grandparent_title = session.get('grandparent_title', '')
            parent_title = session.get('parent_title', '')
            title = session.get('title', 'Unknown Title')
            quality_profile = session.get('quality_profile', '')
            media_type = session.get('media_type', '')

            if media_type == 'track':
                session_info = {
                    "User":    user,
                    "Artist":  grandparent_title,
                    "Album":   parent_title,
                    "Song":    title,
                    "Quality": quality_profile
                }
            else:
                session_info = {
                    "User":    user,
                    "Show":    grandparent_title,
                    "Season":  parent_title,
                    "Episode": title,
                    "Quality": quality_profile
                }

            activity_info.append(session_info)
        else:
            print(f"Unexpected session data type: {type(session)}, value: {session}")
    return activity_info


async def make_api_call(client, api_call):
    url = f"{TAUTULLI_URL}/api/v2?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data
