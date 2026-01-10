from enum import Enum
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, RootModel, ValidationError

class State(str, Enum):
    INIT = "INIT"
    SYN_SENT = "SYN_SENT"
    SYN_RCVD = "SYN_RCVD"
    ESTABLISHED = "ESTABLISHED"

# We define each valid "System State" as a separate Model.
# This makes invalid combinations (like Server=ESTABLISHED, Client=INIT) 
# UNREPRESENTABLE in these types.

class InitState(BaseModel):
    tag: Literal["Init"] = "Init"
    client_state: Literal[State.INIT] = State.INIT
    server_state: Literal[State.INIT] = State.INIT

class SynSentState(BaseModel):
    tag: Literal["SynSent"] = "SynSent"
    client_state: Literal[State.SYN_SENT] = State.SYN_SENT
    server_state: Literal[State.INIT] = State.INIT

class SynRcvdState(BaseModel):
    tag: Literal["SynRcvd"] = "SynRcvd"
    client_state: Literal[State.SYN_SENT] = State.SYN_SENT
    server_state: Literal[State.SYN_RCVD] = State.SYN_RCVD

class ClientEstablishedState(BaseModel):
    tag: Literal["ClientEstablished"] = "ClientEstablished"
    client_state: Literal[State.ESTABLISHED] = State.ESTABLISHED
    server_state: Literal[State.SYN_RCVD] = State.SYN_RCVD

class FullyEstablishedState(BaseModel):
    tag: Literal["FullyEstablished"] = "FullyEstablished"
    client_state: Literal[State.ESTABLISHED] = State.ESTABLISHED
    server_state: Literal[State.ESTABLISHED] = State.ESTABLISHED

# The "Network" state can ONLY be one of these 5 specific valid combinations.
TCPState = Annotated[
    Union[InitState, SynSentState, SynRcvdState, ClientEstablishedState, FullyEstablishedState],
    Field(discriminator="tag")
]

class TCPModel:
    def __init__(self):
        # We start in a valid InitState
        self.state: TCPState = InitState()

    def send_syn(self):
        match self.state:
            case InitState():
                self.state = SynSentState()
                return True
            case _:
                return False

    def receive_syn(self):
        match self.state:
            case SynSentState():
                self.state = SynRcvdState()
                return True
            case _:
                return False

    def receive_syn_ack(self):
        match self.state:
            case SynRcvdState():
                self.state = ClientEstablishedState()
                return True
            case _:
                return False

    def receive_ack(self):
        match self.state:
            case ClientEstablishedState():
                self.state = FullyEstablishedState()
                return True
            case _:
                return False

    def __repr__(self):
        return f"TCPModel(client={self.state.client_state}, server={self.state.server_state})"

if __name__ == "__main__":
    model = TCPModel()
    print(f"Start: {model}")
    
    model.send_syn()
    print(f"After SendSyn: {model}")
    
    # Attempting an "unrepresentable" state transition or manual corruption
    print("\n--- Testing Protection ---")
    try:
        # Pydantic prevents creating an invalid state object
        # e.g. Server Established but Client INIT
        invalid = FullyEstablishedState(client_state=State.INIT, server_state=State.ESTABLISHED)
    except ValidationError as e:
        print(f"Successfully blocked invalid state creation: {e.errors()[0]['msg']}")
