# Database Agent with A2A Protocol

This project implements a database management agent powered by LangGraph and the A2A protocol.  
The agent provides capabilities for querying database schema, retrieving table samples, and executing custom SQL queries based on natural language input.

---

## Features
- **Natural Language to SQL**: Convert user queries into SQL statements.
- **Database Schema Exploration**: View tables, columns, indexes, and relationships.
- **Streaming Responses**: Supports streaming large results via SSE.
- **A2A Protocol**: Fully compatible with agent-to-agent communication standards.
- **Lightweight Server**: Built with FastAPI and LangGraph.

---

## Requirements
- Python 3.12+
- `uv` (Ultra-fast Python Package Manager) installed

Install `uv` if you don't have it:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
