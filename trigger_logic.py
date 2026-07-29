"""Pure helpers for deciding which Discord messages trigger n8n."""

from typing import Any


def is_direct_bot_mention(message: Any, bot_user_id: int) -> bool:
    """Return True only when the bot user is explicitly mentioned.

    discord.py's ``mentioned_in`` helper also returns True for @here and
    @everyone. Checking the concrete mentions collection avoids that behavior.
    """

    return any(
        getattr(mentioned_user, "id", None) == bot_user_id
        for mentioned_user in getattr(message, "mentions", ())
    )


def should_trigger_message(
    message: Any,
    bot_user_id: int,
    *,
    is_dm: bool,
) -> bool:
    """Return True for DMs or an explicit mention of the bot user."""

    return is_dm or is_direct_bot_mention(message, bot_user_id)


def clean_message_content(content: str, bot_user_id: int) -> str:
    """Remove Discord's two supported bot mention formats from content."""

    return (
        content.replace(f"<@{bot_user_id}>", "")
        .replace(f"<@!{bot_user_id}>", "")
        .strip()
    )


def is_guild_admin(author: Any, guild: Any) -> bool:
    """Return the resolved guild administrator permission for an author."""

    if guild is None:
        return False

    permissions = getattr(author, "guild_permissions", None)
    return bool(getattr(permissions, "administrator", False))
