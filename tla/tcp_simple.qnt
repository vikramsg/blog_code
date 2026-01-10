module tcp_simple {
  // Types
  type State = INIT | SYN_SENT | SYN_RCVD | ESTABLISHED

  // State Variables
  var client_state: State
  var server_state: State

  // Initial State
  action init = all {
    client_state' = INIT,
    server_state' = INIT,
  }

  // Client sends SYN
  action SendSyn = all { // 'all' means all statements must hold true (Logical AND)
    client_state == INIT,        // Precondition: Client must be INIT
    client_state' = SYN_SENT,    // Transition: Client moves to SYN_SENT (Note the ' for next state)
    server_state' = server_state // Server state doesn't change yet
  }

  // Server receives SYN, sends SYN-ACK
  action ReceiveSyn = all {
    server_state == INIT,
    client_state == SYN_SENT, // Wait for Client to send SYN
    server_state' = SYN_RCVD,
    client_state' = client_state
  }

  // Client receives SYN-ACK, sends ACK
  action ReceiveSynAck = all {
    client_state == SYN_SENT,
    server_state == SYN_RCVD,
    client_state' = ESTABLISHED,
    server_state' = server_state
  }

  // Server receives ACK
  action ReceiveAck = all {
    server_state == SYN_RCVD,
    client_state == ESTABLISHED,
    server_state' = ESTABLISHED,
    client_state' = client_state
  }

  // The step action defines the transitions that can happen
  action step = any {
    SendSyn,
    ReceiveSyn,
    ReceiveSynAck,
    ReceiveAck,
  }

  // Invariants
  val Safety = not (server_state == ESTABLISHED and client_state == INIT)
}
