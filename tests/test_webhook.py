import unittest

from webhook import (
    AUTH_HEADER,
    TOKEN_PREFIX,
    TOKEN_SECRET_HEX_LENGTH,
    WebhookDeliveryError,
    build_auth_headers,
    post_webhook,
)


VALID_TOKEN = TOKEN_PREFIX + ("a" * TOKEN_SECRET_HEX_LENGTH)


class FakeResponse:
    def __init__(self, status=200, error=None):
        self.status = status
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def raise_for_status(self):
        if self.error:
            raise self.error


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.request = None

    def post(self, url, **kwargs):
        self.request = {"url": url, **kwargs}
        return self.response


class WebhookTests(unittest.IsolatedAsyncioTestCase):
    def test_empty_token_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers("")

    def test_newline_in_token_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers(VALID_TOKEN + "\r\nInjected: value")

    def test_short_token_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers(
                TOKEN_PREFIX + ("a" * (TOKEN_SECRET_HEX_LENGTH - 1))
            )

    def test_surrounding_whitespace_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers(" " + VALID_TOKEN)

    def test_non_ascii_token_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers(
                TOKEN_PREFIX + ("\u00e9" * TOKEN_SECRET_HEX_LENGTH)
            )

    def test_expected_token_format_is_accepted(self):
        self.assertEqual(
            build_auth_headers(VALID_TOKEN),
            {AUTH_HEADER: f"Bearer {VALID_TOKEN}"},
        )

    def test_token_without_required_prefix_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers("a" * TOKEN_SECRET_HEX_LENGTH)

    def test_uppercase_hex_is_rejected(self):
        with self.assertRaises(ValueError):
            build_auth_headers(
                TOKEN_PREFIX + ("A" * TOKEN_SECRET_HEX_LENGTH)
            )

    async def test_token_is_sent_in_header(self):
        session = FakeSession(FakeResponse(status=204))

        status = await post_webhook(
            session,
            "https://n8n.example/webhook/discord",
            VALID_TOKEN,
            {"message_id": "123"},
        )

        self.assertEqual(status, 204)
        self.assertEqual(
            session.request["headers"],
            {AUTH_HEADER: f"Bearer {VALID_TOKEN}"},
        )
        self.assertNotIn(VALID_TOKEN, session.request["json"].values())
        self.assertFalse(session.request["allow_redirects"])

    async def test_only_2xx_responses_confirm_delivery(self):
        for status in (200, 201, 202, 204, 299):
            with self.subTest(status=status):
                session = FakeSession(FakeResponse(status=status))
                self.assertEqual(
                    await post_webhook(session, "https://n8n.example/webhook/discord", VALID_TOKEN, {}),
                    status,
                )

    async def test_non_success_responses_are_rejected(self):
        for status in (199, 300, 301, 302, 303, 304, 307, 308, 399):
            with self.subTest(status=status):
                session = FakeSession(FakeResponse(status=status))
                with self.assertRaises(WebhookDeliveryError) as raised:
                    await post_webhook(session, "https://n8n.example/webhook/discord", VALID_TOKEN, {})
                self.assertEqual(raised.exception.status, status)

    async def test_http_error_is_not_treated_as_success(self):
        session = FakeSession(
            FakeResponse(status=500, error=RuntimeError("HTTP 500"))
        )

        with self.assertRaises(RuntimeError):
            await post_webhook(
                session,
                "https://n8n.example/webhook/discord",
                VALID_TOKEN,
                {"message_id": "123"},
            )


if __name__ == "__main__":
    unittest.main()
