"""Background loop: runs the Detection Engine sweep on a fixed interval
and pushes new detections out over the WebSocket hub. This is a simple
in-process scheduler sufficient for a single backend instance; scale-out
deployments should move this to a dedicated worker consuming from
NATS/Kafka (see README - Distributed Analysis Layer)."""
from __future__ import annotations

import asyncio

from app.api.websocket import manager
from app.config import settings
from app.db.database import SessionLocal
from app.core.detection_engine import run_detection_sweep


async def detection_sweep_loop():
    while True:
        try:
            async with SessionLocal() as db:
                created = await run_detection_sweep(db)
                await db.commit()
                for d in created:
                    await manager.broadcast(
                        {
                            "type": "detection",
                            "id": str(d.id),
                            "entity_id": str(d.entity_id),
                            "category": d.category,
                            "severity": d.severity,
                            "confidence": d.confidence,
                            "detected_at": d.detected_at.isoformat(),
                        }
                    )
        except Exception as e:  # noqa: BLE001
            # A failure in the sweep itself is exactly the kind of
            # self-failure the Platform Silence Guard / Meta-Detection
            # layer should catch - never let it kill the loop.
            await manager.broadcast({"type": "platform_warning", "detail": str(e)})
        await asyncio.sleep(settings.silence_poll_interval_seconds)
