import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent
sys.path.append(str(root / "backend"))

from app.database.connection import get_session_maker
from app.models.attribute_node import AttributeNode
from sqlalchemy import select, delete

async def setup_accessories_metadata():
    session_maker = get_session_maker()
    async with session_maker() as db:
        print("🚀 Setting up accessories (Hardware) metadata...")
        
        # Check if already exists
        result = await db.execute(select(AttributeNode).where(AttributeNode.page_type == 'accessories', AttributeNode.node_type == 'scope_metadata'))
        if result.scalar_one_or_none():
            print("  [OK] Metadata already exists for accessories")
            return

        scope_metadata = {
            "scope": "accessories",
            "label": "Hardware & Accessories",
            "description": "Accessories and hardware components for windows and doors",
            "entities": {
                "accessory": {
                    "label": "Accessory",
                    "icon": "pi pi-cog",
                    "description": "Hardware components like hinges, handles, and locks"
                }
            },
            "entity_count": 1
        }
        
        scope_node = AttributeNode(
            name="accessories",
            display_name="Hardware & Accessories",
            description="Hardware and accessory items for window systems",
            node_type="scope_metadata",
            data_type="object",
            ltree_path="definitions.accessories",
            depth=1,
            page_type="accessories",
            metadata_=scope_metadata,
            validation_rules={
                "is_scope_metadata": True,
                "scope": "accessories"
            }
        )
        
        db.add(scope_node)
        
        # Also add an entity definition for accessories if missing
        entity_node = AttributeNode(
            name="accessory",
            display_name="Accessory",
            description="Hardware accessory entity",
            node_type="entity_definition",
            data_type="object",
            ltree_path="definitions.accessories.accessory",
            depth=2,
            page_type="accessories",
            metadata_={
                "entity_type": "accessory",
                "label": "Accessory",
                "icon": "pi pi-cog",
                "placeholders": {
                    "name": "Enter accessory name"
                },
                "metadata_fields": [
                    {"name": "unit_price", "type": "number", "label": "Unit Price"},
                    {"name": "supplier_code", "type": "text", "label": "Supplier Code"}
                ],
                "scope": "accessories"
            },
            validation_rules={
                "is_entity_definition": True,
                "entity_type": "accessory",
                "scope": "accessories"
            }
        )
        db.add(entity_node)
        
        await db.commit()
        print("✅ Accessories metadata setup complete")

if __name__ == "__main__":
    asyncio.run(setup_accessories_metadata())
