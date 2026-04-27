import asyncio
import logging
import sys

import discord
from discord.ext import commands

import config

# ─────────────────────────────────────────────
# Setup logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)),

    ],
)
logger = logging.getLogger("jadwal_bot")


# ─────────────────────────────────────────────
# Validasi config sebelum start
# ─────────────────────────────────────────────
def validate_config():
    errors = []
    if not config.BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN belum diset di .env")
    if not config.GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY belum diset di .env")
    if errors:
        for e in errors:
            logger.error(f"❌ Config error: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# Bot setup
# ─────────────────────────────────────────────
class JadwalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",   # prefix jarang dipakai, tapi wajib diset
            intents=intents,
            help_command=None,    # kita pakai /help-schedule sendiri
        )

    async def setup_hook(self):
        """Dipanggil saat bot startup — load cogs & sync slash commands."""
        logger.info("Loading cogs...")
        await self.load_extension("cogs.jadwal")
        logger.info("✅ Cog 'jadwal' loaded")

        logger.info("Syncing slash commands...")
        synced = await self.tree.sync()
        logger.info(f"✅ Synced {len(synced)} slash command(s): {[c.name for c in synced]}")

    async def on_ready(self):
        logger.info("─" * 50)
        logger.info(f"✅ Bot online sebagai: {self.user} (ID: {self.user.id})")
        logger.info(f"   Semester aktif : {config.ACTIVE_SEMESTER}")
        logger.info(f"   Gemini model   : {config.GEMINI_MODEL}")
        logger.info(f"   Servers        : {len(self.guilds)}")
        logger.info("─" * 50)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/bot-course-schedule",
            )
        )

    async def on_command_error(self, ctx, error):
        logger.warning(f"Command error: {error}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
async def main():
    validate_config()
    bot = JadwalBot()
    async with bot:
        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
