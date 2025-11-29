import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TOKEN = os.getenv('DISCORD_TOKEN')
    DESK_CHANNEL_ID = int(os.getenv('DESK_CHANNEL_ID', 1423034192387637299))
    DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
    ROLE_ID = int(os.getenv('DISCORD_ROLE_ID', 0))
    GEMINI_KEY = os.getenv('GEMINI_KEY')
    PORT = int(os.environ.get("PORT", 5000))

    FILES = {
        "feriados": "feriados.json",
        "config": "config.json",
        "pokedex": "pokedex.json"
    }

    DEFAULT_HOLIDAYS = {
        "01/01": "Confraternizacao Universal",
        "21/04": "Tiradentes",
        "01/05": "Dia do Trabalho",
        "07/09": "Independencia",
        "12/10": "Nossa Senhora Aparecida",
        "02/11": "Finados",
        "15/11": "Proclamacao da Republica",
        "25/12": "Natal"
    }

    DEFAULT_CONFIG = {"saida_hoje": "18:00"}

    BOT_PERSONALITY = """Voce e o assistente do time NextCompany. Seja prestativo, divertido e objetivo. 
Use linguagem informal brasileira. Seja breve nas respostas quando possivel.
Voce pode usar expressoes como 'bora', 'show', 'beleza', 'tranquilo'.
Se perguntarem sobre voce, diga que e o bot da NextCompany."""
