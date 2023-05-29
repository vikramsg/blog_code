import json
import queue
import re
import sqlite3
from pathlib import Path
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
        "inprop": "url",
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
                    point_str = f"{point_of_interest.group(1)}.{rest.group(0)[1:]}"
                else:
                    point_str = point_of_interest.group(1)
                points_of_interest.append(point_str)

    else:
        print("No '== See ==' section found.")

    return points_of_interest


def _city_table_connection() -> sqlite3.Connection:
    db_path = Path(".").resolve() / "data" / "cities.db"
    conn = sqlite3.connect(db_path)

    # Create the table with a json_array column
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cities(
            city TEXT,
            places_to_see TEXT,
            url TEXT
        )
    """
    )

    return conn


def _create_url_from_page_id(page_id: int) -> str:
    return f"https://en.wikivoyage.org/?curid={page_id}"


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


def cities_table(page_titles: List[str], conn: sqlite3.Connection) -> None:
    """
    This uses a crude regex pattern to extract points of interest
    We should replace this with Pythia API calls from Huggingface
    or use something like geoapify
    """
    with conn:
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

                    places_to_see_json = json.dumps(points_of_interest)

                    conn.execute(
                        "INSERT INTO cities (city, places_to_see, url) VALUES (?, ?, ?)",
                        (
                            page_title,
                            places_to_see_json,
                            _create_url_from_page_id(page_info.pageid),
                        ),
                    )

    conn.close()


if __name__ == "__main__":
    # pages = parse_category_page()
    # print(pages, len(pages))
    conn = _city_table_connection()
    cities_table(["Hamburg", "Lübeck", "Baltic Sea Coast (Germany)"], conn)
