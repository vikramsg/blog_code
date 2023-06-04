import json
import queue
import re
import sqlite3
from typing import Dict, List

import requests
from text_generation import InferenceAPIClient

from src.common import city_table_connection
from src.langchain_summarize import get_client, summary
from src.model import CoordinatesQueryResponse, WikiCategoryResponse, WikiPageResponse

_WIKIVOYAGE_URL = "https://en.wikivoyage.org/w/api.php"


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

        response = requests.get(_WIKIVOYAGE_URL, params=_category_query_params(category))  # type: ignore
        response_data = WikiCategoryResponse.parse_obj(response.json())
        for member in response_data.query.categorymembers:
            if member.ns == 14:
                categories.put(member.title)
            if member.ns == 0:
                pages.append(member.title)

        category_counter += 1
        print(f"Processed {category_counter} categories")

    return pages


def cities_table(
    langchain_client: InferenceAPIClient,
    page_titles: List[str],
    conn: sqlite3.Connection,
    table_name: str,
) -> None:
    """
    This uses a crude regex pattern to extract points of interest
    We should replace this with Pythia API calls from Huggingface
    or use something like geoapify
    """

    conn.execute(
        f"""
        CREATE TABLE {table_name}(
            city TEXT,
            description TEXT,
            url TEXT
        )
    """
    )

    with conn:
        cursor = conn.cursor()

        for page_title in page_titles:
            content_response = requests.get(
                _WIKIVOYAGE_URL, params=_page_query_params(page_title)
            )
            page_content = WikiPageResponse.parse_obj(content_response.json())

            # Extract the page content
            for _, page_info in page_content.query.pages.items():
                page_title = page_info.title
                page_extract = page_info.extract

                is_city = not re.search("== Regions ==", page_extract)
                if is_city:
                    city_description = summary(
                        langchain_client, page_extract, page_title
                    )
                    city_description_json = json.dumps(city_description)

                    print(f"Writing info for {page_title} city.")
                    cursor.execute(
                        f"INSERT INTO {table_name} (city, description, url) VALUES (?, ?, ?)",
                        (
                            page_title,
                            city_description_json,
                            _create_url_from_page_id(page_info.pageid),
                        ),
                    )

    conn.close()


if __name__ == "__main__":
    # Get all pages under the category Germany
    pages = parse_category_page()

    langchain_client = get_client()
    conn = city_table_connection(table_name="cities")
    cities_table(langchain_client, pages, conn, table_name="cities")
