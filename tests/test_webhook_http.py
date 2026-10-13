"""Exercise delivery against an isolated loopback HTTP server."""

import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
from aiohttp import web

import bot as bot_module
from webhook import WebhookDeliveryError, post_webhook


TOKEN = "sk-" + "a" * 64
BOT_ID = 9876543210


class WebhookHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []
        app = web.Application()
        app.router.add_post("/status/{status}", self.handle_status)
        app.router.add_get("/login", self.handle_login)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await site.start()
        port = self.runner.addresses[0][1]
        self.base_url = f"http://127.0.0.1:{port}"
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5)
        )

    async def asyncTearDown(self):
        await self.session.close()
        await self.runner.cleanup()

    async def handle_status(self, request):
        self.calls.append({
            "method": request.method,
            "path": request.path,
            "authorization": request.headers.get("Authorization"),
            "payload": await request.json(),
        })
        status = int(request.match_info["status"])
        headers = {"Location": "/login"} if 300 <= status < 400 else {}
        return web.Response(status=status, headers=headers)

    async def handle_login(self, request):
        self.calls.append({"method": request.method, "path": request.path})
        return web.Response(text="Login page")

    async def test_success_delivers_authenticated_payload(self):
        payload = {"message_id": "test", "content": "fixture"}
        for status in (200, 201, 202, 204):
            with self.subTest(status=status):
                returned = await post_webhook(
                    self.session, f"{self.base_url}/status/{status}", TOKEN, payload
                )
                self.assertEqual(returned, status)
                self.assertEqual(self.calls[-1]["method"], "POST")
                self.assertEqual(self.calls[-1]["payload"], payload)
                self.assertEqual(self.calls[-1]["authorization"], f"Bearer {TOKEN}")

    async def test_redirect_is_rejected_without_contacting_login(self):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                before = len(self.calls)
                with self.assertRaises(WebhookDeliveryError) as raised:
                    await post_webhook(
                        self.session, f"{self.base_url}/status/{status}", TOKEN, {}
                    )
                self.assertEqual(raised.exception.status, status)
                self.assertEqual(len(self.calls), before + 1)
        self.assertFalse(any(call["path"] == "/login" for call in self.calls))

    async def test_304_is_not_success(self):
        with self.assertRaises(WebhookDeliveryError) as raised:
            await post_webhook(self.session, f"{self.base_url}/status/304", TOKEN, {})
        self.assertEqual(raised.exception.status, 304)

    async def test_http_errors_remain_failures(self):
        for status in (401, 403, 404, 500, 503):
            with self.subTest(status=status):
                with self.assertRaises(aiohttp.ClientResponseError) as raised:
                    await post_webhook(
                        self.session, f"{self.base_url}/status/{status}", TOKEN, {}
                    )
                self.assertEqual(raised.exception.status, status)

    async def run_bot_message(self, status):
        message = SimpleNamespace(
            author=SimpleNamespace(
                bot=False, id=123, name="fixture", discriminator="0"
            ),
            channel=SimpleNamespace(id=456, name="fixture"),
            guild=SimpleNamespace(id=789, name="fixture"),
            mentions=[SimpleNamespace(id=BOT_ID)],
            content=f"<@{BOT_ID}> fixture",
            id=101112,
            jump_url="https://discord.example/fixture",
            created_at=datetime.datetime(2026, 10, 13, tzinfo=datetime.timezone.utc),
        )
        process_commands = AsyncMock()
        with (
            patch.object(bot_module.bot._connection, "user", SimpleNamespace(id=BOT_ID)),
            patch.object(bot_module, "webhook_session", self.session),
            patch.object(bot_module, "WEBHOOK_URL", f"{self.base_url}/status/{status}"),
            patch.object(bot_module, "WEBHOOK_TOKEN", TOKEN),
            patch.object(bot_module.bot, "process_commands", process_commands),
            self.assertLogs(bot_module.logger, level="INFO") as logs,
        ):
            await bot_module.on_message(message)
        process_commands.assert_awaited_once_with(message)
        return logs.output

    async def test_bot_logs_rejections_without_false_delivery(self):
        for status in (302, 304, 401, 500):
            with self.subTest(status=status):
                logs = await self.run_bot_message(status)
                self.assertTrue(any(f"Webhook rejected: status={status}" in line for line in logs))
                self.assertFalse(any("Webhook delivered" in line for line in logs))

    async def test_bot_logs_success_and_preserves_payload(self):
        logs = await self.run_bot_message(204)
        self.assertTrue(any("Webhook delivered: status=204" in line for line in logs))
        payload = self.calls[-1]["payload"]
        self.assertEqual(payload["content"], "fixture")
        self.assertEqual(payload["original_content"], f"<@{BOT_ID}> fixture")
        self.assertEqual(payload["source"], "mention")
        self.assertEqual(payload["message_id"], "101112")


if __name__ == "__main__":
    unittest.main()
