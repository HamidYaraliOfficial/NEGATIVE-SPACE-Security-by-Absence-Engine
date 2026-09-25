"""One-off CLI to create the first admin user.

Usage:
    python -m scripts.create_admin admin@example.com "a-strong-password"
"""
from __future__ import annotations

import asyncio
import sys

sys.path.append(".")

from app.core.auth import hash_password
from app.db.database import SessionLocal, engine, Base
from app.db.models import Role, User


async def main(email: str, password: str, tenant_id: str = "default") -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=Role.admin,
            tenant_id=tenant_id,
        )
        db.add(user)
        await db.commit()
    print(f"Created admin user: {email}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.create_admin <email> <password> [tenant_id]")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "default"))
