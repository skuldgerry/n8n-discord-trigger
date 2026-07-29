# n8n Discord Trigger

A lightweight Discord bot that triggers n8n workflows when the bot is explicitly
mentioned in a server or sent a direct message.

## Trigger behavior

- A direct mention of the bot in a guild triggers the webhook.
- `@here` and `@everyone` do not trigger the webhook.
- Mentioning another user does not trigger the webhook.
- Direct messages to the bot continue to trigger the webhook.

## n8n authentication

Version 2.0.0 requires an Authorization Bearer token on every webhook request.

Generate a 256-bit token in the required `sk-` format:

```bash
python -c "import secrets; print('sk-' + secrets.token_hex(32))"
```

If OpenSSL is available, the equivalent command is:

```powershell
"sk-$(openssl rand -hex 32)"
```

The generated token contains the `sk-` prefix followed by exactly 64 lowercase
hexadecimal characters: 67 characters total.

In the n8n Webhook node:

1. Set **Authentication** to **Header Auth**.
2. Create a Header Auth credential.
3. Set the header name to `Authorization`.
4. Set the header value to `Bearer ` followed by the generated token.

For example, if `WEBHOOK_TOKEN` is `sk-<generated-secret>`, the n8n credential
value is `Bearer sk-<generated-secret>`. Always send the webhook over HTTPS.

## Docker Compose

```yaml
services:
  n8n-discord-trigger:
    image: skuldgerry/n8n-discord-trigger:2.0.0
    container_name: n8n-discord-trigger
    restart: unless-stopped
    environment:
      DISCORD_TOKEN: your_bot_token
      WEBHOOK_URL: https://your-n8n-instance/webhook/discord
      WEBHOOK_TOKEN: sk-replace-with-64-lowercase-hex-characters
      WEBHOOK_TIMEOUT_SECONDS: "10"
```

Do not commit real token values to this repository or place them directly in a
public Compose file. Use your deployment platform's secret management.

## Discord setup

1. Create an application and bot in the
   [Discord Developer Portal](https://discord.com/developers/applications).
2. Enable the **Message Content Intent** on the Bot page.
3. Set `DISCORD_TOKEN`, `WEBHOOK_URL`, and `WEBHOOK_TOKEN`.
4. Start the container.
5. Use the invite link written to the container logs.

The bot only needs **View Channels** for its trigger path. It does not need
Administrator permission to determine whether the message author is an
administrator.

## Payload

```json
{
  "user": {
    "id": "1234567890",
    "username": "TestUser",
    "discriminator": "0",
    "tag": "TestUser"
  },
  "content": "Hello there!",
  "original_content": "<@9876543210> Hello there!",
  "channel": {
    "id": "5432109876",
    "name": "general",
    "type": "TextChannel"
  },
  "guild": {
    "id": "1111111111",
    "name": "My Server"
  },
  "message_id": "999888777",
  "message_link": "https://discord.com/channels/1111111111/5432109876/999888777",
  "timestamp": "2026-07-29T20:50:00+00:00",
  "source": "mention",
  "is_admin": true
}
```

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DISCORD_TOKEN` | Yes | — | Discord bot token |
| `WEBHOOK_URL` | Yes | — | Production n8n webhook URL |
| `WEBHOOK_TOKEN` | Yes | — | `sk-` followed by exactly 64 lowercase hex characters |
| `WEBHOOK_TIMEOUT_SECONDS` | No | `10` | Total HTTP request timeout |

## Development

```bash
python -m unittest discover -s tests -v
```

See [CHANGELOG.md](CHANGELOG.md) for release history and
[VERSIONING.md](VERSIONING.md) for the versioning policy.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
