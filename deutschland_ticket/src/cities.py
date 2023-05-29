import queue
from typing import Dict, List

import requests

from src.model import WikiCategoryResponse

_WIKI_URL = "https://en.wikivoyage.org/w/api.php"


def _category_query_params(category: str) -> Dict:
    return {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 500,
    }


def parse_category_page() -> List[str]:
    """
    Create a queue that goes down all subcategories of the Germany category
    Process the queue to get all pages within all subcategories
    """
    categories = queue.Queue()  # type: ignore
    categories.put("Category:Germany")

    pages = []

    i: int = 0
    while not categories.empty():
        category = categories.get()

        response = requests.get(_WIKI_URL, params=_category_query_params(category))  # type: ignore
        response_data = WikiCategoryResponse.parse_obj(response.json())
        for member in response_data.query.categorymembers:
            if member.ns == 14:
                categories.put(member.title)
            if member.ns == 0:
                pages.append(member.title)

        i += 1
        print(f"Processed {i} categories")

    return pages


def temp_parse() -> None:
    # Set the parameters for retrieving page content
    content_params = {
        "action": "query",
        "format": "json",
        # "titles": page_title,
        "prop": "extracts",
        "explaintext": True,
    }

    # Send a GET request to retrieve the page content
    content_response = requests.get(_WIKI_URL, params=content_params)
    content_data = content_response.json()

    # Extract the page content
    pages = content_data["query"]["pages"]
    for _, page_info in pages.items():
        page_title = page_info["title"]
        page_extract = page_info["extract"]

        # Print the page title and plain text extract
        print(f"Page Title: {page_title}")
        print(f"Extract: {page_extract}")
        print()

    # FIXME: This is temporary
    return


if __name__ == "__main__":
    pages = parse_category_page()
    print(pages)
