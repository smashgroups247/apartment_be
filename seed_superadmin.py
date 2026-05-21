"""
Seed Superadmin Script
File: seed_superadmin.py

Usage:
    python seed_superadmin.py [email] [password]

If no arguments are provided, defaults are used.
"""

import asyncio
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.db.database import AsyncSessionLocal
from api.v1.models.users import User
from api.utils.jwt_handler import hash_password


async def seed_superadmin(email: str, password: str):
    async with AsyncSessionLocal() as db:
        # Check if superadmin already exists
        result = await db.execute(select(User).filter(User.email == email))
        existing = result.scalars().first()

        if existing:
            if existing.role == "superadmin":
                print(f"✅ Superadmin already exists: {email}")
                return
            else:
                # Promote existing user to superadmin
                existing.role = "superadmin"
                existing.vendor_verified = True
                existing.id_verification_status = "approved"
                await db.commit()
                print(f"✅ Promoted existing user to superadmin: {email}")
                return

        # Create new superadmin
        user = User(
            first_name="Super",
            last_name="Admin",
            email=email,
            hashed_password=hash_password(password),
            role="superadmin",
            is_active=True,
            is_verified=True,
            vendor_verified=True,
            id_verification_status="approved",
        )
        db.add(user)
        await db.commit()
        print(f"✅ Superadmin created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Role: superadmin")


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@smashapartments.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "Admin@123!"

    print(f"🔧 Seeding superadmin: {email}")
    asyncio.run(seed_superadmin(email, password))
