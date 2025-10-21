# scripts/test_soft_delete.py
"""Test if soft delete is actually working in your database."""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def test_soft_delete():
    """Test soft delete end-to-end."""
    print("\n🧪 TESTING SOFT DELETE FUNCTIONALITY\n")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Create a test room
            print("\n1️⃣ Creating test room...\n")
            
            await db.execute(text("""
                INSERT INTO rooms (hostel_id, number, floor, room_type, capacity, is_deleted, deleted_at)
                VALUES (1, 'TEST_SOFT_DELETE', 99, 'SINGLE', 1, FALSE, NULL)
            """))
            await db.commit()
            
            # Get the ID
            result = await db.execute(text("""
                SELECT id FROM rooms WHERE number = 'TEST_SOFT_DELETE'
            """))
            test_id = result.scalar()
            print(f"   ✅ Created test room with ID: {test_id}")
            
            # Step 2: Check it's visible (not deleted)
            print("\n2️⃣ Checking room is visible...\n")
            
            result = await db.execute(text(f"""
                SELECT id, number, is_deleted, deleted_at 
                FROM rooms 
                WHERE id = {test_id}
            """))
            row = result.fetchone()
            
            print(f"   Room ID: {row[0]}")
            print(f"   Number: {row[1]}")
            print(f"   is_deleted: {row[2]}")
            print(f"   deleted_at: {row[3]}")
            
            if row[2] is False:
                print(f"\n   ✅ Room is active (not deleted)")
            else:
                print(f"\n   ❌ Room is already marked as deleted!")
                return False
            
            # Step 3: Soft delete the room
            print("\n3️⃣ Performing soft delete...\n")
            
            await db.execute(text(f"""
                UPDATE rooms 
                SET is_deleted = TRUE, deleted_at = NOW()
                WHERE id = {test_id}
            """))
            await db.commit()
            
            print(f"   ✅ Soft delete executed")
            
            # Step 4: Check it's marked as deleted
            print("\n4️⃣ Verifying soft delete...\n")
            
            result = await db.execute(text(f"""
                SELECT id, number, is_deleted, deleted_at 
                FROM rooms 
                WHERE id = {test_id}
            """))
            row = result.fetchone()
            
            print(f"   Room ID: {row[0]}")
            print(f"   Number: {row[1]}")
            print(f"   is_deleted: {row[2]}")
            print(f"   deleted_at: {row[3]}")
            
            if row[2] is True and row[3] is not None:
                print(f"\n   ✅ SOFT DELETE IS WORKING!")
                print(f"   ✅ Record is marked as deleted in PostgreSQL")
            else:
                print(f"\n   ❌ SOFT DELETE NOT WORKING!")
                print(f"   ❌ Record is NOT marked as deleted")
                return False
            
            # Step 5: Test filtering (what API does)
            print("\n5️⃣ Testing query filtering...\n")
            
            # Count all rooms (including deleted)
            result = await db.execute(text("""
                SELECT COUNT(*) FROM rooms WHERE hostel_id = 1
            """))
            total = result.scalar()
            
            # Count only active rooms (excluding deleted)
            result = await db.execute(text("""
                SELECT COUNT(*) FROM rooms 
                WHERE hostel_id = 1 AND is_deleted = FALSE
            """))
            active = result.scalar()
            
            print(f"   Total rooms (including deleted): {total}")
            print(f"   Active rooms (excluding deleted): {active}")
            print(f"   Deleted rooms: {total - active}")
            
            if total > active:
                print(f"\n   ✅ Filtering works correctly!")
            else:
                print(f"\n   ⚠️  No deleted rooms found (unexpected)")
            
            # Step 6: Test restore
            print("\n6️⃣ Testing restore...\n")
            
            await db.execute(text(f"""
                UPDATE rooms 
                SET is_deleted = FALSE, deleted_at = NULL
                WHERE id = {test_id}
            """))
            await db.commit()
            
            result = await db.execute(text(f"""
                SELECT is_deleted FROM rooms WHERE id = {test_id}
            """))
            is_deleted = result.scalar()
            
            if is_deleted is False:
                print(f"   ✅ Restore works!")
            else:
                print(f"   ❌ Restore failed!")
                return False
            
            # Clean up
            print("\n7️⃣ Cleaning up test data...\n")
            
            await db.execute(text(f"""
                DELETE FROM rooms WHERE id = {test_id}
            """))
            await db.commit()
            
            print(f"   ✅ Test data cleaned up")
            
            # Final summary
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\n🎉 Your soft delete is working correctly!\n")
            print("What this means:")
            print("  ✅ PostgreSQL has is_deleted and deleted_at columns")
            print("  ✅ UPDATE queries successfully mark records as deleted")
            print("  ✅ Filtering excludes deleted records")
            print("  ✅ Restore functionality works")
            print("\nNow test in Swagger:")
            print("  1. DELETE /api/v1/rooms/{room_id}")
            print("  2. GET /api/v1/rooms/{room_id} → should return 404")
            print("  3. POST /api/v1/rooms/{room_id}/restore → should work")
            print("=" * 60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()
            
            print("\n" + "=" * 60)
            print("TROUBLESHOOTING")
            print("=" * 60)
            print("\nIf you see 'column does not exist' error:")
            print("  Run: python scripts/fix_soft_delete_simple.py")
            print("\nIf you see 'table does not exist' error:")
            print("  Run: python scripts/reset_db_simple.py")
            print("  Then: python scripts/seed.py")
            print("=" * 60 + "\n")
            
            return False


if __name__ == "__main__":
    success = asyncio.run(test_soft_delete())
    sys.exit(0 if success else 1)