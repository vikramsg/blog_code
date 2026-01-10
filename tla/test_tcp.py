import json
import os
import sys
from tcp import TCPModel, State

def main():
    trace_path = os.getenv("QUINT_TRACE_PATH", "trace.itf.json")
    if not os.path.exists(trace_path):
        print(f"Trace file {trace_path} not found. Run quint first.")
        sys.exit(1)

    with open(trace_path, "r") as f:
        trace = json.load(f)

    states = trace["states"]
    model = TCPModel()

    print("Initial state verified.")

    for i in range(1, len(states)):
        state_json = states[i]
        action = state_json["mbt::actionTaken"]
        
        print(f"Step {i}: Applying {action}")
        
        success = False
        match action:
            case "SendSyn":
                success = model.send_syn()
            case "ReceiveSyn":
                success = model.receive_syn()
            case "ReceiveSynAck":
                success = model.receive_syn_ack()
            case "ReceiveAck":
                success = model.receive_ack()
            case "init":
                success = True
            case _:
                print(f"Unknown action: {action}")
                sys.exit(1)

        if not success:
            print(f"Action {action} failed at step {i}")
            sys.exit(1)

        # Verify state
        expected_client = state_json["client_state"]["tag"]
        expected_server = state_json["server_state"]["tag"]
        
        if model.state.client_state != expected_client:
            print(f"Client mismatch: {model.state.client_state} != {expected_client}")
            sys.exit(1)
        if model.state.server_state != expected_server:
            print(f"Server mismatch: {model.state.server_state} != {expected_server}")
            sys.exit(1)

    print("Python Trace verified successfully!")

if __name__ == "__main__":
    main()
