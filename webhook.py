"""Authenticated webhook delivery helpers."""

import re
from typing import Any, Mapping


AUTH_HEADER = "Authorization"
TOKEN_PREFIX = "sk-"
TOKEN_SECRET_HEX_LENGTH = 64
TOKEN_PATTERN = re.compile(
    rf"{re.escape(TOKEN_PREFIX)}[0-9a-f]{{{TOKEN_SECRET_HEX_LENGTH}}}"
)


class WebhookDeliveryError(Exception):
    """A webhook response did not confirm successful delivery."""

    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Webhook returned non-success HTTP status {status}")


def build_auth_headers(token: str) -> Mapping[str, str]:
    """Build the required n8n Authorization Bearer header."""

    if not token:
        raise ValueError("WEBHOOK_TOKEN is required")
    if not TOKEN_PATTERN.fullmatch(token):
        raise ValueError(
            "WEBHOOK_TOKEN must match sk- followed by exactly "
            f"{TOKEN_SECRET_HEX_LENGTH} lowercase hexadecimal characters"
        )

    return {AUTH_HEADER: f"Bearer {token}"}


async def post_webhook(
    session: Any,
    url: str,
    token: str,
    payload: Mapping[str, Any],
) -> int:
    """POST one authenticated payload and raise for non-success responses."""

    async with session.post(
        url,
        json=payload,
        headers=build_auth_headers(token),
        allow_redirects=False,
    ) as response:
        response.raise_for_status()
        if not 200 <= response.status < 300:
            raise WebhookDeliveryError(response.status)
        return response.status
