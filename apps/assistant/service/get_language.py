import pycountry
from babel import Locale
from functools import lru_cache

def get_language_full_name(locale_code: str):
    try:
        lang, country = locale_code.split("-")
        language = pycountry.languages.get(alpha_2=lang)
        country = pycountry.countries.get(alpha_2=country)
        return f"{language.name} ({country.name})"
    except Exception:
        return locale_code


LANGUAGE_ALIAS = {"Bengali": "Bangla"}

@lru_cache(maxsize=128)
def get_base_language(locale: str):
    if not locale:
        return None
    try:
        lang_code = locale.split("-")[0]  # en-US -> en
        lang = pycountry.languages.get(alpha_2=lang_code)
        if not lang:
            return None
        name = getattr(lang, "name", None)
        return LANGUAGE_ALIAS.get(name, name)
    except Exception:
        return None


def build_language_list_from_voices(voices: list) -> list:
    langs = set()
    for v in voices:
        base = get_base_language(v.get("locale"))
        if base:
            langs.add(base)
    return sorted(langs)