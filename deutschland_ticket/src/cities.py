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
_WIKIPEDIA_URL = "https://en.wikipedia.org/w/api.php"


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


def _coordinate_query_params(city: str) -> Dict:
    return {
        "action": "query",
        "format": "json",
        "titles": city,
        "prop": "coordinates",
    }


def _get_points_of_interest(page_title: str, page_extract: str) -> List[str]:
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
                    if rest:
                        point_str = f"{point_of_interest.group(1)}.{rest.group(0)[1:]}"
                    else:
                        raise ValueError("Name should not be None")
                else:
                    point_str = point_of_interest.group(1)
                points_of_interest.append(point_str)

    else:
        print(f"No '== See ==' section found for city: {page_title}.")

    return points_of_interest


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
            places_to_see TEXT,
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
                    places_to_see_json = json.dumps(city_description)

                    print(f"Writing info for {page_title} city.")
                    cursor.execute(
                        f"INSERT INTO {table_name} (city, places_to_see, url) VALUES (?, ?, ?)",
                        (
                            page_title,
                            places_to_see_json,
                            _create_url_from_page_id(page_info.pageid),
                        ),
                    )


# conn.close()


def cities_lat_lon(
    conn: sqlite3.Connection, input_table: str, output_table: str
) -> None:
    """
    Scrape Wikipedia for the same cities to get co-ordinates
    """
    conn.execute(
        f"""
        CREATE TABLE {output_table}(
            city TEXT,
            lat REAL,
            lon REAL
        )
    """
    )

    with conn:
        cursor = conn.cursor()

        cursor.execute(f"SELECT city FROM {input_table}")
        cities = cursor.fetchall()

        for city in cities:
            print(f"Querying co-ordinates for city: {city[0]}")
            content_response = requests.get(
                _WIKIPEDIA_URL, params=_coordinate_query_params(city)
            )
            city_coords_resp = CoordinatesQueryResponse.parse_obj(
                content_response.json()
            )

            for _, page in city_coords_resp.query.pages.items():
                if page.coordinates:
                    # If we don't find co-ordinates don't put in table
                    cursor.execute(
                        f"INSERT INTO {output_table} (city, lat, lon) VALUES (?, ?, ?)",
                        (city[0], page.coordinates[0].lat, page.coordinates[0].lon),
                    )

    conn.close()


if __name__ == "__main__":
    # Get all pages under the category Germany
    # pages = parse_category_page()

    # Create cities table with city name and places of interest
    # FIXME: Remove
    pages = ["Osnabrück", "Sassnitz"]
    langchain_client = get_client()
    conn = city_table_connection(table_name="cities")
    cities_table(langchain_client, pages, conn, table_name="cities")

    # Use the existing db to get cities in the cities table
    # Scrape wikipedia to get lat lon and create new table
    # conn = city_table_connection(table_name="cities_lat_lon")
    # cities_lat_lon(conn, input_table="cities", output_table="cities_lat_lon")

    # ToDo
    # 1. Run to create the tables
    #   a. Check if it works
    # 2. Create query for from: to: based on co-ordinates from Hamburg
    # 3. Create Markdown string for each destination
    # 4. Put Markdown on Vercel and test if it reads
