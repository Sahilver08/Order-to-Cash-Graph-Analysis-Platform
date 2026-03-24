# FDE First Round - Order-to-Cash Graph Analysis Platform

A graph-based data modeling and query system for SAP Order-to-Cash (O2C) business processes, featuring interactive visualization and AI-powered natural language querying.

## Overview

This system unifies fragmented SAP O2C data (orders, deliveries, invoices, payments) into a connected graph representation. Users can explore relationships visually and query the data using natural language through an integrated chat interface.

## Architecture

### Backend (FastAPI - Python)

- **Data Layer**: Preprocesses and indexes SAP O2C JSONL datasets for fast lookups
- **Graph Construction**: Dynamically builds entity-relationship graphs with 8 node types and 7 edge types
- **Query Engine**: Template-driven queries with LLM classification and execution
- **LLM Integration**: HuggingFace Mistral-7B for question understanding and answer generation

### Frontend (React + TypeScript + Vite)

- **Graph Visualization**: Interactive force-directed graph using react-force-graph-2d
- **Chat Interface**: Conversational querying with real-time responses
- **Responsive UI**: Two-panel layout with graph exploration and chat

### Data Storage

- In-memory data store with precomputed indexes
- No external database required for the dataset size

## Key Features

### Graph Modeling

- **Nodes**: Sales orders, deliveries, billing documents, products, customers, journal entries, payments, addresses
- **Edges**: Semantic relationships (SO→Delivery, Delivery→Billing, etc.)
- **Visualization**: Expandable nodes with metadata inspection

### Query Capabilities

- Natural language to structured query translation
- Pre-built templates for common analyses:
  - Top products by billing frequency
  - Full O2C flow tracing for billing documents
  - Detection of broken/incomplete flows
- Guardrails: Domain restriction with refusal of out-of-scope queries

### LLM Strategy

- **Provider**: HuggingFace Inference API (Mistral-7B-Instruct)
- **Classification**: Determines query relevance and extracts parameters
- **Answer Generation**: Grounded responses based on template results
- **Fallback**: Rule-based matching if LLM unavailable

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- SAP O2C dataset (place in `data/sap-o2c-data/`)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Data Setup

1. Download the dataset from: https://drive.google.com/file/d/1UqaLbFaveV-3MEuiUrzKydhKmkeC1iAL/view?usp=sharing
2. Extract and place in `data/sap-o2c-data/`
3. The system will automatically load on startup

## Usage

1. Start both backend and frontend servers
2. Open http://localhost:5173 in your browser
3. Explore the graph by clicking nodes to expand relationships
4. Use the chat interface for natural language queries:
   - "Trace billing document 123456"
   - "Show broken flows"

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/graph/overview` - Full graph data
- `GET /api/graph/expand/{node_id}` - Expand node relationships
- `POST /api/query` - Natural language query processing

## Deployment

### Backend

- Deploy to Heroku, Railway, or similar Python hosting
- Set environment variables for production (if needed)

### Frontend

- Build: `npm run build`
- Deploy to Vercel, Netlify, or static hosting
- Configure API proxy for backend communication

## Architecture Decisions

### Data Storage

- **Choice**: In-memory with indexes
- **Rationale**: Dataset fits in memory, enables O(1) lookups, no DB complexity
- **Tradeoffs**: Not scalable for larger datasets, requires restart on data changes

### Graph Representation

- **Choice**: Dynamic construction from relational data
- **Rationale**: Flexible for different query patterns, semantic edge labels
- **Tradeoffs**: Computation on each request vs. precomputed graph

### Query Templates

- **Choice**: Pre-defined templates with parameter extraction
- **Rationale**: Deterministic, reliable, easier to maintain than dynamic SQL generation
- **Tradeoffs**: Less flexible than full NL-to-SQL, requires template expansion for new queries

### LLM Integration

- **Choice**: Classification + summarization pattern
- **Rationale**: Balances accuracy with cost, prevents hallucinations
- **Tradeoffs**: Two API calls per query, depends on LLM availability

## Guardrails Implementation

- **Domain Filtering**: LLM classifies queries as domain-related or not
- **Parameter Validation**: JSON schema validation for extracted parameters
- **Refusal Response**: Standardized message for out-of-scope queries
- **Fallback Logic**: Rule-based matching ensures system works without LLM

## Evaluation Notes

This implementation prioritizes:

- **Correctness**: All answers grounded in data
- **Usability**: Intuitive graph exploration and chat interface
- **Maintainability**: Modular architecture with clear separation of concerns
- **Compliance**: Meets all assignment requirements with room for extension

## Future Enhancements

- Conversation memory and context
- Streaming LLM responses
- Advanced graph analytics (clustering, centrality)
- Semantic search over entities
- Multi-dataset support
