import re
from typing import List

import requests
from bs4 import BeautifulSoup

from general_scripts.scraper_telegram_bot.article_scraper.base_scraper import GenericScraper


class RepubblicaScraper(GenericScraper):
    url: str = "https://www.repubblica.it/"

    def extract_links(self) -> List[str]:
        pass

    def extract_article_name(self, soup: BeautifulSoup) -> str:
        title = soup.find("h1", attrs={"class": ["detail_title", "story__title"]})
        if title:
            return re.sub(r"\s+|\n|\r|\t", " ", title.get_text()).strip()
        return ""


if __name__ == '__main__':
    repubblica_scraper = RepubblicaScraper()
    response = requests.get(
        "https://www.repubblica.it/esteri/2024/04/16/news/europa_indifesa_attacco_missili_balistici_iran_israele_medio_oriente-422543807/?ref=RHLF-BG-P1-S1-T1")
    soup = BeautifulSoup(response.text, "html.parser")
    print(repubblica_scraper.extract_article_name(soup=soup))
