"""Defensive message and WebSocket fixtures; no Discord/n8n connections."""

import asyncio
import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
from aiohttp import web

import bot as bot_module
import test_webhook_http as http_fixtures


BOT_ID = http_fixtures.BOT_ID
TOKEN = http_fixtures.TOKEN


class DiscordMessageTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = http_fixtures.WebhookHTTPTests.asyncSetUp
    asyncTearDown = http_fixtures.WebhookHTTPTests.asyncTearDown
    handle_status = http_fixtures.WebhookHTTPTests.handle_status
    handle_login = http_fixtures.WebhookHTTPTests.handle_login

    def message(self, *, dm=False, bot=False, content="fixture", mentions=()):
        channel = Mock(spec=bot_module.discord.DMChannel) if dm else SimpleNamespace(name="fixture")
        channel.id = 456
        return SimpleNamespace(
            author=SimpleNamespace(bot=bot, id=123, name="fixture", discriminator="0"),
            channel=channel,
            guild=None if dm else SimpleNamespace(id=789, name="fixture"),
            mentions=[SimpleNamespace(id=user_id) for user_id in mentions],
            mention_everyone="@everyone" in content or "@here" in content,
            content=content,
            id=101112,
            jump_url="https://discord.example/fixture",
            created_at=datetime.datetime(2026, 11, 20, tzinfo=datetime.timezone.utc),
        )

    async def dispatch(self, message, delivery_error=None):
        process_commands = AsyncMock()
        with (
            patch.object(bot_module.bot._connection, "user", SimpleNamespace(id=BOT_ID)),
            patch.object(bot_module, "webhook_session", self.session),
            patch.object(bot_module, "WEBHOOK_URL", f"{self.base_url}/status/204"),
            patch.object(bot_module, "WEBHOOK_TOKEN", TOKEN),
            patch.object(bot_module.bot, "process_commands", process_commands),
        ):
            if delivery_error is None:
                await bot_module.on_message(message)
            else:
                with patch.object(bot_module, "post_webhook", AsyncMock(side_effect=delivery_error)):
                    await bot_module.on_message(message)
        return process_commands

    async def test_dm_without_mention_preserves_dm_payload(self):
        message = self.message(dm=True, content="private fixture")
        processed = await self.dispatch(message)
        self.assertEqual(len(self.calls), 1)
        payload = self.calls[0]["payload"]
        self.assertEqual(payload["source"], "dm")
        self.assertEqual(payload["content"], "private fixture")
        self.assertEqual(payload["guild"], {"id": None, "name": None})
        self.assertIsNone(payload["message_link"])
        self.assertFalse(payload["is_admin"])
        self.assertEqual(self.calls[0]["authorization"], f"Bearer {TOKEN}")
        processed.assert_awaited_once_with(message)

    async def test_bot_authors_never_trigger(self):
        for dm in (False, True):
            with self.subTest(dm=dm):
                processed = await self.dispatch(self.message(dm=dm, bot=True, mentions=(BOT_ID,)))
                processed.assert_not_awaited()
        self.assertEqual(self.calls, [])

    async def test_broadcasts_and_other_users_never_trigger(self):
        for content, mentions in (("@everyone fixture", ()), ("@here fixture", ()), ("<@42> fixture", (42,))):
            with self.subTest(content=content):
                processed = await self.dispatch(self.message(content=content, mentions=mentions))
                processed.assert_not_awaited()
        self.assertEqual(self.calls, [])

    async def test_explicit_mentions_preserve_clean_content(self):
        cases = (
            (f"<@{BOT_ID}> fixture", "fixture"),
            (f"<@!{BOT_ID}> fixture", "fixture"),
            (f"@everyone <@{BOT_ID}> fixture", "@everyone  fixture"),
        )
        for content, cleaned in cases:
            with self.subTest(content=content):
                message = self.message(content=content, mentions=(BOT_ID,))
                processed = await self.dispatch(message)
                payload = self.calls[-1]["payload"]
                self.assertEqual(payload["source"], "mention")
                self.assertEqual(payload["content"], cleaned)
                self.assertEqual(payload["original_content"], content)
                processed.assert_awaited_once_with(message)
        self.assertEqual(len(self.calls), len(cases))

    async def test_timeouts_and_connection_errors_do_not_log_delivery(self):
        for error in (asyncio.TimeoutError(), aiohttp.ClientConnectionError("fixture")):
            with self.subTest(error=type(error).__name__):
                message = self.message(mentions=(BOT_ID,))
                with self.assertLogs(bot_module.logger, level="ERROR") as logs:
                    processed = await self.dispatch(message, delivery_error=error)
                self.assertTrue(any("Webhook delivery failed" in line for line in logs.output))
                self.assertFalse(any("Webhook delivered" in line for line in logs.output))
                processed.assert_awaited_once_with(message)
        self.assertEqual(self.calls, [])


class DiscordWebSocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_compressed_gateway_json_and_ping_before_ack(self):
        heartbeats = []

        async def gateway(request):
            ws = web.WebSocketResponse(compress=True)
            await ws.prepare(request)
            await ws.send_json({"op": 10, "d": {"heartbeat_interval": 45000}})
            heartbeats.append(await ws.receive_json())
            await ws.ping(b"fixture")
            await ws.send_json({"op": 11, "d": None, "fixture": "x" * 2048})
            await ws.close()
            return ws

        app = web.Application()
        app.router.add_get("/gateway", gateway)
        runner = web.AppRunner(app)
        await runner.setup()
        try:
            await web.TCPSite(runner, "127.0.0.1", 0).start()
            port = runner.addresses[0][1]
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.ws_connect(
                    f"http://127.0.0.1:{port}/gateway", compress=15,
                    timeout=aiohttp.ClientWSTimeout(ws_receive=5),
                ) as ws:
                    self.assertGreater(ws.compress, 0)
                    self.assertEqual((await ws.receive_json())["op"], 10)
                    await ws.send_json({"op": 1, "d": 123})
                    acknowledgement = await ws.receive_json()
                    self.assertEqual(acknowledgement["op"], 11)
                    self.assertEqual(acknowledgement["fixture"], "x" * 2048)
            self.assertEqual(heartbeats, [{"op": 1, "d": 123}])
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    unittest.main()
