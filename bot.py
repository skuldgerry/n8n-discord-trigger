import asyncio
import logging
import os

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from invite import build_invite_url, write_invite_url
from trigger_logic import (
    clean_message_content,
    is_guild_admin,
    should_trigger_message,
)
from webhook import WebhookDeliveryError, build_auth_headers, post_webhook


VERSION = "2.0.1"

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")
INVITE_URL_FILE = os.getenv(
    "INVITE_URL_FILE",
    "/tmp/n8n-discord-trigger-invite-url.txt",
)
try:
    WEBHOOK_TIMEOUT_SECONDS = float(
        os.getenv("WEBHOOK_TIMEOUT_SECONDS", "10")
    )
except ValueError:
    WEBHOOK_TIMEOUT_SECONDS = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
webhook_session: aiohttp.ClientSession | None = None


@bot.event
async def on_ready():
    logger.info(
        "n8n Discord Trigger %s is online as %s (ID: %s)",
        VERSION,
        bot.user,
        bot.user.id,
    )
    invite_link = build_invite_url(bot.user.id)
    logger.info("Invite the bot using this link:\n%s", invite_link)
    try:
        destination = write_invite_url(INVITE_URL_FILE, invite_link)
        logger.info("Invite URL saved to %s", destination)
    except OSError as error:
        logger.warning(
            "Could not save invite URL to %s: %s",
            INVITE_URL_FILE,
            type(error).__name__,
        )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)

    if not should_trigger_message(message, bot.user.id, is_dm=is_dm):
        return

    source = "dm" if is_dm else "mention"
    logger.info(
        "Webhook triggered: source=%s user_id=%s channel_id=%s message_id=%s",
        source,
        message.author.id,
        message.channel.id,
        message.id,
    )

    payload = {
        "user": {
            "id": str(message.author.id),
            "username": message.author.name,
            "discriminator": message.author.discriminator,
            "tag": str(message.author),
        },
        "content": clean_message_content(message.content, bot.user.id),
        "original_content": message.content,
        "channel": {
            "id": str(message.channel.id),
            "name": getattr(message.channel, "name", "DM"),
            "type": type(message.channel).__name__,
        },
        "guild": {
            "id": str(message.guild.id) if message.guild else None,
            "name": message.guild.name if message.guild else None,
        },
        "message_id": str(message.id),
        "message_link": message.jump_url if message.guild else None,
        "timestamp": message.created_at.isoformat(),
        "source": source,
        "is_admin": is_guild_admin(message.author, message.guild),
    }

    try:
        if webhook_session is None:
            raise RuntimeError("Webhook session is not initialized")

        status = await post_webhook(
            webhook_session,
            WEBHOOK_URL,
            WEBHOOK_TOKEN,
            payload,
        )
        logger.info(
            "Webhook delivered: status=%s message_id=%s",
            status,
            message.id,
        )
    except (aiohttp.ClientResponseError, WebhookDeliveryError) as error:
        logger.error(
            "Webhook rejected: status=%s message_id=%s",
            error.status,
            message.id,
        )
    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        logger.error(
            "Webhook delivery failed for message_id=%s: %s",
            message.id,
            type(error).__name__,
        )

    await bot.process_commands(message)


def validate_configuration() -> list[str]:
    required = {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "WEBHOOK_URL": WEBHOOK_URL,
        "WEBHOOK_TOKEN": WEBHOOK_TOKEN,
    }
    errors = [
        f"{name} is not set"
        for name, value in required.items()
        if not value
    ]

    if WEBHOOK_TOKEN:
        try:
            build_auth_headers(WEBHOOK_TOKEN)
        except ValueError as error:
            errors.append(str(error))

    if (
        WEBHOOK_TIMEOUT_SECONDS is None
        or WEBHOOK_TIMEOUT_SECONDS <= 0
    ):
        errors.append("WEBHOOK_TIMEOUT_SECONDS must be greater than zero")

    return errors


async def main():
    global webhook_session

    configuration_errors = validate_configuration()
    if configuration_errors:
        logger.error(
            "Invalid configuration: %s",
            "; ".join(configuration_errors),
        )
        raise SystemExit(1)

    timeout = aiohttp.ClientTimeout(total=WEBHOOK_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as webhook_session:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
