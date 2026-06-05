"""GrapeHub — FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import (
    auth, collections, grapes, producers, reports, stock, tastings, users, wines, wishlist,
)
from app.core.config import settings
from app.db.session import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

# Path to the sibling frontend/ directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
UPLOAD_DIR = Path(settings.UPLOAD_DIR).resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "wines").mkdir(parents=True, exist_ok=True)
    logger.info("GrapeHub started — frontend: %s", FRONTEND_DIR)
    yield
    logger.info("GrapeHub stopped")


app = FastAPI(
    title="GrapeHub 🍷",
    description="Gestão premium de garrafeira pessoal — FastAPI + SQLite + Vue 3",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(producers.router)
app.include_router(grapes.router)
app.include_router(wines.router)
app.include_router(stock.router)
app.include_router(tastings.router)
app.include_router(wishlist.router)
app.include_router(collections.router)
app.include_router(reports.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": "GrapeHub", "version": "1.0.0"}


@app.get("/api/health", tags=["meta"])
def health_api():
    return {"status": "ok", "app": "GrapeHub", "version": "1.0.0"}


# ── Uploaded files (wine photos) ──────────────────────────────────────────────
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ── Frontend SPA serving ──────────────────────────────────────────────────────
if FRONTEND_DIR.exists():
    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(str(FRONTEND_DIR / "index.html"), headers={"Cache-Control": "no-cache"})

    for sub in ["src", "icons"]:
        sub_path = FRONTEND_DIR / sub
        if sub_path.exists():
            app.mount(f"/{sub}", StaticFiles(directory=str(sub_path)), name=f"static_{sub}")

    @app.get("/manifest.json", include_in_schema=False)
    async def manifest():
        return FileResponse(str(FRONTEND_DIR / "manifest.json"), media_type="application/json")

    @app.get("/service-worker.js", include_in_schema=False)
    async def sw():
        return FileResponse(str(FRONTEND_DIR / "service-worker.js"),
                            media_type="application/javascript",
                            headers={"Cache-Control": "no-cache"})

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, full_path: str):
        # Serve static files from frontend, otherwise fallback to index.html for SPA routing
        # API routes (auth/, wines/, etc.) will be matched by their routers before this catch-all
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            ext_map = {".js": "application/javascript", ".css": "text/css",
                       ".json": "application/json", ".html": "text/html",
                       ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon"}
            ct = ext_map.get(file_path.suffix.lower(), "application/octet-stream")
            return FileResponse(str(file_path), media_type=ct, headers={"Cache-Control": "no-cache"})
        # Return index.html for SPA routing
        return FileResponse(str(FRONTEND_DIR / "index.html"), headers={"Cache-Control": "no-cache"})
