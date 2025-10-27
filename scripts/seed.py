"""Database seeding script for initial data - UPDATED FOR AUTH SERVICE COMPATIBILITY."""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import date, timedelta

from app.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.hostel import Plan, PlanTier, Hostel, Subscription, SubscriptionStatus
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_plans(session: AsyncSession):
    """Seed subscription plans."""
    plans_data = [
        {
            "name": "Free Plan",
            "tier": PlanTier.FREE,
            "description": "Basic plan for small hostels",
            "max_hostels": 1,
            "max_tenants_per_hostel": 10,
            "max_rooms_per_hostel": 5,
            "max_admins_per_hostel": 1,
            "max_storage_mb": 100,
            "features": {
                "basic_billing": True,
                "reports": False,
                "api_access": False,
                "custom_branding": False,
            },
            "is_active": True,
        },
        {
            "name": "Standard Plan",
            "tier": PlanTier.STANDARD,
            "description": "Professional plan for medium hostels",
            "max_hostels": 3,
            "max_tenants_per_hostel": 50,
            "max_rooms_per_hostel": 20,
            "max_admins_per_hostel": 3,
            "max_storage_mb": 1000,
            "features": {
                "basic_billing": True,
                "reports": True,
                "api_access": True,
                "custom_branding": False,
                "bulk_operations": True,
            },
            "is_active": True,
        },
        {
            "name": "Premium Plan",
            "tier": PlanTier.PREMIUM,
            "description": "Enterprise plan for large hostels",
            "max_hostels": None,
            "max_tenants_per_hostel": None,
            "max_rooms_per_hostel": None,
            "max_admins_per_hostel": None,
            "max_storage_mb": 10000,
            "features": {
                "basic_billing": True,
                "reports": True,
                "api_access": True,
                "custom_branding": True,
                "bulk_operations": True,
                "priority_support": True,
                "advanced_analytics": True,
            },
            "is_active": True,
        },
    ]

    for plan_data in plans_data:
        plan = Plan(**plan_data)
        session.add(plan)
    
    await session.commit()
    print("✓ Seeded subscription plans")


