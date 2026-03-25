from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.api.routes_graph import router as graph_router
from backend.api.routes_query import router as query_router
from backend.graph.preprocess import O2CDataStore
from backend.llm.hf_client import HuggingFaceClient

DATASET_BASE_PATH = Path(__file__).parent.parent / "data" / "sap-o2c-data"


def create_app() -> FastAPI:
    app = FastAPI(
        title="FDE First Round API",
        description="Backend API for graph visualization and template-driven querying.",
        version="0.1.0",
    )

    # Keep CORS open for initial local frontend integration.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    store = O2CDataStore(base_path=DATASET_BASE_PATH)
    store.load()
    app.state.data_store = store
    app.state.hf_client = HuggingFaceClient(api_token="")

    app.include_router(graph_router)
    app.include_router(query_router)

    return app


app = create_app()
