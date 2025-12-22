#!/usr/bin/env python3
"""
Test script to verify inline editing functionality works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import get_db
from app.services.entry import EntryService
from app.models.user import User
from app.models.configuration import Configuration
from sqlalchemy import select

async def test_inline_editing():
    """Test the inline editing functionality."""
    print("🧪 Testing inline editing functionality...")
    
    async for db in get_db():
        try:
            # Get a superuser for testing
            stmt = select(User).where(User.is_superuser == True).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No superuser found for testing")
                return
            
            print(f"✅ Using user: {user.email}")
            
            # Get a configuration for testing
            stmt = select(Configuration).limit(1)
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
            if not config:
                print("❌ No configuration found for testing")
                return
            
            print(f"✅ Using configuration ID: {config.id}")
            
            # Test the update_preview_value method
            entry_service = EntryService(db)
            
            # Test updating a field
            test_field = "Name"
            test_value = "Test Updated Value"
            
            print(f"🔄 Testing update of field '{test_field}' to '{test_value}'...")
            
            updated_config = await entry_service.update_preview_value(
                config.id, test_field, test_value, user
            )
            
            print(f"✅ Update successful! Configuration name: {updated_config.name}")
            
            # Test preview generation
            print("🔄 Testing preview generation...")
            preview_data = await entry_service.generate_preview_data(config.id, user)
            
            print(f"✅ Preview generated with {len(preview_data.table.rows)} rows")
            print(f"   Headers: {len(preview_data.table.headers)} columns")
            
            # Test list previews
            print("🔄 Testing list previews...")
            preview_table = await entry_service.list_previews(config.manufacturing_type_id, user)
            
            print(f"✅ Preview list generated with {len(preview_table.rows)} rows")
            
            print("🎉 All tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(test_inline_editing())