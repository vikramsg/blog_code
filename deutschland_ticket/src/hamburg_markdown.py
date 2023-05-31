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
    conn: Connection, hamburg_destinations_table: str
) -> None:
    with conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT city, places_to_see, url, journey, journey_time FROM {hamburg_destinations_table}"
        )

        row = cursor.fetchone()
        while row is not None:
            city, places_to_see, url, journey, journey_time = row
            print(row)

            # FIXME: Remove
            break
            row = cursor.fetchone()


if __name__ == "__main__":
    cities_table = "cities"
    hamburg_journeys_table = "hamburg_journeys"
    joined_table = "hamburg_destinations"

    # conn = city_table_connection()
    # join_cities_journeys(conn, cities_table, hamburg_journeys_table, joined_table)

    conn = city_table_connection()
    hamburg_destinations_markdown(conn, joined_table)
