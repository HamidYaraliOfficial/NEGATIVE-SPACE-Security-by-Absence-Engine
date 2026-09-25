"""Negative Space Query Playground endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.query_engine import NegativeSpaceQuery, run_query
from app.db.database import get_db
from app.schemas.schemas import QueryRequest

router = APIRouter(prefix="/api/v1/query", tags=["query"])


@router.post("")
async def query(
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    q = NegativeSpaceQuery(**body.model_dump())
    return await run_query(db, q, tenant_id=user.tenant_id)
