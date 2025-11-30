"""Create database tables script."""
import asyncio
from sqlalchemy import text

from app.database.connection import get_engine
from app.database.base import Base

# Import all models to register them with Base.metadata
from app.models.user import User
from app.models.session import Session
from app.models.customer import Customer
from app.models.manufacturing_type import ManufacturingType
from app.models.attribute_node import AttributeNode
from app.models.configuration import Configuration
from app.models.configuration_selection import ConfigurationSelection
from app.models.configuration_template import ConfigurationTemplate
from app.models.template_selection import TemplateSelection
from app.models.quote import Quote
from app.models.order import Order
from app.models.order_item import OrderItem


async def create_tables():
    """Create all database tables."""
    engine = get_engine()
    print("Creating LTREE extension...")
    async with engine.begin() as conn:
        # Create LTREE extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree"))
        print("✓ LTREE extension created")
        
        # Create all tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created successfully")


if __name__ == "__main__":
    asyncio.run(create_tables())
