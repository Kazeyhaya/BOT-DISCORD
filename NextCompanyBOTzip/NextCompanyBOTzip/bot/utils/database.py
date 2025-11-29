import os
import json
import logging

logger = logging.getLogger(__name__)


class JsonDatabase:
    @staticmethod
    def load(filename: str, default: dict = None) -> dict:
        if default is None:
            default = {}
        try:
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {filename}: {e}")

        JsonDatabase.save(filename, default)
        return default

    @staticmethod
    def save(filename: str, data: dict) -> bool:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar {filename}: {e}")
            return False
