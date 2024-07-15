from hata import Embed

from haruki.bots import Haruki


@Haruki.interactions(is_global = True)
async def perms(event):
    """Shows your permissions."""
    user_permissions = event.user_permissions
    if user_permissions:
        description = '\n'.join(permission_name.replace('_', '-') for permission_name in user_permissions)
    else:
        description = '*none*'

    user = event.user
    return Embed('Permissions', description).add_author(user.full_name, user.avatar_url)
