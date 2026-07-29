"""Discord bot invite URL helpers."""

from pathlib import Path
from urllib.parse import urlencode


DISCORD_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
VIEW_CHANNEL_PERMISSION = 1024


def build_invite_url(client_id: int | str) -> str:
    """Build a least-privilege Discord bot invite URL."""

    query = urlencode(
        {
            "client_id": str(client_id),
            "permissions": VIEW_CHANNEL_PERMISSION,
            "scope": "bot",
        }
    )
    return f"{DISCORD_AUTHORIZE_URL}?{query}"


def write_invite_url(path: str, invite_url: str) -> Path:
    """Persist the public invite URL for retrieval after logs rotate."""

    destination = Path(path)
    destination.write_text(f"{invite_url}\n", encoding="utf-8")
    return destination
