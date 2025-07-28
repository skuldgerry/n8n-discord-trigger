import os
import logging
import discord
import requests
import json
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Bot is online as {bot.user} (ID: {bot.user.id})")
    invite_link = (
        f"https://discord.com/oauth2/authorize?"
        f"client_id={bot.user.id}&permissions=277025508352&scope=bot%20applications.commands"
    )
    logger.info(f"Invite the bot using this link:\n{invite_link}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    logger.info(f"Received message from {message.author} in {message.channel}: {message.content}")

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mention = bot.user.mentioned_in(message)

    if not (is_dm or is_mention):
        return

    logger.info("Message triggered the webhook")

    # Remove mention if it exists
    mention_text = f"<@{bot.user.id}>"
    clean_content = message.content.replace(mention_text, "").strip()

    # Build payload
    payload = {
        "user": {
            "id": str(message.author.id),
            "username": message.author.name,
            "discriminator": message.author.discriminator,
            "tag": str(message.author),
        },
        "content": clean_content,
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
        "source": "mention" if is_mention else "dm",
        "is_admin": (
            any(r.permissions.administrator for r in getattr(message.author, "roles", []))
            if message.guild else False
        ),
    }

    logger.info(f"Payload:\n{json.dumps(payload, indent=2)}")

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        logger.info(f"Webhook response status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    if not DISCORD_TOKEN or not WEBHOOK_URL:
        logger.error("DISCORD_TOKEN and/or WEBHOOK_URL are not set.")
        exit(1)
    bot.run(DISCORD_TOKEN)
