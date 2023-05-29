import queue
import re
from typing import Dict, List

import requests

from src.model import WikiCategoryResponse, WikiPageResponse

_WIKI_URL = "https://en.wikivoyage.org/w/api.php"


def _category_query_params(category: str) -> Dict:
    return {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 500,
    }


def _page_query_params(page_title: str) -> Dict:
    return {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "extracts",
        "explaintext": True,
    }


def _get_points_of_interest(page_extract: str) -> List[str]:
    points_of_interest = []

    match = re.search("== See ==", page_extract)
    if match:
        start_index = match.end()
        # Find the start and end positions of the next section (or end of string)
        next_match = re.search(r"\n==\s+(\w+)\s+==\n|\Z", page_extract[start_index:])
        end_index = (
            len(page_extract)
            if next_match is None
            else start_index + next_match.start()
        )

        # Extract the text under the "== See ==" section
        see_section = page_extract[start_index:end_index].strip()

        # Extract the points of interest using a regex pattern
        for line in see_section.splitlines():
            point_of_interest = re.search(r"\d+\s(.*?)\.", line)

            if point_of_interest:
                if point_of_interest.group(1) == "St":
                    rest = re.search(r"\.+.*?(\.+)", line)
                    point_str = "St.", rest.group(0)[1:]
                else:
                    point_str = point_of_interest.group(1)
                points_of_interest.append(point_str)

    else:
        print("No '== See ==' section found.")

    return points_of_interest


def parse_category_page() -> List[str]:
    """
    Create a queue that goes down all subcategories of the Germany category
    Process the queue to get all pages within all subcategories
    """
    categories = queue.Queue()  # type: ignore
    categories.put("Category:Germany")

    pages = []

    category_counter: int = 0
    while not categories.empty():
        category = categories.get()

        response = requests.get(_WIKI_URL, params=_category_query_params(category))  # type: ignore
        response_data = WikiCategoryResponse.parse_obj(response.json())
        for member in response_data.query.categorymembers:
            if member.ns == 14:
                categories.put(member.title)
            if member.ns == 0:
                pages.append(member.title)

        category_counter += 1
        print(f"Processed {category_counter} categories")

    return pages


def parse_pages(page_titles: List[str]) -> None:
    """
    This uses a crude regex pattern to extract points of interest
    We should replace this with Pythia API calls from Huggingface
    or use something like geoapify
    """
    for page_title in page_titles:
        content_response = requests.get(
            _WIKI_URL, params=_page_query_params(page_title)
        )
        page_content = WikiPageResponse.parse_obj(content_response.json())

        # Extract the page content
        for _, page_info in page_content.query.pages.items():
            page_title = page_info.title
            page_extract = page_info.extract

            is_city = not re.search("== Regions ==", page_extract)
            if is_city:
                points_of_interest = _get_points_of_interest(page_extract)

                # If it is city, we will store city name, url
                # And places to see


if __name__ == "__main__":
    # pages = parse_category_page()
    # print(pages, len(pages))
    parse_pages(["Hamburg", "Lübeck", "Baltic Sea Coast (Germany)"])
