import discord
from discord.ext import commands
from aiohttp import ClientSession
import logging

from .config import Config

logger = logging.getLogger(__name__)


class WorkBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.session = None

    async def setup_hook(self):
        self.session = ClientSession()

        cogs = [
            'bot.cogs.pokemon',
            'bot.cogs.schedule',
            'bot.cogs.tools',
            'bot.cogs.deskmanager'
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Cog carregado: {cog}")
            except Exception as e:
                logger.error(f"Erro ao carregar {cog}: {e}")

    async def on_ready(self):
        logger.info(f"Bot conectado como {self.user}")
        logger.info(f"Servidores: {len(self.guilds)}")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()
