import pathlib
from dataclasses import dataclass
from pathlib import Path

import dotenv
import requests
from jinja2 import Template
from pydantic import Extra
from requests import Response
from utils import CodeDest, CodeKeys, inject_inline, log

from mealie.schema._mealie import MealieModel

BASE = pathlib.Path(__file__).parent.parent.parent

API_KEY = dotenv.get_key(BASE / ".env", "CROWDIN_API_KEY")


@dataclass
class LocaleData:
    name: str
    dir: str = "ltr"


LOCALE_DATA: dict[str, LocaleData] = {
    "en-US": LocaleData(name="American English"),
    "en-GB": LocaleData(name="British English"),
    "af-ZA": LocaleData(name="Afrikaans (Afrikaans)"),
    "ar-SA": LocaleData(name="العربية (Arabic)", dir="rtl"),
    "ca-ES": LocaleData(name="Català (Catalan)"),
    "cs-CZ": LocaleData(name="Čeština (Czech)"),
    "da-DK": LocaleData(name="Dansk (Danish)"),
    "de-DE": LocaleData(name="Deutsch (German)"),
    "el-GR": LocaleData(name="Ελληνικά (Greek)"),
    "es-ES": LocaleData(name="Español (Spanish)"),
    "fi-FI": LocaleData(name="Suomi (Finnish)"),
    "fr-FR": LocaleData(name="Français (French)"),
    "he-IL": LocaleData(name="עברית (Hebrew)", dir="rtl"),
    "hu-HU": LocaleData(name="Magyar (Hungarian)"),
    "it-IT": LocaleData(name="Italiano (Italian)"),
    "ja-JP": LocaleData(name="日本語 (Japanese)"),
    "ko-KR": LocaleData(name="한국어 (Korean)"),
    "no-NO": LocaleData(name="Norsk (Norwegian)"),
    "nl-NL": LocaleData(name="Nederlands (Dutch)"),
    "pl-PL": LocaleData(name="Polski (Polish)"),
    "pt-BR": LocaleData(name="Português do Brasil (Brazilian Portuguese)"),
    "pt-PT": LocaleData(name="Português (Portuguese)"),
    "ro-RO": LocaleData(name="Română (Romanian)"),
    "ru-RU": LocaleData(name="Pусский (Russian)"),
    "sr-SP": LocaleData(name="српски (Serbian)"),
    "sv-SE": LocaleData(name="Svenska (Swedish)"),
    "tr-TR": LocaleData(name="Türkçe (Turkish)"),
    "uk-UA": LocaleData(name="Українська (Ukrainian)"),
    "vi-VN": LocaleData(name="Tiếng Việt (Vietnamese)"),
    "zh-CN": LocaleData(name="简体中文 (Chinese simplified)"),
    "zh-TW": LocaleData(name="繁體中文 (Chinese traditional)"),
}

LOCALE_TEMPLATE = """// This Code is auto generated by gen_global_components.py
export const LOCALES = [{% for locale in locales %}
  {
    name: "{{ locale.name }}",
    value: "{{ locale.locale }}",
    progress: {{ locale.progress }},
    dir: "{{ locale.dir }}",
  },{% endfor %}
]

"""


class TargetLanguage(MealieModel):
    id: str
    name: str
    locale: str
    dir: str = "ltr"
    threeLettersCode: str
    twoLettersCode: str
    progress: float = 0.0

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


class CrowdinApi:
    project_name = "Mealie"
    project_id = "451976"
    api_key = API_KEY

    def __init__(self, api_key: str):
        api_key = api_key

    @property
    def headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def get_projects(self) -> Response:
        return requests.get("https://api.crowdin.com/api/v2/projects", headers=self.headers)

    def get_project(self) -> Response:
        return requests.get(f"https://api.crowdin.com/api/v2/projects/{self.project_id}", headers=self.headers)

    def get_languages(self) -> list[TargetLanguage]:
        response = self.get_project()
        tls = response.json()["data"]["targetLanguages"]

        models = [TargetLanguage(**t) for t in tls]

        models.insert(
            0,
            TargetLanguage(
                id="en-US",
                name="English",
                locale="en-US",
                dir="ltr",
                threeLettersCode="en",
                twoLettersCode="en",
                progress=100,
            ),
        )

        progress: list[dict] = self.get_progress()["data"]

        for model in models:
            if model.locale in LOCALE_DATA:
                locale_data = LOCALE_DATA[model.locale]
                model.name = locale_data.name
                model.dir = locale_data.dir

            for p in progress:
                if p["data"]["languageId"] == model.id:
                    model.progress = p["data"]["translationProgress"]

        models.sort(key=lambda x: x.locale, reverse=True)
        return models

    def get_progress(self) -> dict:
        response = requests.get(
            f"https://api.crowdin.com/api/v2/projects/{self.project_id}/languages/progress?limit=500",
            headers=self.headers,
        )
        return response.json()


PROJECT_DIR = Path(__file__).parent.parent.parent


datetime_dir = PROJECT_DIR / "frontend" / "lang" / "dateTimeFormats"
locales_dir = PROJECT_DIR / "frontend" / "lang" / "messages"
nuxt_config = PROJECT_DIR / "frontend" / "nuxt.config.js"

"""
This snippet walks the message and dat locales directories and generates the import information
for the nuxt.config.js file and automatically injects it into the nuxt.config.js file. Note that
the code generation ID is hardcoded into the script and required in the nuxt config.
"""


def inject_nuxt_values():
    all_date_locales = [
        f'"{match.stem}": require("./lang/dateTimeFormats/{match.name}"),' for match in datetime_dir.glob("*.json")
    ]

    all_langs = []
    for match in locales_dir.glob("*.json"):
        lang_string = f'{{ code: "{match.stem}", file: "{match.name}" }},'
        all_langs.append(lang_string)

    log.debug(f"injecting locales into nuxt config -> {nuxt_config}")
    inject_inline(nuxt_config, CodeKeys.nuxt_local_messages, all_langs)
    inject_inline(nuxt_config, CodeKeys.nuxt_local_dates, all_date_locales)


def generate_locales_ts_file():
    api = CrowdinApi("")
    models = api.get_languages()
    tmpl = Template(LOCALE_TEMPLATE)
    rendered = tmpl.render(locales=models)

    log.debug(f"generating locales ts file -> {CodeDest.use_locales}")
    with open(CodeDest.use_locales, "w") as f:
        f.write(rendered)  # type:ignore


def main():
    if API_KEY is None or API_KEY == "":
        log.error("CROWDIN_API_KEY is not set")
        return

    generate_locales_ts_file()
    inject_nuxt_values()


if __name__ == "__main__":
    main()
