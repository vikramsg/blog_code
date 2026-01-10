# Introduction to Formal Methods (Part 1): Why Spec First?

Formal methods, sounds very... formal!
But I have been trying to dive a bit into what they are and so I decided to write down my learnings.
Hopefully this proves a good starting point for someone else who was curious about the idea but didn't have a good starting point.

This post is part 1 of 2. 
In part 1, I will try to give a more conceptual understanding, while also introducing tooling using `Quint`.
In part 2, I will try to show how it can be wired up so that we make sure software implementations actually benefit from formal methods.

## The Problem with English (and AI)

First a warning, and then if you stick around, we can go deeper.
My dive into formal methods was motivated by posts like [this](https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html).
I have been increasingly using AI/Agents and I believe something is required to make the use of AI more productive. 
And if the word AI is triggering, then this would be a good time to stop reading.
If you are still here, let's talk about AI a little bit, and the programming language for AI - English.

We prompt agents in English. We write requirements documents in English.
- "The user is authenticated after a successful handshake."
- "The program is crashing. Fix it."

But English is inherently ambiguous. What "program"? What exactly constitutes a "successful handshake"? Are we talking about a human handshake? 

When we jump straight to code based on English prompts, the *implementation* becomes the specification. 
If the Agent guesses wrong, that guess can lead to some very complicated code. 
And cue the inevitable conversation, 

```json
{
  "user": "This isn't what I meant",
  "agent": "You are absolutely right. You are amazing. I will fix it....."
  ... 
  ...
  "agent": "Here's the updated code."
  "user": "That's still wrong".
}
```

If that feels familiar, hopefully the following points to a way forward. 

1. More and more software will be written by AI.
2. That leaves me, the human, needing to somehow verify that the software is correct, but I don't have the ability to read thousands of lines of code constantly.
3. But what if we had the ability to define the system with a much smaller volume of text that I can read and verify and have the confidence that if the software meets this spec, it is correct. 

## The Scary Part: TLA+

This isn't a new problem. 
Decades ago, Leslie Lamport (the creator of LaTeX and distributed systems legend) gave us [TLA+](https://en.wikipedia.org/wiki/TLA%2B) (Temporal Logic of Actions).
It is the gold standard for formal verification. 
It is used by AWS to design DynamoDB and S3. It is used by Azure. It works.

But then I looked at TLA+. 
And this is what it looks like.

```tla
Total ==
  LET S == { r[type] : r \in Records }
  IN  Cardinality(S)

Inv == \A r \in Records : r.amount >= 0
```

Yes, if you are thinking that looks like LaTeX, that's exactly how I felt.
Don't get me wrong, I loved LaTeX back when I was in Graduate School.
There's nothing better to write equations.
But if we could write equations (and the other stuff required to write a paper or thesis) in Python, I would take Python over LaTeX anyday.
And my job does not involve equations (most of the time).
Ultimately, if the spec is harder to read than the code, the spec is almost never going to be written.

## Enter Quint

This is where [Quint](https://github.com/informalsystems/quint) comes in.
It is TLA+ for humans, or software engineers (who are also humans for now). 
It looks way closer to something like TypeScript than LaTeX.
I think if you can read code, you can read Quint.

### A Concrete Example: The TCP Handshake

To understand what we can do with this, let's look at something a lot of us know and understand: the TCP 3-way handshake.
We want to verify that a client and server can establish a connection correctly.

In code, we'd worry about packets, sequence numbers, buffers, and timeouts.
In a spec, we worry about **State** and **Transitions**.

#### 1. Modeling State

We define the universe of our protocol.

```quint
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
```

#### 2. Defining Actions (Transitions)

Next, we define what *can* happen. These are the rules of the road.

```quint
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
}
```

This is very readable. 
Now, let's go over what the snippet says.
First note that there is no explicit ordering.
We are not saying "Run `SendSyn` then `ReceiveSyn`".

In Quint, these actions are a menu of choices.
At every step, the system (the Quint simulator) asks: "Which of these actions is allowed to happen right now?",
for example,
at the beginning everyone is `INIT`.

-   Can `ReceiveSyn` happen? No. It requires `client_state == SYN_SENT`.
-   Can `SendSyn` happen? Yes. It requires `client_state == INIT`.
-   So, the simulator picks `SendSyn`.

The order isn't hardcoded. The order emerges from the logic.

#### 3. Simulation

Unlike a static diagram, we can **run** this.
Quint has a built-in simulator. 
We can ask it: "Run this logic for 10 steps and see what happens."

```bash
quint run --max-steps=10 tcp_simple.qnt
```

It will execute the actions randomly, effectively "fuzzing" our design logic. 
It produces a trace:
`Init -> SendSyn -> ReceiveSyn -> ReceiveSynAck ...`

#### 4. Invariants (The Guardrails)

This is the superpower. We can define properties that must **always** be true.

For example, we might want to assert that the Server never thinks the connection is established before the Client has at least initiated it.

```quint
val Safety = not (server_state == ESTABLISHED and client_state == INIT)
```

If we run the simulator (or the model checker), and it finds a sequence of events that leads to this invalid state, it reports a **Violation**.
It gives us the exact trace of steps that caused the bug.
We fix the logic in the spec, long before we've written a single line of C or Rust or Mojo.

### Recap

To summarize, with Quint we get:
1.  **A Readable Spec**: A precise description of the system (State & Transitions) that is easy to read.
2.  **Simulation**: A way to run the spec and explore behaviors (like fuzzing).
3.  **Invariants**: A way to define properties that must *always* be true.

## What's Next?

So we have a verified spec. 
We know our logic is sound. 
We know that our state machine respects our safety properties.

But a spec in a file is just some text (or outdated documentation!). 
How do we ensure our *actual* code implements this logic correctly?

In **Part 2**, we will explore how to make sure the code follows the spec.
