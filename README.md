# Agentic AI Learn — LangGraph / MCP / A2A Learning Project

A hands-on project to learn and build production-grade AI agents using:

- LangGraph
- LangSmith
- MCP (Model Context Protocol)
- A2A (Agent-to-Agent communication)
- RAG / Vector DB
- Shared Context Memory
- FastAPI Production Deployment
- Evaluation Pipelines
- Agent Registry / Security

This repository is designed as a step-by-step progression from basic LangGraph concepts to enterprise-grade multi-agent systems.

---

# Purpose

The purpose of this project is to learn how modern AI agent systems are built in production.

This project covers:

- Basic graph workflows
- LLM integration
- Tool calling
- Routing
- Memory
- Human-in-the-loop
- Parallel execution
- Async execution
- MCP integrations
- A2A communication
- Production deployment
- Evaluation
- Registry / security architecture

Final goal:

Build and understand a complete production-grade multi-agent ecosystem.

---

# Use Cases

This project is applicable for building AI agents in domains such as:

- Enterprise automation
- Customer support
- DevOps / SRE
- Cloud operations
- BI / analytics
- Healthcare workflows
- Finance assistants
- Autonomous orchestration systems
- Multi-company AI ecosystems

Example:

- Parking agent
- SQL analytics agent
- RAG knowledge assistant
- Incident management agent
- Multi-agent orchestration platform

---

# Learning Modules

| Name | Functionality / Purpose | Example Real Time Use Case Scenarios |
|------|--------------------------|-------------------------------------|
| agentv1_basic_graph | Basic LangGraph graph | Hello-world workflow |
| agentv2_llm_node | Single LLM node | Simple chatbot |
| agentv3_tool_calling | Tool invocation | Calculator / API call |
| agentv4_router | Conditional routing | Route support tickets |
| agentv5_messages_state | Conversation memory | Chat assistant |
| agentv6_checkpointing | State persistence | Resume interrupted workflows |
| agentv7_multi_agent | Multiple cooperating agents | Planner + executor |
| agentv8_iterative_sql_tool_agent | Tool loops / retries | SQL generation + correction |
| agentv9_dynamic_parallel_workflow | Dynamic parallel execution | Query multiple services |
| agentv10_supervisor_agent | Supervisor orchestration | Coordinator agent |
| agentv11_human_in_loop | Human approval workflow | Financial approval |
| agentv12_rag | RAG workflow | PDF Q&A |
| agentv13_vector_store | Vector DB integration | Knowledge search |
| agentv14_subgraphs | Reusable graph components | Shared workflows |
| agentv15_memory_patterns | Memory strategies | Long-running assistants |
| agentv16_async_graph | Async execution | Parallel external API calls |
| agentv17_mcp | MCP integration | External tool server access |
| agentv18_simple_a2a | Basic agent communication | SQL agent + RAG agent |
| agentv19_a2a_protocol | Protocol-based A2A | Agent discovery + communication |
| agentv20_streaming_a2a | Streaming responses | Real-time agent output |
| agentv21_google_a2a_sdk | Official A2A SDK | Production A2A workflows |
| agentv22_multimodal_agent | Image / multimodal workflows | Vision agents |
| agentv23_shared_context_store | Persistent shared memory | Incident context reuse |
| agentv24_production_deployment_pattern | FastAPI deployment | Production API service |
| agentv25_langsmith_evaluation | Agent testing / evaluation | Regression testing |
| agentv26_agent_registry_auth_security | Registry + auth + security | Enterprise multi-agent ecosystems |

---

# Key Technologies

- Python
- LangGraph
- LangChain
- LangSmith
- FastAPI
- OpenAI / Gemini
- Chroma / FAISS / Vector DB
- SQLite / PostgreSQL
- MCP
- A2A Protocol
- Docker
- Kubernetes / Cloud Deployment

---

# Final Architecture

```text
User
 ↓
Host Agent (LangGraph)
 ↓
Planner / Supervisor
 ↓
Specialized Agents
 ├── SQL Agent
 ├── RAG Agent
 ├── MCP Agent
 ├── External A2A Agents
 ↓
Shared Context Store
 ↓
Vector DB / Knowledge Store
 ↓
Evaluation + Monitoring




