# agentv6_persistence_checkpointer

This version introduces **LangGraph persistence using a checkpointer**.

Graph:

```text
START → assistant → END
```

The graph itself is intentionally simple.

The focus of this version is not routing or tools.
The focus is **durable state management**.

---

# Learning Goals

* Understand why `agentv5_state_memory` is not durable
* Compile a graph with a checkpointer
* Understand `thread_id`
* Understand how LangGraph loads prior state
* Understand how `add_messages` works with persistence
* Inspect checkpointed state
* Observe persisted conversations in LangSmith

---

# Setup

Use the root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

Required `.env` values:

```env
OPENAI_API_KEY=your_openai_api_key

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=langgraph-playground
```

---

# Core Concept

This version introduces:

```text
thread_id + checkpointer = durable conversation state
```

This is one of the most important LangGraph concepts.

---

# v5 vs v6

## agentv5_state_memory

You manually carried conversation history.

Example:

```python
history = state1["messages"]

state2 = graph.invoke({
    "messages": history + [
        HumanMessage(content="What is my name?")
    ]
})
```

You were responsible for preserving history.

If the notebook or process restarts:

```text
history is lost
```

---

## agentv6_persistence_checkpointer

LangGraph stores and reloads state automatically.

Example:

```python
config = {
    "configurable": {
        "thread_id": "sam-demo-thread"
    }
}

state = graph.invoke(
    {"messages": [HumanMessage(content="What is my name?")]},
    config=config,
)
```

Now you only pass the **new message**.

LangGraph loads previous messages automatically.

---

# Important Question: Does config map to messages?

No.

This is a very important distinction.

## AgentState

Your graph state is:

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

This is the actual workflow state.

Example:

```python
{
    "messages": [...]
}
```

---

## Config

Config is separate.

Example:

```python
{
    "configurable": {
        "thread_id": "sam-demo-thread"
    }
}
```

This is runtime metadata.

It does **not** become part of `AgentState`.

---

# What does thread_id do?

`thread_id` identifies a persisted conversation.

Example:

```python
thread_id = "sam-demo-thread"
```

Think of it as a key.

```text
thread_id → saved conversation state
```

Same `thread_id`:

```text
continue existing conversation
```

Different `thread_id`:

```text
start separate conversation
```

---

# Mental Model: Checkpoint Store

Checkpoint storage behaves roughly like this:

```python
checkpoint_store = {
    thread_id_1: AgentState(...),
    thread_id_2: AgentState(...),
    thread_id_3: AgentState(...),
}
```

Example:

```python
checkpoint_store = {
    "sam-demo-thread": {
        "messages": [
            HumanMessage("My name is Sam"),
            AIMessage("Got it"),
            HumanMessage("What is my name?"),
            AIMessage("Your name is Sam")
        ]
    }
}
```

That is the simplest mental model.

---

# How v6 Works Internally

Suppose you call:

```python
graph.invoke(
    {"messages": [HumanMessage(content="Where do I live?")]},
    config={"configurable": {"thread_id": "sam-demo-thread"}}
)
```

LangGraph roughly does this.

---

## Step 1: Load checkpoint

```python
state = checkpoint_store["sam-demo-thread"]
```

State becomes:

```python
{
    "messages": [
        HumanMessage("My name is Sam"),
        AIMessage("Got it"),
        HumanMessage("What is my name?"),
        AIMessage("Your name is Sam")
    ]
}
```

---

## Step 2: Merge new input

Input state:

```python
{
    "messages": [
        HumanMessage("Where do I live?")
    ]
}
```

Since messages uses:

```python
Annotated[list[BaseMessage], add_messages]
```

LangGraph merges:

```python
merged_messages = add_messages(
    old_messages,
    new_messages
)
```

Result:

```python
[
    HumanMessage("My name is Sam"),
    AIMessage("Got it"),
    HumanMessage("What is my name?"),
    AIMessage("Your name is Sam"),
    HumanMessage("Where do I live?")
]
```

---

## Step 3: Run graph

Assistant node runs:

```python
assistant_node(state)
```

Returns:

```python
{
    "messages": [
        AIMessage("I don't know where you live.")
    ]
}
```

---

## Step 4: Merge assistant response

Again `add_messages` runs:

```python
[
    ...previous messages...,
    HumanMessage("Where do I live?"),
    AIMessage("I don't know where you live.")
]
```

---

## Step 5: Save checkpoint

LangGraph updates storage:

```python
checkpoint_store["sam-demo-thread"] = updated_state
```

Conversation is now persisted.

---

# Where add_messages Fits

This is important.

Persistence does **not replace** `add_messages`.

`add_messages` still handles message merging.

Without it, message history would be overwritten.

---

## Without add_messages

New messages replace old messages.

Bad for conversations.

---

## With add_messages

New messages are appended to old messages.

Good for conversations.

---

# So what changed from v5?

In both v5 and v6:

```python
messages: Annotated[list[BaseMessage], add_messages]
```

is still doing message append.

The difference is:

### v5

You manually provide old messages.

```text
manual history management
```

---

### v6

Checkpointer loads old messages.

```text
automatic history management
```

---

# More Accurate Internal Model

Real checkpoint storage is richer than:

```python
thread_id -> AgentState
```

It often stores:

```python
checkpoint_store = {
    thread_id: {
        "state": AgentState,
        "metadata": {...},
        "next_node": ...,
        "checkpoint_id": ...,
        "timestamp": ...
    }
}
```

Because LangGraph supports:

* interrupted workflows
* resumable execution
* human approval
* long-running agents
* partial graph execution

So it may store:

* current state
* execution position
* graph version
* checkpoint history

Not just messages.

---

# InMemorySaver

In this version:

```python
checkpointer = InMemorySaver()
```

Storage is:

```text
RAM only
```

If the notebook/kernel/process stops:

```text
all checkpoints are lost
```

---

# Production Checkpointers

Later, persistent storage becomes important.

Examples:

| Checkpointer   | Storage            |
| -------------- | ------------------ |
| InMemorySaver  | RAM                |
| SQLite Saver   | Local DB           |
| Postgres Saver | Database           |
| Redis Saver    | Cache              |
| Custom Saver   | S3 / Cloud Storage |

For production systems, persistent checkpointing is essential.

Especially for:

* long-running agents
* approval workflows
* human-in-the-loop
* multi-agent systems
* A2A workflows

---

# Why This Matters

Checkpointing enables:

* persistent chat sessions
* long-running workflows
* interrupted execution recovery
* human approval and resume
* multi-step automation
* shared state across agents

This is the foundation for advanced LangGraph workflows.

---

# Summary

`thread_id` selects the saved conversation.

`checkpointer` stores and reloads state.

`add_messages` still merges message history.

Simple mental model:

```text
thread_id → load checkpoint
checkpoint + new input → merged state
graph executes
updated state → save checkpoint
```

That is the core idea of `agentv6_persistence_checkpointer`.

