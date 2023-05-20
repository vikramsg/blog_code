from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class Location(BaseModel):
    type: str
    id: str
    latitude: float
    longitude: float


class Products(BaseModel):
    nationalExpress: bool
    national: bool
    regionalExpress: bool
    regional: bool
    suburban: bool
    bus: bool
    ferry: bool
    subway: bool
    tram: bool
    taxi: bool


class Stop(BaseModel):
    type: str
    id: int
    name: str
    location: Location
    products: Products


class Operator(BaseModel):
    type: str
    id: str
    name: str


class Line(BaseModel):
    type: str
    id: str
    fahrtNr: str
    name: str
    public: bool
    adminCode: str
    productName: str
    mode: str
    product: str
    operator: Operator
    additionalName: str


class Destination(BaseModel):
    type: str
    id: int
    name: str
    location: Location
    products: Products


class Departure(BaseModel):
    tripId: str
    stop: Stop
    when: str
    plannedWhen: str
    delay: Optional[str]
    platform: str
    plannedPlatform: str
    prognosisType: Optional[str]
    direction: str
    provenance: Optional[str]
    line: Line
    remarks: List[str]
    origin: Optional[str]
    destination: Destination


class Stopover(BaseModel):
    stop: Stop
    arrival: Optional[str]
    plannedArrival: Optional[str]
    arrivalDelay: Optional[str]
    arrivalPlatform: Optional[str]
    arrivalPrognosisType: Optional[str]
    plannedArrivalPlatform: Optional[str]
    departure: Optional[str]
    plannedDeparture: Optional[str]
    departureDelay: Optional[str]
    departurePlatform: Optional[str]
    departurePrognosisType: Optional[str]
    plannedDeparturePlatform: Optional[str]


class Trip(BaseModel):
    origin: Stop
    destination: Stop
    departure: str
    plannedDeparture: datetime
    departureDelay: Optional[str]
    arrival: str
    plannedArrival: datetime
    arrivalDelay: Optional[str]
    line: Line
    direction: str
    arrivalPlatform: str
    plannedArrivalPlatform: str
    arrivalPrognosisType: str
    departurePlatform: str
    plannedDeparturePlatform: str
    departurePrognosisType: str
    stopovers: List[Stopover]


class TripResponseModel(BaseModel):
    trip: Trip


class TripDepartureArrival(BaseModel):
    departure: datetime
    arrival: datetime


class StopDeparturesResponseModel(BaseModel):
    departures: List[Departure]
    realtimeDataUpdatedAt: int


class TravelRoute(BaseModel):
    origin: str
    destination: str
    train_line: str
    origin_id: int
    destination_id: int
    departure: datetime
    arrival: datetime

    def __hash__(self) -> int:
        # Override hash to consider only origin and destination fields
        return hash((self.origin, self.destination))

    def __eq__(self, other: Any) -> bool:
        # Override equality to consider only origin and destination fields
        if isinstance(other, TravelRoute):
            return self.origin == other.origin and self.destination == other.destination
        return False
