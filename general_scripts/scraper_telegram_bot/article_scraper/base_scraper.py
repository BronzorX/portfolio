from pprint import pprint
from typing import List

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


class GenericScraper(BaseModel):

    def extract_links_from_link(self, link: str) -> List[str]:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a"):
            link_obj = link.get("href")
            if (link_obj and not link_obj.endswith(('.jpg', '.gif', '.png', '.jpeg'))
                    and link_obj.startswith(('http', 'https'))):
                yield link_obj
