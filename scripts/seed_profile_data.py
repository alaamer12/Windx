#!/usr/bin/env python3
"""Seed dummy profile data for testing.

This script creates sample profile configurations to test the profile entry system.
It creates realistic data based on the CSV structure and validation rules.
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.database.connection import get_async_session
from app.models.configuration import Configuration
from app.models.manufacturing_type import ManufacturingType
from app.services.entry import EntryService
from app.schemas.entry import ProfileEntryData


async def seed_profile_data():
    """Seed dummy profile data for testing."""
    print("🌱 Starting profile data seeding...")
    
    settings = get_settings()
    print(f"📊 Database: {settings.database.provider}")
    
    async for session in get_async_session():
        try:
            # Get any manufacturing type
            from sqlalchemy import select, text
            result = await session.execute(select(ManufacturingType).limit(1))
            manufacturing_type = result.scalar_one_or_none()
            
            if not manufacturing_type:
                print("❌ No manufacturing types found. Please create one first.")
                print("   You can create one via the admin interface or database.")
                return
            
            print(f"✅ Found manufacturing type: {manufacturing_type.name} (ID: {manufacturing_type.id})")
            
            # Get any admin user for the seeding
            from app.models.user import User
            result = await session.execute(select(User).where(User.is_superuser == True).limit(1))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ No admin user found. Please create one first.")
                return
                
            print(f"✅ Found admin user: {admin_user.email}")
            
            # Create EntryService
            entry_service = EntryService(session)
            
            # Sample profile data based on CSV structure
            # First entry: Correct data from CSV first row
            # Subsequent entries: Intentionally wrong data to test validation
            sample_profiles = [
                # ✅ CORRECT DATA - From CSV first row
                {
                    "manufacturing_type_id": manufacturing_type.id,
                    "name": "Frame with renovation 3.8 cm",
                    "type": "Frame",
                    "company": "kompen",
                    "material": "UPVC",
                    "opening_system": "Casement",
                    "system_series": "Kom700",
                    "code": "705",
                    "length_of_beam": Decimal("6.0"),
                    "renovation": "yes",  # CSV shows "yes/no" - using "yes"
                    "width": Decimal("61.0"),
                    "builtin_flyscreen_track": False,  # CSV shows "n.a"
                    "total_width": None,  # CSV shows "n.a"
                    "flyscreen_track_height": None,  # CSV shows "n.a"
                    "front_height": Decimal("31.0"),
                    "rear_height": Decimal("51.0"),  # Different from front_height
                    "glazing_height": Decimal("20.0"),
                    "renovation_height": Decimal("38.0"),
                    "glazing_undercut_height": None,  # CSV shows "n.a"
                    "pic": "",  # CSV shows empty
                    "sash_overlap": None,  # CSV shows "n.a"
                    "flying_mullion_horizontal_clearance": None,
                    "flying_mullion_vertical_clearance": None,
                    "steel_material_thickness": None,
                    "weight_per_meter": Decimal("1045.0"),  # This seems high, might trigger validation
                    "reinforcement_steel": "multi choice from steel database",
                    "colours": "White",
                    "price_per_meter": Decimal("150.0"),
                    "price_per_beam": Decimal("900.0"),  # 150 * 6 = 900 ✅
                    "upvc_profile_discount": Decimal("20.0"),
                },
                
                # ❌ TEST CASE 1: Height difference validation error
                {
                    "manufacturing_type_id": manufacturing_type.id,
                    "name": "Test Height Difference Error",
                    "type": "Frame",
                    "company": "kompen",
                    "material": "UPVC",
                    "opening_system": "Casement",
                    "system_series": "Kom700",
                    "code": "TEST-001",
                    "length_of_beam": Decimal("6.0"),
                    "renovation": "no",
                    "width": Decimal("70.0"),
                    "builtin_flyscreen_track": False,
                    "front_height": Decimal("25.0"),
                    "rear_height": Decimal("100.0"),  # 75mm difference - should trigger validation error
                    "glazing_height": Decimal("20.0"),
                    "weight_per_meter": Decimal("2.5"),
                    "reinforcement_steel": "Standard",
                    "colours": "White",
                    "price_per_meter": Decimal("45.00"),
                    "price_per_beam": Decimal("270.00"),
                    "upvc_profile_discount": Decimal("20.0"),
                },
                
                # ❌ TEST CASE 2: Price calculation validation error
                {
                    "manufacturing_type_id": manufacturing_type.id,
                    "name": "Test Price Calculation Error",
                    "type": "sash",
                    "company": "kompen",
                    "material": "UPVC",
                    "opening_system": "Casement",
                    "system_series": "Kom701",
                    "code": "TEST-002",
                    "length_of_beam": Decimal("4.5"),
                    "renovation": "no",
                    "width": Decimal("60.0"),
                    "builtin_flyscreen_track": False,
                    "front_height": Decimal("22.0"),
                    "rear_height": Decimal("22.0"),
                    "glazing_height": Decimal("18.0"),
                    "sash_overlap": Decimal("15.0"),
                    "weight_per_meter": Decimal("2.1"),
                    "reinforcement_steel": "Premium",
                    "colours": "White, Anthracite",
                    "price_per_meter": Decimal("52.00"),
                    "price_per_beam": Decimal("999.00"),  # Wrong! Should be 52 * 4.5 = 234
                    "upvc_profile_discount": Decimal("15.0"),
                },
                
                # ❌ TEST CASE 3: Missing required fields
                {
                    "manufacturing_type_id": manufacturing_type.id,
                    "name": "",  # Empty name - should trigger required field error
                    "type": "",  # Empty type - should trigger required field error
                    "company": "kompen",
                    "material": "UPVC",
                    "opening_system": "Casement",
                    "system_series": "Kom800",
                    "code": "TEST-003",
                    "length_of_beam": Decimal("3.0"),
                    "renovation": "n.a",
                    "width": Decimal("50.0"),
                    "builtin_flyscreen_track": False,
                    "front_height": Decimal("20.0"),
                    "rear_height": Decimal("20.0"),
                    "weight_per_meter": Decimal("1.8"),
                    "reinforcement_steel": "Standard",
                    "colours": "White, Brown",
                    "price_per_meter": Decimal("38.00"),
                    "price_per_beam": Decimal("114.00"),
                    "upvc_profile_discount": Decimal("25.0"),
                },
                
                # ❌ TEST CASE 4: Invalid numeric ranges
                {
                    "manufacturing_type_id": manufacturing_type.id,
                    "name": "Test Invalid Ranges",
                    "type": "glazing bead",
                    "company": "kompen",
                    "material": "UPVC",
                    "opening_system": "All",
                    "system_series": "All",
                    "code": "TEST-004",
                    "length_of_beam": Decimal("-1.0"),  # Negative length - should trigger validation
                    "renovation": "no",
                    "width": Decimal("12.0"),
                    "builtin_flyscreen_track": False,
                    "front_height": Decimal("8.0"),
                    "rear_height": Decimal("8.0"),
                    "glazing_undercut_height": Decimal("6.0"),
                    "weight_per_meter": Decimal("0.3"),
                    "reinforcement_steel": "None",
                    "colours": "White, Brown, Grey, Anthracite",
                    "price_per_meter": Decimal("-10.00"),  # Negative price - should trigger validation
                    "price_per_beam": Decimal("21.25"),
                    "upvc_profile_discount": Decimal("150.0"),  # Over 100% - should trigger validation
                },
            ]
            
            print(f"📝 Creating {len(sample_profiles)} sample profiles...")
            
            created_count = 0
            for i, profile_data in enumerate(sample_profiles, 1):
                try:
                    print(f"  {i}. Creating '{profile_data['name']}'...")
                    
                    # Convert dict to ProfileEntryData model
                    profile_entry = ProfileEntryData(**profile_data)
                    
                    # Use the EntryService to save the profile
                    configuration = await entry_service.save_profile_configuration(profile_entry, admin_user)
                    
                    print(f"     ✅ Created configuration ID: {configuration.id}")
                    created_count += 1
                    
                except Exception as e:
                    print(f"     ❌ Failed to create '{profile_data['name']}': {e}")
                    print(f"         Error type: {type(e).__name__}")
                    if hasattr(e, 'field_errors'):
                        print(f"         Field errors: {e.field_errors}")
                    continue
            
            await session.commit()
            print(f"\n🎉 Successfully created {created_count}/{len(sample_profiles)} profile configurations!")
            
            # Show summary
            total_configs = await session.scalar(
                text("SELECT COUNT(*) FROM configurations WHERE manufacturing_type_id = :mfg_id"),
                {"mfg_id": manufacturing_type.id}
            )
            print(f"📊 Total configurations for '{manufacturing_type.name}': {total_configs}")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    print("🚀 Profile Data Seeder")
    print("=" * 50)
    
    try:
        asyncio.run(seed_profile_data())
        print("\n✅ Seeding completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Seeding interrupted by user")
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        sys.exit(1)