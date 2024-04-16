from typing import List
import requests
from pydantic import BaseModel


class AmazonScraper(BaseModel):
    category: str

    def get_all_products(self) -> List[str]:
        pass


if __name__ == '__main__':
    scraper = AmazonScraper(category='computer')
    scraper.get_all_products()
