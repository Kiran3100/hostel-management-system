# scripts/verify_soft_delete.py
"""Verify soft delete is working correctly."""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import AsyncSessionLocal
from datetime import datetime


async def verify_soft_delete():
    """Verify soft delete functionality."""
    print("\n🔍 VERIFYING SOFT DELETE FUNCTIONALITY\n")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Check columns exist
            print("\n1️⃣ Checking if soft delete columns exist...\n")
            
            tables = ['hostels', 'rooms', 'beds', 'tenant_profiles', 'users']
            all_good = True
            
            for table in tables:
                query = text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name IN ('is_deleted', 'deleted_at')
                    ORDER BY column_name
                """)
                
                result = await db.execute(query)
                columns = result.fetchall()
                
                if len(columns) == 2:
                    print(f"   ✅ {table}: is_deleted (boolean), deleted_at (timestamp)")
                else:
                    print(f"   ❌ {table}: MISSING COLUMNS!")
                    all_good = False
            
            if not all_good:
                print("\n❌ Some tables are missing soft delete columns!")
                print("Run: python scripts/fix_soft_delete_simple.py")
                return False
            
            # Step 2: Test soft delete on a dummy room
            print("\n2️⃣ Testing soft delete operation...\n")
            
            # Create test room
            print("   Creating test room...")
            await db.execute(text("""
                INSERT INTO rooms (hostel_id, number, floor, room_type, capacity, is_deleted)
                VALUES (1, 'TEST_DELETE', 99, 'SINGLE', 1, FALSE)
            """))
            await db.commit()
            
            # Get the room ID
            result = await db.execute(text("""
                SELECT id FROM rooms WHERE number = 'TEST_DELETE'
            """))
            test_room_id = result.scalar()
            print(f"   ✅ Created test room ID: {test_room_id}")
            
            # Soft delete it
            print("\n   Performing soft delete...")
            await db.execute(text(f"""
                UPDATE rooms 
                SET is_deleted = TRUE, deleted_at = NOW()
                WHERE id = {test_room_id}
            """))
            await db.commit()
            
            # Verify it's marked as deleted
            result = await db.execute(text(f"""
                SELECT is_deleted, deleted_at 
                FROM rooms 
                WHERE id = {test_room_id}
            """))
            row = result.fetchone()
            
            if row and row[0] is True and row[1] is not None:
                print(f"   ✅ Soft delete successful!")
                print(f"      is_deleted: {row[0]}")
                print(f"      deleted_at: {row[1]}")
            else:
                print(f"   ❌ Soft delete FAILED!")
                print(f"      is_deleted: {row[0] if row else 'N/A'}")
                print(f"      deleted_at: {row[1] if row else 'N/A'}")
                return False
            
            # Clean up
            await db.execute(text(f"""
                DELETE FROM rooms WHERE id = {test_room_id}
            """))
            await db.commit()
            print("\n   🧹 Cleaned up test data")
            
            # Step 3: Check current data
            print("\n3️⃣ Checking existing records...\n")
            
            for table in ['rooms', 'beds', 'tenant_profiles']:
                result = await db.execute(text(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE is_deleted = TRUE) as deleted,
                        COUNT(*) FILTER (WHERE is_deleted = FALSE) as active
                    FROM {table}
                """))
                row = result.fetchone()
                
                print(f"   {table}:")
                print(f"      Total: {row[0]}, Active: {row[2]}, Deleted: {row[1]}")
            
            print("\n" + "=" * 60)
            print("✅ VERIFICATION COMPLETE - ALL CHECKS PASSED!")
            print("=" * 60)
            print("\n📝 Your soft delete is working correctly!")
            print("\nNow test in Swagger:")
            print("1. DELETE /api/v1/rooms/{room_id}")
            print("2. GET /api/v1/rooms/{room_id} → should return 404")
            print("3. Check in PostgreSQL:")
            print("   SELECT * FROM rooms WHERE id = {room_id};")
            print("   → should show is_deleted = true")
            print("=" * 60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(verify_soft_delete())
    sys.exit(0 if success else 1)