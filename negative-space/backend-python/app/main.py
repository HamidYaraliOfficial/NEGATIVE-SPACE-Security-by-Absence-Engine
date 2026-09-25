"""NEGATIVE SPACE backend entrypoint - FastAPI app wiring."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_agents,
    routes_auth,
    routes_business_hours,
    routes_cases,
    routes_detections,
    routes_entities,
    routes_ingest,
    routes_query,
    routes_relationships,
    routes_reports,
    websocket,
)
from app.workers.background_tasks import detection_sweep_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(detection_sweep_loop())
    yield
    task.cancel()


app = FastAPI(
    title="NEGATIVE SPACE — Security by Absence Engine",
    description="Detects what should have happened but didn't.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_entities.router)
app.include_router(routes_ingest.router)
app.include_router(routes_detections.router)
app.include_router(routes_cases.router)
app.include_router(routes_business_hours.router)
app.include_router(routes_relationships.router)
app.include_router(routes_agents.router)
app.include_router(routes_query.router)
app.include_router(routes_reports.router)
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "negative-space-backend"}
