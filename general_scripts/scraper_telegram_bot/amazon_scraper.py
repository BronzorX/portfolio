from pprint import pprint
from typing import List
import requests
from pydantic import BaseModel

from general_scripts.scraper_telegram_bot.article_scraper.base_scraper import GenericScraper


class AmazonScraper(GenericScraper):
    category: str

    def get_all_products(self) -> List[str]:
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
        pprint(list(self.extract_links_from_link(
            link="https://www.amazon.it/s?k=pc&__mk_it_IT=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=6J8CZLH8QG2D&sprefix=p%2Caps%2C113&ref=nb_sb_noss_2",
            headers=headers)))


if __name__ == '__main__':
    scraper = AmazonScraper(category='computer')
    scraper.get_all_products()
