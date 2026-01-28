import asyncio
import sys
import os

# Add the backend directory to sys.path to resolve 'app' correctly
backend_dir = os.path.join(os.getcwd(), 'backend')
sys.path.append(backend_dir)

from app.database import get_db
from app.models.attribute_node import AttributeNode
from sqlalchemy import select, and_

async def sync_metadata():
    print("--- METADATA SYNC (WITH NAMES) START ---")
    async for db in get_db():
        # 1. Get all complete dependency paths
        stmt = select(AttributeNode).where(
            and_(
                AttributeNode.node_type == "color_path",
                AttributeNode.page_type == "profile",
                AttributeNode.depth == 4
            )
        )
        result = await db.execute(stmt)
        paths = result.scalars().all()
        print(f"Found {len(paths)} dependency paths")

        # 2. Group by system_series name and fetch parent names
        series_links = {}
        for path in paths:
            rules = path.validation_rules or {}
            series_id = rules.get("system_series_id")
            company_id = rules.get("company_id")
            opening_id = rules.get("opening_system_id")
            
            if series_id:
                series_entity = await db.get(AttributeNode, series_id)
                if not series_entity: continue
                
                # Fetch parent names for compatibility with frontend (which expects names)
                company_entity = await db.get(AttributeNode, company_id) if company_id else None
                opening_entity = await db.get(AttributeNode, opening_id) if opening_id else None
                material_entity = await db.get(AttributeNode, material_id) if material_id else None
                
                series_name = series_entity.name
                if series_name not in series_links:
                    series_links[series_name] = {
                        "company_name": company_entity.name if company_entity else None,
                        "opening_name": opening_entity.name if opening_entity else None,
                        "material_name": material_entity.name if material_entity else None,
                    }

        print(f"Aggregated names for {len(series_links)} unique system series")

        # 3. Update the standalone system_series entities
        for series_name, links in series_links.items():
            stmt = select(AttributeNode).where(
                and_(
                    AttributeNode.name == series_name,
                    AttributeNode.node_type == "system_series"
                )
            )
            result = await db.execute(stmt)
            entities = result.scalars().all()
            
            for entity in entities:
                metadata = entity.metadata_ or {}
                # Inject the NAMES (strings) instead of IDs
                metadata["linked_company_material"] = links["company_name"]
                metadata["opening_system_id"] = links["opening_name"]
                metadata["linked_material_id"] = links["material_name"] # Add material name directly
                
                # Force update
                entity.metadata_ = None
                db.add(entity)
                await db.flush()
                entity.metadata_ = metadata
                db.add(entity)
                
                print(f"Updated metadata for series: {series_name} -> Company: {links['company_name']}, Material: {links['material_name']}, Opening: {links['opening_name']}")

        await db.commit()
        print("Changes committed to database")
        break
    print("--- METADATA SYNC (WITH NAMES) END ---")

if __name__ == "__main__":
    asyncio.run(sync_metadata())
