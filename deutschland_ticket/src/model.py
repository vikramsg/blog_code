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
    id: str
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
    id: str
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


class StopDeparturesResponseModel(BaseModel):
    departures: List[Departure]
    realtimeDataUpdatedAt: int


class TravelRoute(BaseModel):
    origin: str
    destination: str
    train_line: str
    origin_id: int
    destination_id: int
    trip_id: Optional[str]

    def __hash__(self) -> int:
        # Override hash to consider only origin and destination fields
        return hash((self.origin, self.destination))

    def __eq__(self, other: Any) -> bool:
        # Override equality to consider only origin and destination fields
        if isinstance(other, TravelRoute):
            return self.origin == other.origin and self.destination == other.destination
        return False
