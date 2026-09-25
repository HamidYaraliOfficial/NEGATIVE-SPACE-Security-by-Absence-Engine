"""Entity CRUD - hosts, services, processes, users, APIs, databases, etc."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db.database import get_db
from app.db.models import Entity
from app.schemas.schemas import EntityCreate, EntityOut

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])


@router.get("", response_model=list[EntityOut])
async def list_entities(
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    stmt = select(Entity).where(Entity.tenant_id == user.tenant_id)
    if entity_type:
        stmt = stmt.where(Entity.entity_type == entity_type)
    rows = (await db.execute(stmt.order_by(Entity.created_at.desc()).limit(500))).scalars().all()
    return [_serialize(e) for e in rows]


@router.post("", response_model=EntityOut)
async def create_entity(
    body: EntityCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    entity = Entity(
        tenant_id=user.tenant_id,
        entity_type=body.entity_type,
        name=body.name,
        criticality=body.criticality,
        attributes=body.attributes,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return _serialize(entity)


def _serialize(e: Entity) -> dict:
    return {
        "id": str(e.id),
        "entity_type": e.entity_type.value if hasattr(e.entity_type, "value") else e.entity_type,
        "name": e.name,
        "criticality": e.criticality,
        "attributes": e.attributes,
        "created_at": e.created_at,
    }
