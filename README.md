# FDE First Round - Order-to-Cash Graph Analysis Platform

A graph-based data modeling and query system for SAP Order-to-Cash (O2C) business processes, featuring interactive visualization and AI-powered natural language querying.

---

## Overview

Enterprise O2C data is typically fragmented across multiple systems and tables (orders, deliveries, invoices, payments), making it difficult to trace relationships and identify inconsistencies.

This system unifies that fragmented data into a **connected graph representation**, enabling:

* End-to-end visibility across the O2C lifecycle
* Efficient traversal of relationships (order → delivery → billing → payment)
* Detection of incomplete or broken business flows

Users can explore these relationships visually and query the system using natural language through an integrated chat interface.

---

## Architecture

### Backend (FastAPI - Python)

* **Data Layer**: Preprocesses and indexes SAP O2C JSONL datasets for efficient in-memory access and fast lookups
* **Graph Construction**: Dynamically builds a directed entity-relationship graph with clearly defined node and edge types
* **Query Engine**: Template-driven execution system ensuring deterministic and reliable query results
* **LLM Integration**: HuggingFace Mistral-7B used for intent classification, parameter extraction, and response generation

---

### Frontend (React + TypeScript + Vite)

* **Graph Visualization**: Interactive force-directed graph using `react-force-graph-2d`
* **Chat Interface**: Natural language querying with real-time responses
* **UI Design**: Clean two-panel layout for simultaneous graph exploration and querying

---

### Data Storage

* In-memory data store with precomputed indexes
* Optimized for O(1) lookups and fast traversal
* No external database required given dataset size

---

## Key Features

### Graph Modeling

The O2C process is modeled as a **directed graph**, where:

* **Nodes** represent business entities:

  * Sales Orders, Deliveries, Billing Documents, Payments, Products, Customers, Journal Entries, Addresses

* **Edges** represent lifecycle relationships:

  * Sales Order → Delivery → Billing → Payment

This graph-based approach enables:

* Efficient traversal for flow tracing
* Identification of broken or incomplete business processes
* Context-aware querying across multiple entity layers

---

### Query Capabilities

* Natural language → structured query translation
* Template-driven execution to ensure correctness and avoid ambiguity
* Supported query types include:

  * Top products by billing frequency
  * Full O2C flow tracing for billing documents
  * Detection of broken or incomplete flows

This approach avoids unreliable raw NL-to-SQL generation and ensures all outputs are deterministic and data-backed.

---

### Query Processing Flow

1. User submits a natural language query
2. LLM classifies intent and extracts relevant parameters
3. Query engine selects the appropriate template
4. Backend executes logic on indexed in-memory dataset
5. Results are passed through a formatting layer
6. Final response is returned as a clean, human-readable answer

This pipeline ensures:

* Zero hallucination
* Full grounding in dataset
* Consistent and reliable outputs

---

### LLM Strategy

* **Provider**: HuggingFace Inference API (Mistral-7B-Instruct)
* **Classification Layer**: Determines query relevance and extracts structured parameters
* **Execution Separation**: LLM does not execute queries — backend handles all data operations
* **Response Generation**: LLM refines responses for clarity and readability
* **Fallback Mechanism**: Rule-based query handling ensures system reliability if LLM is unavailable

---

## Setup and Installation

### Prerequisites

* Python 3.8+
* Node.js 16+
* SAP O2C dataset (place in `data/sap-o2c-data/`)

---

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

### Data Setup

1. Download dataset:
   https://drive.google.com/file/d/1UqaLbFaveV-3MEuiUrzKydhKmkeC1iAL/view

2. Extract and place in:
   `data/sap-o2c-data/`

3. Data loads automatically at startup

---

## Usage

1. Start backend and frontend
2. Open `http://localhost:5173`
3. Explore graph by expanding nodes and inspecting relationships
4. Use chat interface for queries such as:

   * "Trace billing document 123456"
   * "Show broken flows"

---

## API Endpoints

* `GET /api/health` → Health check
* `GET /api/graph/overview` → Retrieve full graph
* `GET /api/graph/expand/{node_id}` → Expand node relationships
* `POST /api/query` → Process natural language queries

---

## Deployment

### Backend

* Deploy on platforms such as Railway / Render / Heroku
* Configure environment variables if needed

---

### Frontend

* Build:

```bash
npm run build
```

* Deploy to Netlify / Vercel / static hosting
* Configure API proxy for backend communication

---

## Architecture Decisions

### Data Storage

* **Choice**: In-memory with indexing
* **Rationale**: Dataset fits in memory, enables fast lookups and low latency
* **Tradeoff**: Limited scalability for larger datasets

---

### Graph Representation

* **Choice**: Dynamic graph construction from relational data
* **Rationale**: Enables flexible traversal and relationship-based querying
* **Tradeoff**: Additional computation vs precomputed graph storage

---

### Query Templates

* **Choice**: Template-driven execution instead of raw NL-to-SQL
* **Rationale**: Ensures deterministic, safe, and correct query execution
* **Tradeoff**: Requires predefined templates for supported queries

---

### LLM Integration

* **Choice**: Classification + response refinement
* **Rationale**: Separates reasoning from execution, preventing hallucination
* **Tradeoff**: Additional latency due to multi-step processing

---

## Guardrails Implementation

Guardrails are enforced at multiple levels:

1. **Query Classification** → Rejects non-domain queries
2. **Template Restriction** → Only predefined query types allowed
3. **Data Grounding** → All responses derived from actual dataset
4. **Fallback Handling** → Standard refusal message for unsupported queries

This ensures strict domain adherence and prevents misuse.

---

## Response Formatting

A dedicated formatting layer converts raw query results into structured, human-readable responses.

This improves:

* Clarity for end users
* Consistency across responses
* Separation of logic and presentation

---

## Evaluation Notes

This implementation prioritizes:

* **Correctness** → All answers are data-backed
* **System Design** → Clear separation of concerns across layers
* **Usability** → Intuitive graph + conversational interface
* **Reliability** → Guardrails and deterministic query execution

---

## Future Enhancements

* Conversation memory and context awareness
* Streaming LLM responses
* Advanced graph analytics (clustering, centrality)
* Semantic search across entities
* Support for larger datasets with persistent storage
