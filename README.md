# n8n Discord Trigger

A lightweight Discord bot that triggers n8n workflows when mentioned in a server or sent a direct message. Sends detailed payloads including user, message, channel, and guild info — with admin status detection built-in.

## Features

- Webhook trigger for n8n when bot is mentioned or DMed
- Works across multiple servers
- Includes full metadata (user, channel, guild, message link, etc.)
- Adds `is_admin` flag for context-aware workflows

## Payload Example

Here’s what the bot sends to your n8n webhook:

```json
{
  "user": {
    "id": "1234567890",
    "username": "TestUser",
    "discriminator": "1234",
    "tag": "TestUser#1234"
  },
  "content": "Hello there!",
  "original_content": "<@9876543210> Hello there!",
  "channel": {
    "id": "5432109876",
    "name": "general",
    "type": "GuildText"
  },
  "guild": {
    "id": "1111111111",
    "name": "My Server"
  },
  "message_id": "999888777",
  "message_link": "https://discord.com/channels/1111111111/5432109876/999888777",
  "timestamp": "2025-07-26T20:50:00.000Z",
  "source": "mention",
  "is_admin": true
}
```

## Docker Setup

The bot is available on Docker Hub:

```bash
docker pull skuldgerry/n8n-discord-trigger:1.0.0
```

```yml
services:
  n8n-discord-trigger:
    image: skuldgerry/n8n-discord-trigger:1.0.0
    container_name: n8n-discord-trigger
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=your_bot_token
      - WEBHOOK_URL=https://your-n8n-instance/webhook/discord
```

After starting the container, check the console logs for the bot's invite link. You can use this link to invite the bot to your server with all required permissions.

### Required Permissions

The bot requires the following permissions to function properly:

- Read Messages/View Channels
- Send Messages
- Read Message History
- Use Slash Commands *(optional, for future use)*
- Administrator *(required to correctly set the `is_admin` flag in the payload)*

---

## How It Works

- When a user **mentions the bot** in a server or sends a **direct message**, the bot captures:
  - Message content
  - User and guild information
  - Whether the user is a Discord admin
  - A message permalink
- The bot sends this data to the `WEBHOOK_URL` you define as a POST request

---

## Setup

1. Create a Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Copy your bot token
3. Deploy the bot using Docker Compose
4. Invite the bot to your server using the invite link shown in the logs
5. In n8n, create an POST HTTP Webhook trigger to receive and handle payloads

---

## Use Cases

- Trigger AI conversations in n8n from Discord
- Control automation workflows via Discord messages
- Personalize responses based on user context and permissions
- Integrate chat-based workflows with memory and logic layers

---

## Built With AI

This bot was built with the help of OpenAI’s GPT technology for rapid prototyping, debugging, and system design.

---

## License

This project is licensed under the MIT License.

