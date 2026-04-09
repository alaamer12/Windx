import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, func
from app.models.attribute_node import AttributeNode
from app.core.config import get_settings

async def check():
    settings = get_settings()
    engine = create_async_engine(settings.database.url)
    async with engine.begin() as conn:
        stmt = select(func.count()).where(
            AttributeNode.node_type == "entity_path",
            AttributeNode.page_type == "profile"
        )
        result = await conn.execute(stmt)
        count = result.scalar()
        print(f"Total entity_path nodes: {count}")
        
        if count > 0:
            stmt = select(AttributeNode).where(
                AttributeNode.node_type == "entity_path",
                AttributeNode.page_type == "profile"
            ).limit(5)
            result = await conn.execute(stmt)
            for row in result.fetchall():
                print(f"Path: {row.ltree_path}, Metadata: {row.metadata_}")
                
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
