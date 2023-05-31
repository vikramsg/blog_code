import json
from datetime import datetime
from sqlite3 import Connection
from typing import Any, Dict, List, Optional

import pydantic
import requests

from src.common import city_table_connection, session_with_retry
from src.model import (
    JourneyResponse,
    Stop,
    StopDeparturesResponseModel,
    TravelRoute,
    TripDepartureArrival,
    TripResponseModel,
)


def _journey_params(origin_id: int, destination_id: int) -> Dict:
    return {
        "from": origin_id,
        "to": destination_id,
        "bus": "false",
        "national": "false",
        "nationalExpress": "false",
        "suburban": "false",
        "subway": "false",
    }


def _get_trip_departure_arrival(trip_id: str) -> TripDepartureArrival:
    url = f"https://v6.db.transport.rest/trips/{trip_id}"

    response = requests.get(url)
    json_response = response.json()

    # Parse and validate the JSON response using the ResponseModel
    response_model = TripResponseModel.parse_obj(json_response)

    trip = response_model.trip
    planned_departure = trip.plannedDeparture
    planned_arrival = trip.plannedArrival

    return TripDepartureArrival(departure=planned_departure, arrival=planned_arrival)


def get_departures(stop_id: int) -> List[TravelRoute]:
    url = (
        f"https://v6.db.transport.rest/stops/{stop_id}/departures?"
        "duration=120&bus=false&national=false&nationalExpress=false&suburban=false&subway=false&when=2023-05-20T07:00"
    )

    response = requests.get(url)
    json_response = response.json()

    # Parse and validate the JSON response using the ResponseModel
    response_model = StopDeparturesResponseModel.parse_obj(json_response)

    # Access the data from the response model
    departures = response_model.departures

    travel_routes = set()
    # Print the first departure's tripId as an example
    for departure in departures:
        orig_name = departure.stop.name
        orig_id = departure.stop.id
        line = departure.line
        line_name = line.name
        destination_name = departure.destination.name
        destination_id = departure.destination.id
        trip_id = departure.tripId
        trip_departure_arrival = _get_trip_departure_arrival(trip_id)

        travel_route = TravelRoute(
            origin=orig_name,
            origin_id=orig_id,
            destination=destination_name,
            destination_id=destination_id,
            train_line=line_name,
            departure=trip_departure_arrival.departure,
            arrival=trip_departure_arrival.arrival,
        )
        travel_routes.add(travel_route)

    return list(travel_routes)


def _get_hours_minutes(date_time: datetime) -> str:
    return date_time.time().strftime("%H:%M")


def _location(city_query: str) -> Optional[int]:
    """
    Returns stop id for the given city

    The transport API has weird issues
    1. It only unblocks after timeout is reached
    2. It blocks if query params are used as params instead of in url
    """
    location_url = (
        f"https://v6.db.transport.rest/locations?query={city_query}&results=1"
    )
    request_session = session_with_retry()
    location_response = request_session.get(location_url, timeout=1)

    try:
        stop_response = Stop.parse_obj(location_response.json()[0])
    except pydantic.error_wrappers.ValidationError:
        print(f"Could not resolve {city_query}. Skipping.")
        return None

    return stop_response.id


def get_city_stops(conn: Connection, input_table: str, output_table: str) -> None:
    conn.execute(
        f"""CREATE TABLE {output_table}(
            city TEXT,
            stop_id INTEGER
        )
        """
    )
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT city from {input_table}")

        cities = cursor.fetchall()

        for city in cities:
            city_name = city[0]
            print(f"Processing stop ID for city: {city_name}")
            stop_id = _location("+".join(city_name.split()))

            if stop_id:
                cursor.execute(
                    f"INSERT INTO {output_table} (city, stop_id) VALUES (?, ?)",
                    (city[0], stop_id),
                )

    return


def _journey(origin: int, destination: int) -> Optional[List[List[Any]]]:
    url = (
        "https://v6.db.transport.rest/journeys"
        "?from="
        f"{origin}"
        "&to="
        f"{destination}"
        "&bus=false"
        "&national=false"
        "&nationalExpress=false"
        "&suburban=false"
        "&subway=false"
        "&departure=2023-05-27T05:00"
    )

    request_session = session_with_retry()
    try:
        response = request_session.get(url, timeout=1)

        journey_response = JourneyResponse.parse_obj(response.json())

        journey_summary = []
        if journey_response.journeys:
            for journey in journey_response.journeys:
                leg_summary = []
                for leg in journey.legs:
                    line_name = leg.line.name if leg.line else None
                    leg_summary.append(
                        (
                            leg.origin.name,
                            leg.plannedDeparture,
                            leg.destination.name,
                            leg.plannedArrival,
                            line_name,
                        )
                    )
                journey_summary.append(leg_summary)

            return journey_summary
        else:
            return None
    # Even with backoff, if it does not work, then we just ignore it
    except requests.exceptions.ConnectionError:
        print("Timeout occured. Returning None.")
        return None


def hamburg_journeys(conn: Connection, input_table: str, output_table: str) -> None:
    hamburg_stop_id = 8096009

    conn.execute(
        f"""CREATE TABLE {output_table}(
            city TEXT,
            journey TEXT
        )
        """
    )
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT city, stop_id from {input_table}")

        table_output = cursor.fetchall()
        cities = [city_stop[0] for city_stop in table_output]
        stop_ids = [city_stop[1] for city_stop in table_output]

        for it, destination_stop_id in enumerate(stop_ids):
            print(
                f"Processing journey to city: {cities[it]} with stop id: {destination_stop_id}"
            )
            journey_summary = _journey(hamburg_stop_id, destination_stop_id)

            if journey_summary:
                journey_summary_json = json.dumps(journey_summary)

                cursor.execute(
                    f"INSERT INTO {output_table} (city, journey) VALUES (?, ?)",
                    (cities[it], journey_summary_json),
                )

    return


if __name__ == "__main__":
    # hamburg_stop_id = 8002549
    # travel_routes = get_departures(hamburg_stop_id)
    # for route in travel_routes:
    #     print(
    #         f"Origin: {route.origin}, Destination: {route.destination}, Train: {route.train_line},"
    #         f" Departure: {_get_hours_minutes(route.departure)}, Arrival: {_get_hours_minutes(route.arrival)}"
    #     )

    # conn = city_table_connection("city_stops")
    # get_city_stops(conn, "cities_lat_lon", "city_stops")

    conn = city_table_connection("hamburg_journeys")
    hamburg_journeys(conn, "city_stops", "hamburg_journeys")

    # ToDo
    # 1. Run through cities tables and get stop ids of each
