"""Relationship graph API - upsert observed/expected edges and fetch the
Reality Graph diff (missing / unexpected relationships)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.relationship_graph import RealityGraph
from app.db.database import get_db
from app.db.models import Entity, Relationship
from app.schemas.schemas import RelationshipUpsert

router = APIRouter(prefix="/api/v1/relationships", tags=["relationships"])


@router.post("")
async def upsert_relationship(
    body: RelationshipUpsert,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    rel = Relationship(
        tenant_id=user.tenant_id,
        source_entity_id=body.source_entity_id,
        target_entity_id=body.target_entity_id,
        relationship_type=body.relationship_type,
        expected=body.expected,
        observed=body.observed,
        frequency_per_day=body.frequency_per_day,
        confidence=body.confidence,
    )
    db.add(rel)
    await db.commit()
    return {"id": str(rel.id)}


@router.get("/graph")
async def get_graph(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    entities = (
        await db.execute(select(Entity).where(Entity.tenant_id == user.tenant_id))
    ).scalars().all()
    relationships = (
        await db.execute(select(Relationship).where(Relationship.tenant_id == user.tenant_id))
    ).scalars().all()

    rg = RealityGraph()
    for e in entities:
        rg.add_entity(str(e.id), name=e.name, entity_type=str(e.entity_type), criticality=e.criticality)
    for r in relationships:
        rg.upsert_relationship(
            str(r.source_entity_id),
            str(r.target_entity_id),
            r.relationship_type,
            r.expected,
            r.observed,
            r.frequency_per_day,
            r.confidence,
        )

    graph_json = rg.to_json()
    diff = rg.diff()
    return {
        "graph": graph_json,
        "diff": {
            "missing_edges": diff.missing_edges,
            "unexpected_edges": diff.unexpected_edges,
        },
    }
