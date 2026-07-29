import unittest
from types import SimpleNamespace

from trigger_logic import (
    clean_message_content,
    is_direct_bot_mention,
    is_guild_admin,
    should_trigger_message,
)


BOT_ID = 9876543210


class TriggerLogicTests(unittest.TestCase):
    def test_bot_mention_triggers(self):
        message = SimpleNamespace(
            mentions=[SimpleNamespace(id=BOT_ID)],
            mention_everyone=False,
        )

        self.assertTrue(is_direct_bot_mention(message, BOT_ID))

    def test_dm_triggers_without_a_mention(self):
        message = SimpleNamespace(
            mentions=[],
            mention_everyone=False,
        )

        self.assertTrue(
            should_trigger_message(message, BOT_ID, is_dm=True)
        )

    def test_everyone_does_not_trigger(self):
        message = SimpleNamespace(mentions=[], mention_everyone=True)

        self.assertFalse(is_direct_bot_mention(message, BOT_ID))

    def test_here_does_not_trigger(self):
        message = SimpleNamespace(mentions=[], mention_everyone=True)

        self.assertFalse(is_direct_bot_mention(message, BOT_ID))

    def test_other_user_mention_does_not_trigger(self):
        message = SimpleNamespace(
            mentions=[SimpleNamespace(id=1234)],
            mention_everyone=False,
        )

        self.assertFalse(is_direct_bot_mention(message, BOT_ID))

    def test_explicit_bot_mention_still_triggers_with_everyone(self):
        message = SimpleNamespace(
            mentions=[SimpleNamespace(id=BOT_ID)],
            mention_everyone=True,
        )

        self.assertTrue(is_direct_bot_mention(message, BOT_ID))

    def test_clean_content_handles_both_discord_mention_formats(self):
        self.assertEqual(
            clean_message_content(f"<@{BOT_ID}> hello", BOT_ID),
            "hello",
        )
        self.assertEqual(
            clean_message_content(f"<@!{BOT_ID}> hello", BOT_ID),
            "hello",
        )

    def test_resolved_admin_permission_is_used(self):
        author = SimpleNamespace(
            guild_permissions=SimpleNamespace(administrator=True)
        )

        self.assertTrue(is_guild_admin(author, guild=object()))
        self.assertFalse(is_guild_admin(author, guild=None))


if __name__ == "__main__":
    unittest.main()
