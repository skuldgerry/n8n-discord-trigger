import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from invite import (
    DISCORD_AUTHORIZE_URL,
    VIEW_CHANNEL_PERMISSION,
    build_invite_url,
    write_invite_url,
)


class InviteTests(unittest.TestCase):
    def test_builds_least_privilege_bot_invite(self):
        invite_url = build_invite_url(123456789)
        parsed = urlparse(invite_url)

        self.assertEqual(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            DISCORD_AUTHORIZE_URL,
        )
        self.assertEqual(
            parse_qs(parsed.query),
            {
                "client_id": ["123456789"],
                "permissions": [str(VIEW_CHANNEL_PERMISSION)],
                "scope": ["bot"],
            },
        )

    @patch.object(Path, "write_text")
    def test_writes_invite_url_with_a_trailing_newline(self, write_text):
        invite_url = build_invite_url(123456789)

        destination = write_invite_url(
            "/tmp/n8n-discord-trigger-invite-url.txt",
            invite_url,
        )

        self.assertEqual(
            destination,
            Path("/tmp/n8n-discord-trigger-invite-url.txt"),
        )
        write_text.assert_called_once_with(
            f"{invite_url}\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
