import json
from sqlite3 import Connection

from src.common import city_table_connection

"""
WITH hamburg_stop AS
(
    SELECT stop_id FROM city_stops WHERE city='Hamburg'
),
hamburg_destinations AS
(
    SELECT cities.city as city,
    cities.description as description,
    cities.url as url,
    hamburg_journeys.journey_time as journey_time
    FROM cities
    JOIN hamburg_journeys
    ON cities.city = hamburg_journeys.city
),
hamburg_destinations_stops AS
(
    SELECT hamburg_destinations.city as city,
--    hamburg_destinations.description as description,
    hamburg_destinations.url as url,
    hamburg_destinations.journey_time as journey_time,
    city_stops.stop_id as destination_stop,
    hamburg_stop.stop_id as destination_stop
    FROM hamburg_destinations
    JOIN city_stops
    ON hamburg_destinations.city = city_stops.city
    CROSS JOIN hamburg_stop
)
SELECT * FROM hamburg_destinations_stops;
"""


def join_cities_journeys(
    conn: Connection, cities_table: str, hamburg_journeys_table: str, joined_table: str
) -> None:
    conn.execute(f"DROP TABLE IF EXISTS {joined_table}")

    conn.execute(
        f"""CREATE TABLE {joined_table} AS
        SELECT {cities_table}.city as city,
        {cities_table}.description as description,
        {cities_table}.url as url,
        {hamburg_journeys_table}.journey as journey,
        {hamburg_journeys_table}.journey_time as journey_time
        FROM {cities_table}
        JOIN {hamburg_journeys_table}
        ON {cities_table}.city = {hamburg_journeys_table}.city
        ORDER BY journey_time ASC
    """
    )

    conn.close()


def hamburg_destinations_json(
    conn: Connection, hamburg_destinations_table: str, output_file: str
) -> None:
    with conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT city, description, url, journey_time FROM {hamburg_destinations_table}"
        )

        json_list = []
        row = cursor.fetchone()
        while row is not None:
            city, description, url, journey_time = row
            json_list.append(
                {
                    "city": city,
                    "description": description,
                    "url": url,
                    "journey_time": journey_time,
                }
            )

            row = cursor.fetchone()
    conn.close()

    with open(output_file, "w") as file_write:
        json.dump({"cities": json_list}, file_write)


if __name__ == "__main__":
    cities_table = "cities"
    hamburg_journeys_table = "hamburg_journeys"
    joined_table = "hamburg_destinations"

    conn = city_table_connection()
    join_cities_journeys(conn, cities_table, hamburg_journeys_table, joined_table)

    output_file = "data/hamburg.json"
    conn = city_table_connection()
    hamburg_destinations_json(conn, joined_table, output_file)
