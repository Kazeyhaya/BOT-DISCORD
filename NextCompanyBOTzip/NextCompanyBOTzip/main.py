import logging
from bot import WorkBot
from bot.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    if not Config.TOKEN:
        logger.error("DISCORD_TOKEN nao encontrado!")
        return

    logger.info("Iniciando bot...")
    bot = WorkBot()
    bot.run(Config.TOKEN)


if __name__ == "__main__":
    main()
