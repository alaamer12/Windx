"""Script to truncate configuration and transactional data.

This script clears all configurations, selections, templates, orders, 
quotes, and customer data from the database, while preserving 
core manufacturing types and attribute definitions.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import text
from app.database.connection import get_session_maker


async def truncate_config_data():
    """Truncate all configuration-related tables."""
    session_maker = get_session_maker()
    
    # List of core tables to truncate. 
    # Using CASCADE will automatically handle related child tables like
    # configuration_selections, order_items, quotes, etc.
    tables = [
        "configuration_selections",
        "template_selections",
        "order_items",
        "quotes",
        "orders",
        "configurations",
        "configuration_templates",
        "customers"
    ]
    
    print("🚀 Starting data truncation...")
    
    async with session_maker() as db:
        try:
            # Disable triggers to speed up and avoid constraints if necessary
            # (Though CASCADE handles foreign keys)
            
            for table in tables:
                print(f"  [TRUNCATE] {table}...")
                try:
                    # RESTART IDENTITY resets the auto-increment counters
                    # CASCADE handles dependent rows in other tables
                    await db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                except Exception as e:
                    print(f"  [WARNING] Could not truncate {table}: {e}")
            
            await db.commit()
            print("✅ All configuration and definition data has been truncated.")
            print("💡 You can now run setup scripts to seed fresh data.")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error during truncation: {e}")
            raise


if __name__ == "__main__":
    confirm = input("⚠️  WARNING: This will delete ALL configuration and definition data. Are you sure? (y/N): ")
    if confirm.lower() == 'y':
        asyncio.run(truncate_config_data())
    else:
        print("Operation cancelled.")
