from typing import List
import requests

from src.model import StopDeparturesResponseModel, TravelRoute


def get_trip_info(trip_id: str) -> None:
    pass


def get_departures(stop_id: int) -> List[TravelRoute]:
    url = (
        f"https://v6.db.transport.rest/stops/{stop_id}/departures?"
        "duration=120&bus=false&national=false&nationalExpress=false&suburban=false&subway=false&when=2023-05-20T08:00"
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

        travel_route = TravelRoute(
            origin=orig_name,
            origin_id=orig_id,
            destination=destination_name,
            destination_id=destination_id,
            train_line=line_name,
            trip_id=trip_id,
        )
        travel_routes.add(travel_route)

    return list(travel_routes)


if __name__ == "__main__":
    hamburg_stop_id = 8002549
    # ToDo: We are not getting travel time or arrival time?
    # to get departure and arrival time, we will have to
    # call the trip api
    travel_routes = get_departures(hamburg_stop_id)
    print(travel_routes)
