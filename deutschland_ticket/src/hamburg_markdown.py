import json
from datetime import datetime, timedelta
from sqlite3 import Connection

from src.common import city_table_connection


def join_cities_journeys(
    conn: Connection, cities_table: str, hamburg_journeys_table: str, joined_table: str
) -> None:
    conn.execute(f"DROP TABLE IF EXISTS {joined_table}")

    conn.execute(
        f"""CREATE TABLE {joined_table} AS
        SELECT {cities_table}.city as city,
        {cities_table}.places_to_see as places_to_see,
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


def hamburg_destinations_markdown(
    conn: Connection, hamburg_destinations_table: str, output_file: str
) -> None:
    with conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT city, places_to_see, url, journey, journey_time FROM {hamburg_destinations_table}"
        )

        markdown_str = ""

        row = cursor.fetchone()
        while row is not None:
            city, places_to_see, url, journey, journey_time = row

            places_to_see_str = ", ".join(json.loads(places_to_see))

            delta = timedelta(seconds=journey_time)

            journey_with_legs = json.loads(journey)
            first_journey = journey_with_legs[0]

            journey_str = ""
            for it, leg in enumerate(first_journey):
                departure_time = datetime.fromisoformat(leg[1]).strftime("%H:%M")
                arrival_time = datetime.fromisoformat(leg[3]).strftime("%H:%M")
                journey_str += (
                    f"  \n\n**Leg {it}**  \n**Origin**: {leg[0]}  \n"
                    f"**Destination**: {leg[2]}  \n"
                    f"**Departure**: {departure_time}  \n"
                    f"**Arrival**: {arrival_time}  \n"
                    f"**Train**: {leg[4]}\n"
                )

            markdown_str += (
                f"## [{city}]({url})\n\n"
                f"**Journey time** is {delta}.\n\n"
                f"Places to visit are {places_to_see_str}.\n\n"
                f"Example journey would be {journey_str}\n\n"
            )

            row = cursor.fetchone()
    conn.close()

    with open(output_file, "w") as file_write:
        file_write.write(markdown_str)


if __name__ == "__main__":
    cities_table = "cities"
    hamburg_journeys_table = "hamburg_journeys"
    joined_table = "hamburg_destinations"

    conn = city_table_connection()
    join_cities_journeys(conn, cities_table, hamburg_journeys_table, joined_table)

    output_file = "markdown/hamburg.md"
    conn = city_table_connection()
    hamburg_destinations_markdown(conn, joined_table, output_file)