async def seed_superadmin(session: AsyncSession):
    """Seed super admin user."""
    superadmin = User(
        email="superadmin@hostelms.com",
        phone="+919999999999",
        password_hash=hash_password("SuperAdmin@123"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(superadmin)
    await session.commit()
    print("✓ Seeded super admin")
    print("  Email: superadmin@hostelms.com")
    print("  Password: SuperAdmin@123")
    return superadmin


async def seed_demo_hostel_with_admin(session: AsyncSession):
    """Seed demo hostel with admin."""
    from sqlalchemy import select
    
    # Get the FREE plan
    result = await session.execute(select(Plan).where(Plan.tier == PlanTier.FREE))
    free_plan = result.scalar_one()

    # Create demo hostel
    demo_hostel = Hostel(
        name="Demo Hostel",
        code="DEMO001",
        address="123 Demo Street",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        phone="+919876543210",
        email="demo@hostel.com",
        timezone="Asia/Kolkata",
        is_active=True,
    )
    session.add(demo_hostel)
    await session.flush()

    # Create subscription for demo hostel
    subscription = Subscription(
        hostel_id=demo_hostel.id,
        plan_id=free_plan.id,
        status=SubscriptionStatus.TRIAL,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        auto_renew=False,
    )
    session.add(subscription)

    # Create hostel admin
    admin = User(
        email="admin@demo.com",
        phone="+919876543211",
        password_hash=hash_password("Admin@123"),
        role=UserRole.HOSTEL_ADMIN,
        primary_hostel_id=demo_hostel.id,
        is_active=True,
        is_verified=True,
    )
    session.add(admin)
    await session.flush()

    # Associate admin with hostel (manual insert to avoid lazy loading in async)
    from sqlalchemy import insert
    from app.models.associations import user_hostel_association
    
    await session.execute(
        insert(user_hostel_association).values(
            user_id=admin.id,
            hostel_id=demo_hostel.id
        )
    )

    await session.commit()
    print("✓ Seeded demo hostel with admin")
    print("  Hostel: Demo Hostel (DEMO001)")
    print("  Admin Email: admin@demo.com")
    print("  Admin Password: Admin@123")
    return demo_hostel, admin


async def seed_demo_tenant_with_profile(session: AsyncSession, hostel: Hostel):
    """
    Seed demo tenant with complete profile.
    
    ✅ UPDATED: Automatically creates TenantProfile when creating TENANT user,
    matching the behavior in AuthService.register_user()
    """
    from app.models.tenant import TenantProfile
    from datetime import date
    
    # Create tenant user
    tenant_user = User(
        email="tenant@demo.com",
        phone="+919876543212",
        password_hash=hash_password("Tenant@123"),
        role=UserRole.TENANT,
        primary_hostel_id=hostel.id,
        is_active=True,
        is_verified=True,
    )
    session.add(tenant_user)
    await session.flush()  # Get the ID
    
    # ✅ AUTO-CREATE TENANT PROFILE (matching AuthService behavior)
    # When role is TENANT, automatically create a basic tenant profile
    # This ensures consistency with the auth service registration
    
    # Derive full_name from email (same logic as AuthService)
    full_name = tenant_user.email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
    
    tenant_profile = TenantProfile(
        user_id=tenant_user.id,
        hostel_id=hostel.id,
        full_name=full_name or "Demo Tenant",
        date_of_birth=date(2000, 1, 1),
        gender="Male",
        guardian_name="Demo Guardian",
        guardian_phone="+919876543213",
        emergency_contact="+919876543213"
    )
    session.add(tenant_profile)
    
    await session.commit()
    
    print("✓ Seeded demo tenant with auto-created profile")
    print("  Email: tenant@demo.com")
    print("  Password: Tenant@123")
    print(f"  Profile ID: {tenant_profile.id}")
    print("  Full Name: " + full_name)
    print("  ℹ️  TenantProfile auto-created (matching AuthService behavior)")
    
    return tenant_user, tenant_profile


async def seed_all():
    """Seed all initial data."""
    print("\n🌱 Starting database seeding...\n")

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables verified\n")

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            
            # Check if plans already exist
            result = await session.execute(select(Plan))
            existing_plans = result.scalars().all()
            
            if not existing_plans:
                # Seed plans only if they don't exist
                await seed_plans(session)
            else:
                print("⚠️  Plans already exist. Skipping plan seeding.")
            
            # Check if superadmin already exists
            result = await session.execute(select(User).where(User.role == UserRole.SUPER_ADMIN))
            if result.scalar_one_or_none():
                print("⚠️  Super admin already exists. Skipping user seeding.\n")
                return

            # Seed superadmin
            await seed_superadmin(session)

            # Seed demo hostel with admin
            demo_hostel, admin = await seed_demo_hostel_with_admin(session)

            # Seed demo tenant (with auto-created profile)
            await seed_demo_tenant_with_profile(session, demo_hostel)

            print("\n✅ Database seeding completed successfully!\n")
            print("=" * 60)
            print("DEFAULT CREDENTIALS")
            print("=" * 60)
            print("\n1. SUPER ADMIN")
            print("   Email: superadmin@hostelms.com")
            print("   Password: SuperAdmin@123")
            print("\n2. HOSTEL ADMIN (Demo Hostel)")
            print("   Email: admin@demo.com")
            print("   Password: Admin@123")
            print("   Hostel Code: DEMO001")
            print("\n3. TENANT (Demo Hostel)")
            print("   Email: tenant@demo.com")
            print("   Password: Tenant@123")
            print("   Note: TenantProfile auto-created ✓")
            print("\n" + "=" * 60)
            print("\n⚠️  IMPORTANT: Change these passwords in production!")
            print("\nℹ️  TENANT REGISTRATION:")
            print("   - Admin-created tenants get auto-generated profiles")
            print("   - Self-registered tenants also get auto-generated profiles")
            print("   - This matches the AuthService.register_user() behavior\n")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise
        
        
if __name__ == "__main__":
    asyncio.run(seed_all())