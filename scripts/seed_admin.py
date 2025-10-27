"""Seed initial super admin user."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_super_admin():
    """Create initial super admin user."""
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if super admin exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.role == UserRole.SUPER_ADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Super Admin already exists: {existing.email or existing.phone}")
            return
        
        # Create super admin
        email = input("Enter super admin email: ").strip()
        password = input("Enter super admin password (min 8 chars): ").strip()
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            return
        
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"\n✅ Super Admin created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"\n🔐 You can now login at /api/v1/auth/login with:")
        print(f"   Email: {email}")
        print(f"   Password: [your password]")


if __name__ == "__main__":
    print("🚀 Creating Super Admin User...\n")
    asyncio.run(create_super_admin())