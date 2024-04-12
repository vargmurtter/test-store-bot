import os
import csv
from typing import Any, Dict


class Localizer:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.langs: Dict[str, Dict[str, str]] = {}
        self.current_lang = "ru"
        self._load_locales()

    def _load_locales(self) -> None:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError("Locales file not found!")

        with open(self.filepath, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = row.pop("locale")
                for lang, value in row.items():
                    if lang not in self.langs:
                        self.langs[lang] = {}
                    self.langs[lang][key] = value

    def set_language(self, lang: str) -> None:
        if lang not in self.langs:
            raise ValueError(f"{lang} language not supported.")
        self.current_lang = lang

    def has_translation(self, key: str) -> bool:
        return key in self.langs[self.current_lang]

    def get_text(self, key: str, *params: Any) -> str:
        if not self.has_translation(key):
            return key
        return self.langs[self.current_lang][key].format(*params)
