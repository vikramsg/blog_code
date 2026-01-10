# Introduction to Formal Methods (Part 2): From Spec to Code

In [Part 1](./intro-to-formal-methods-part-1.md), we talked about the "Why".
Why write a spec? Because English is ambiguous, and debugging design flaws in code is expensive.
We looked at **Quint** and modeled a simple TCP Handshake.
We verified that our logic was sound (no safety violations).

But as I hinted at the end of Part 1: a spec is just a file. 
If I go off and write code and ignore the spec, I haven't really gained anything.
In fact, I've just wasted time writing a spec.

In this part, we will close the loop.
We will use what is called Model-Based Testing to ensure our Python implementation behaves *exactly* like our verified spec.

## The Strategy: Trace Replay

We can't easily "compile" Quint to Python (yet).
And we probably don't want to, because the spec is an abstraction, not an implementation.
The spec doesn't care about memory management, sockets, or cache lines. 
The implementation does.

Instead, we treat the spec as a test case generator.

1.  First, generate a trace by using quint to run a simulation and save the sequence of steps (the trace) to a file.
2.  Then, we replay the trace in Python, but we instrument it so that it looks like a test.
3.  For every step in the trace (e.g., `SendSyn`), we execute the corresponding method in our Python class.
4.  Finally, after each step, we check if our Python object's state matches the spec's state.

If the test passes, we know our code handles the scenarios defined by the spec correctly.

### Step 1: Generating the Trace

In Part 1, we ran `quint run` to see text output.
Now, we want a machine-readable format. 
Quint supports the **ITF** (Json Trace Format).

```bash
quint run --mbt --max-steps=10 --out-itf=trace.itf.json tcp_simple.qnt
```

This produces a JSON file that looks roughly like this:

```json
{
  "vars": ["client_state", "server_state", "mbt::actionTaken"],
  "states": [
    { 
      "#meta": { "index": 0 }, 
      "client_state": { "tag": "INIT" }, 
      "server_state": { "tag": "INIT" },
      "mbt::actionTaken": "init"
    },
    { 
      "#meta": { "index": 1 }, 
      "client_state": { "tag": "SYN_SENT" }, 
      "server_state": { "tag": "INIT" },
      "mbt::actionTaken": "SendSyn"
    },
    ...
  ]
}
```

It captures the exact state of the system at every step.
Note that this is just *one* possible execution path. 
In the "Scaling Up" section below, we will discuss how to test against many random traces.

### Step 2: The Python Implementation

Now let's write our "production" code.
We want to make sure that **unrepresentable states** are actually unrepresentable. 
We can use **Pydantic**, **Enums**, and **Tagged Unions** for this.

```python
# tcp.py
from enum import Enum
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field

class State(str, Enum):
    INIT = "INIT"
    SYN_SENT = "SYN_SENT"
    SYN_RCVD = "SYN_RCVD"
    ESTABLISHED = "ESTABLISHED"

# We define each valid "System State" as a separate Model.
class InitState(BaseModel):
    tag: Literal["Init"] = "Init"
    client_state: Literal[State.INIT] = State.INIT
    server_state: Literal[State.INIT] = State.INIT

class SynSentState(BaseModel):
    tag: Literal["SynSent"] = "SynSent"
    client_state: Literal[State.SYN_SENT] = State.SYN_SENT
    server_state: Literal[State.INIT] = State.INIT

# ... other valid state models (SynRcvdState, FullyEstablishedState, etc.) ...

TCPState = Annotated[
    Union[InitState, SynSentState, ...], # All valid states
    Field(discriminator="tag")
]

class TCPModel:
    def __init__(self):
        self.state: TCPState = InitState()

    def send_syn(self):
        match self.state:
            case InitState():
                self.state = SynSentState()
                return True
            case _:
                return False

    # ... receive_syn, receive_syn_ack, receive_ack, etc.
```

This looks simple, but notice how the logic in `send_syn` uses Python's `match` statement?
By using specific Pydantic models for each state, it becomes impossible to even construct an invalid state (like Server being `ESTABLISHED` while Client is `INIT`). If we messed up the transition logic, the state wouldn't match the spec.

### Step 3: The Replay Test

This is the magic glue. We write a test that reads the JSON trace and drives the Python model.

```python
# test_tcp.py (simplified)
import json
from tcp import TCPModel

def main():
    with open("trace.itf.json") as f:
        trace = json.load(f)
    
    model = TCPModel()
    # Skip index 0 as it is the initial state
    for i, state_json in enumerate(trace["states"][1:], 1):
        action = state_json["mbt::actionTaken"]
        
        match action:
            case "SendSyn":
                success = model.send_syn()
            case "ReceiveSyn":
                success = model.receive_syn()
            # ... handle other actions ...
        
        if not success:
             raise Exception(f"Action {action} failed at step {i}")
             
        # Verify state matches
        assert model.state.client_state == state_json["client_state"]["tag"]
        assert model.state.server_state == state_json["server_state"]["tag"]

    print("Trace verified successfully!")
```

The test reads the action from the trace, executes it on the model, and asserts that the resulting state matches the spec.
If the implementation (Python) and the Spec (Quint) disagree, this test fails.

## Why is this powerful?

1.  **Fuzzing for Free**: Quint's random simulation generates edge cases we might forget to test manually.
2.  **Living Documentation**: The spec *is* the documentation, and the tests ensure the code respects it.
3.  **Refactoring Safety**: If we optimize the internals of `TCPModel`, as long as the external behavior (states) remains the same, the trace tests will pass.
4.  **Type Safety**: By using Tagged Unions in Python, we ensure that the code can only ever be in a valid state.

### Scaling Up

In this simple TCP example, the logic is linear, so every random trace looks identical.
However, for complex protocols, we typically run this process in a loop (generating 100+ traces).
Since Quint picks random paths, this effectively fuzzes our Python implementation against the spec.

However, note that the scale of this approach has a limit. 
More complicated specs have many different trace paths.
And we cannot possibly test again all of them. 
But testing a sample of traces is definitely better than none. 

### What about Invariants?

You might ask: "Where are we checking the invariants (like `Safety`) in the Python test?"
Well, we don't, Quint does!
During the simulation phase, if a sequence of steps leads to a violation, 
Quint reports it as a `Violation Error`.
The job of the tracing test is purely to ensure that the code conforms to the spec.
And if the code matches the spec, then we will be reasonably confident that the code is correct.

### The Caveat: We still need Unit Tests

Formal methods are great for logic and state machines, but they don't replace unit tests entirely.
Specs often abstract away details.
For example, in TLS, the spec might say:

```quint
action Encrypt = {
  encrypted_data' = encrypt(data, key)
}
```

The spec assumes `encrypt` works mathematically.
It doesn't check if your AES-GCM implementation handles padding correctly, or if you have an off-by-one error in your buffer allocation.
For those lower-level implementation details, standard unit tests are still required.
We use formal methods to verify the orchestration and logic, and unit tests to verify the primitives.

## Conclusion

We've gone from a high-level requirement ("The connection must be safe") -> Formal spec (Quint) -> Verification (Model Checking) -> Concrete Implementation (Python with Pydantic) -> Verified Code.

Instead of struggling with English and producing concrete requirements,
we can collaborate with our favourite agent to produce a spec for the set of components we are building.
And if the tooling is in place, we can just tell the agent to build the component, 
and the trace tests will make sure we adhere to the spec.
