from ...constants import TAUTULLI_TOKEN, TAUTULLI_URL


def get_session_info(session):
    """
    Get session information.

    This method takes a session object as input and returns a formatted string containing session information.

    Parameters:
    - session (dict): A dictionary representing the session object.

    Returns:
    - session_info (str): A formatted string containing session information.

    Example usage:
    ```
    session = {
        'user': 'John Doe',
        'grandparent_title': 'Artist',
        'parent_title': 'Album',
        'title': 'Song',
        'quality_profile': 'High',
        'media_type': 'track'
    }
    info = get_session_info(session)
    print(info)
    ```

    Output:
    ```
    **User:**  `John Doe    `  **Artist:**  `Artist`  **Album:**  `Album`  **Song:**  `Song`  **Quality:**  `High`
    ```
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

    Parameters:
    - client: The http client used to make the api call.
    - api_call: The specific api call to be made.

    Returns:
    The data obtained from the api call.

    Example usage:
    client = aiohttp.ClientSession()
    api_call = "get_users"
    result = await make_api_call(client, api_call)

    """
    url = f"{TAUTULLI_URL}/api/v2?apikey={TAUTULLI_TOKEN}&cmd={api_call}"
    async with client.http.get(url) as response:
        data = await response.json()
    return data
