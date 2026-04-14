"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memoryforge.config import Config, get_config
from memoryforge.db.connection import get_connection
from memoryforge.db.repository import Repository

from .routes_subjects import router as subjects_router
from .routes_materials import router as materials_router
from .routes_sessions import router as sessions_router
from .routes_dashboard import router as dashboard_router
from .routes_plans import router as plans_router
from .routes_history import router as history_router


def create_app(config: Config | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = get_config()

    config.ensure_dirs()

    app = FastAPI(title="MemoryForge API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    conn = get_connection(config.db_path)
    app.state.repo = Repository(conn)
    app.state.config = config

    app.include_router(subjects_router)
    app.include_router(materials_router)
    app.include_router(sessions_router)
    app.include_router(dashboard_router)
    app.include_router(plans_router)
    app.include_router(history_router)

    return app
