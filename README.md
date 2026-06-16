# OncoGuide Agentic AI

An open-source multi-agent AI system for:

- Cancer symptom screening
- Medical report explanation
- Evidence-based medical Q&A
- Clinical trial discovery
- Human-in-the-loop validation

---

# Architecture

![OncoGuide Architecture](docs/architecture.png)

---

# Key Features

## Multi-Agent Architecture

- Supervisor Agent
- Screening Agent
- Agentic RAG Agent
- Clinical Trial Agent
- Report Explanation Agent
- Manual Tool Agent
- ReAct Agent
- General Chat Agent

## Safety Layers

- Unified Input Guardrail
- Reflection Agent
- Claim Verification Agent
- Human-in-the-Loop Review
- Output Guardrail

## Hybrid RAG

- Query Rewrite
- Query Classification
- Vector Retrieval
- BM25 Retrieval
- RRF Fusion
- Cross-Encoder Re-ranking
- Context Assembly

## MCP Integration

- PubMed MCP
- ClinicalTrials MCP
- Vector DB MCP
- File System MCP

## Observability

- LangSmith Tracing
- Agent Routing Monitoring
- Tool Usage Tracking
- Latency Monitoring

---

# Technology Stack

| Component | Technology |
|------------|------------|
| LLM | Groq |
| Orchestration | LangGraph |
| RAG | LlamaIndex |
| Vector DB | ChromaDB / Qdrant |
| Monitoring | LangSmith |
| Evaluation | RAGAS, DeepEval |

---

# Current Pipeline

User Question

→ Input Guardrail

→ Supervisor

→ Specialized Agent

→ Reflection Agent

→ Claim Verification Agent

→ Human Review (if needed)

→ Output Guardrail

→ Final Answer

---

# Documentation

Detailed technical guide available in:

docs/OncoGuide_Agentic_AI_Updated.docx

---

# Research Direction

This project is being developed toward a publication-quality medical agentic AI system featuring:

- Hybrid Biomedical RAG
- MCP Tool Integration
- Claim Verification
- Human-in-the-Loop Validation
- LangSmith Observability