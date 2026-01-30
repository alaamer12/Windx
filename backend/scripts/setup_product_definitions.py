#!/usr/bin/env python3
"""Setup script for creating product definition scopes from YAML configuration.

This script reads YAML configuration files from config/product_definition/ and
creates the necessary database records for definition scopes, entities, and their
metadata. This replaces the hard-coded DEFINITION_SCOPES constant in the relations service.

Usage:
    python setup_product_definitions.py                    # Setup all scopes
    python setup_product_definitions.py profile            # Setup profile scope only
    python setup_product_definitions.py glazing            # Setup glazing scope only
    python setup_product_definitions.py hardware           # Setup hardware scope only
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# Fix Windows CMD encoding issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_engine, get_session_maker
from app.models.attribute_node import AttributeNode


class ProductDefinitionSetup:
    """Setup class for creating product definition scopes from YAML configuration."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def setup_from_yaml_file(self, yaml_file: Path) -> None:
        """Setup product definitions from a YAML configuration file."""
        print(f"Setting up product definitions from {yaml_file.name}...")
        
        # Load YAML configuration
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            print(f"  [ERROR] Error loading YAML file: {e}")
            raise

        # Validate required fields
        required_fields = ['scope', 'label', 'entities', 'hierarchy']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field '{field}' in {yaml_file.name}")

        scope = config['scope']
        label = config['label']
        description = config.get('description', f"Definitions for {scope}")
        
        print(f"  [SCOPE] Scope: {scope}")
        print(f"  [LABEL] Label: {label}")

        # Clean existing scope data
        await self.clean_existing_scope_data(scope)

        # Create scope metadata record
        await self.create_scope_metadata(scope, label, description, config)

        # Create entity definitions
        await self.create_entity_definitions(scope, config['entities'])

        print(f"  [OK] Product definitions setup completed for {scope}")

    async def clean_existing_scope_data(self, scope: str) -> None:
        """Clean existing data for a scope to allow fresh setup."""
        print(f"  [CLEAN] Cleaning existing data for scope: {scope}")
        
        # Delete existing definition metadata nodes for this scope
        delete_stmt = delete(AttributeNode).where(
            AttributeNode.page_type == scope,
            AttributeNode.node_type.in_(['scope_metadata', 'entity_definition'])
        )
        result = await self.session.execute(delete_stmt)
        deleted_count = result.rowcount
        
        await self.session.commit()
        print(f"  [CLEAN] Deleted {deleted_count} existing definition records")

    async def create_scope_metadata(self, scope: str, label: str, description: str, config: Dict[str, Any]) -> None:
        """Create a metadata record for the scope."""
        print(f"  [METADATA] Creating scope metadata for {scope}")
        
        # Create scope metadata node
        scope_node = AttributeNode(
            name=scope,
            display_name=label,
            description=description,
            node_type="scope_metadata",
            data_type="object",
            ltree_path=f"definitions.{scope}",
            depth=1,
            page_type=scope,
            metadata_={
                "scope": scope,
                "label": label,
                "description": description,
                "hierarchy": config.get('hierarchy', {}),
                "dependencies": config.get('dependencies', []),
                "entity_count": len(config.get('entities', {}))
            },
            validation_rules={
                "is_scope_metadata": True,
                "scope": scope
            }
        )
        
        self.session.add(scope_node)
        await self.session.flush()
        print(f"  [METADATA] Created scope metadata (ID: {scope_node.id})")

    async def create_entity_definitions(self, scope: str, entities: Dict[str, Any]) -> None:
        """Create entity definition records."""
        print(f"  [ENTITIES] Creating {len(entities)} entity definitions for {scope}")
        
        for entity_type, entity_config in entities.items():
            await self.create_entity_definition(scope, entity_type, entity_config)
        
        await self.session.commit()
        print(f"  [ENTITIES] Completed creating entity definitions")

    async def create_entity_definition(self, scope: str, entity_type: str, config: Dict[str, Any]) -> None:
        """Create a single entity definition record."""
        print(f"    [ENTITY] Creating definition for {entity_type}")
        
        label = config.get('label', entity_type.replace('_', ' ').title())
        icon = config.get('icon', 'pi pi-box')
        placeholders = config.get('placeholders', {})
        metadata_fields = config.get('metadata_fields', [])
        special_ui = config.get('special_ui')
        
        # Create entity definition node
        entity_node = AttributeNode(
            name=entity_type,
            display_name=label,
            description=f"Entity definition for {label}",
            node_type="entity_definition",
            data_type="object",
            ltree_path=f"definitions.{scope}.{entity_type}",
            depth=2,
            page_type=scope,
            metadata_={
                "entity_type": entity_type,
                "label": label,
                "icon": icon,
                "placeholders": placeholders,
                "metadata_fields": metadata_fields,
                "special_ui": special_ui,
                "scope": scope
            },
            validation_rules={
                "is_entity_definition": True,
                "entity_type": entity_type,
                "scope": scope
            }
        )
        
        self.session.add(entity_node)
        await self.session.flush()
        print(f"    [ENTITY] Created {entity_type} definition (ID: {entity_node.id})")


async def setup_scope(scope: str) -> bool:
    """Setup a specific scope from its YAML configuration."""
    config_dir = Path(__file__).parent.parent / "config" / "product_definition"
    yaml_file = config_dir / f"{scope}.yaml"
    
    if not yaml_file.exists():
        print(f"[ERROR] Configuration file not found: {yaml_file}")
        return False

    engine = get_engine()
    session_maker = get_session_maker()

    try:
        async with session_maker() as session:
            setup = ProductDefinitionSetup(session)
            await setup.setup_from_yaml_file(yaml_file)
        
        print(f"[OK] {scope.title()} product definitions setup completed successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Error during {scope} setup: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def setup_all_scopes() -> None:
    """Setup all available product definition scopes."""
    config_dir = Path(__file__).parent.parent / "config" / "product_definition"
    
    if not config_dir.exists():
        print(f"[ERROR] Configuration directory not found: {config_dir}")
        return

    # Find all YAML files in the config directory
    yaml_files = list(config_dir.glob("*.yaml"))
    
    if not yaml_files:
        print(f"[ERROR] No YAML configuration files found in {config_dir}")
        return

    print(f"Found {len(yaml_files)} configuration files:")
    for yaml_file in yaml_files:
        print(f"  [FILE] {yaml_file.name}")

    success_count = 0
    for yaml_file in yaml_files:
        scope = yaml_file.stem  # filename without extension
        print(f"\n{'='*60}")
        print(f"Setting up {scope.title()} product definitions...")
        print('='*60)
        
        if await setup_scope(scope):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"Setup Summary: {success_count}/{len(yaml_files)} scopes completed successfully")
    print('='*60)


async def main():
    """Main setup function."""
    if len(sys.argv) > 1:
        # Setup specific scope
        scope = sys.argv[1].lower()
        print(f"Setting up {scope.title()} product definitions...")
        print("=" * 60)
        
        success = await setup_scope(scope)
        if not success:
            sys.exit(1)
    else:
        # Setup all scopes
        print("Setting up all product definition scopes...")
        print("=" * 60)
        await setup_all_scopes()


if __name__ == "__main__":
    asyncio.run(main())