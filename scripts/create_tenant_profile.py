"""Create tenant profile for demo tenant user."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.tenant import TenantProfile
from datetime import date


async def create_tenant_profile():
    """Create tenant profile for demo tenant."""
    async with AsyncSessionLocal() as db:
        # Get tenant user
        result = await db.execute(
            select(User).where(User.email == "tenant@demo.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Tenant user not found!")
            print("Run: python scripts/seed.py first")
            return False
        
        print(f"✅ Found tenant user:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Hostel ID: {user.primary_hostel_id}")
        
        # Check if profile already exists
        result = await db.execute(
            select(TenantProfile).where(TenantProfile.user_id == user.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"\n⚠️  Tenant profile already exists:")
            print(f"   Profile ID: {existing.id}")
            print(f"   Is Deleted: {existing.is_deleted}")
            
            if existing.is_deleted:
                print("\n🔧 Profile is soft-deleted. Restoring...")
                existing.is_deleted = False
                existing.deleted_at = None
                await db.commit()
                print("✅ Profile restored!")
            else:
                print("\n✅ Profile is active. No action needed.")
            
            return True
        
        # Create tenant profile
        print("\n🔧 Creating tenant profile...")
        
        profile = TenantProfile(
            user_id=user.id,
            hostel_id=user.primary_hostel_id,
            full_name="Demo Tenant",
            date_of_birth=date(2000, 1, 1),
            gender="Male",
            guardian_name="Demo Guardian",
            guardian_phone="+919876543213",
            emergency_contact="+919876543213",
            is_deleted=False
        )
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        print(f"\n✅ Tenant profile created successfully!")
        print(f"   Profile ID: {profile.id}")
        print(f"   User ID: {profile.user_id}")
        print(f"   Hostel ID: {profile.hostel_id}")
        print(f"   Full Name: {profile.full_name}")
        print(f"\n🎉 You can now create complaints as tenant@demo.com!")
        
        return True


if __name__ == "__main__":
    print("\n🚀 Creating Tenant Profile...\n")
    success = asyncio.run(create_tenant_profile())
    sys.exit(0 if success else 1)