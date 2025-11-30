"""Example: Hierarchy Insertion with HierarchyBuilderService

This example demonstrates how to use the HierarchyBuilderService to create
and manage hierarchical attribute data for product configuration.

Features demonstrated:
- Creating manufacturing types
- Creating individual nodes with automatic path calculation
- Creating entire hierarchies from nested dictionaries
- Getting tree as JSON-serializable Pydantic models
- Generating ASCII tree visualizations
- Generating graphical tree plots

Requirements:
- Database connection configured in .env
- PostgreSQL with LTREE extension enabled
- Optional: matplotlib for tree plotting

Usage:
    python examples/hierarchy_insertion.py
"""

import asyncio
import json
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.hierarchy_builder import HierarchyBuilderService


async def example_create_manufacturing_type(service: HierarchyBuilderService):
    """Example 1: Create a manufacturing type.
    
    Manufacturing types are the root of the hierarchy. Each manufacturing type
    represents a product category (e.g., Window, Door, Table) and has its own
    attribute tree.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Creating a Manufacturing Type")
    print("="*80)
    
    # Create a manufacturing type for casement windows
    window_type = await service.create_manufacturing_type(
        name="Casement Window",
        description="Energy-efficient casement windows with superior ventilation",
        base_category="window",
        base_price=Decimal("200.00"),  # Starting price
        base_weight=Decimal("15.00"),  # Base weight in kg
    )
    
    print(f"\n✓ Created manufacturing type:")
    print(f"  ID: {window_type.id}")
    print(f"  Name: {window_type.name}")
    print(f"  Base Price: ${window_type.base_price}")
    print(f"  Base Weight: {window_type.base_weight} kg")
    
    return window_type


async def example_create_nodes_manually(
    service: HierarchyBuilderService,
    manufacturing_type_id: int
):
    """Example 2: Create nodes manually with automatic path calculation.
    
    This example shows how to create individual nodes one at a time.
    The service automatically calculates the LTREE path and depth for each node.
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Creating Nodes Manually")
    print("="*80)
    
    # Create a root category node
    print("\n→ Creating root category node...")
    frame_material = await service.create_node(
        manufacturing_type_id=manufacturing_type_id,
        name="Frame Material",
        node_type="category",
        description="Frame material options",
    )
    
    print(f"✓ Created: {frame_material.name}")
    print(f"  LTREE Path: {frame_material.ltree_path}")
    print(f"  Depth: {frame_material.depth}")
    
    # Create an attribute node under the category
    print("\n→ Creating attribute node...")
    material_type = await service.create_node(
        manufacturing_type_id=manufacturing_type_id,
        name="Material Type",
        node_type="attribute",
        parent_node_id=frame_material.id,
        data_type="selection",
        ui_component="dropdown",
        required=True,
        description="Select the frame material",
    )
    
    print(f"✓ Created: {material_type.name}")
    print(f"  LTREE Path: {material_type.ltree_path}")
    print(f"  Depth: {material_type.depth}")
    
    # Create option nodes with pricing
    print("\n→ Creating option nodes with pricing...")
    
    aluminum = await service.create_node(
        manufacturing_type_id=manufacturing_type_id,
        name="Aluminum",
        node_type="option",
        parent_node_id=material_type.id,
        data_type="string",
        price_impact_type="fixed",
        price_impact_value=Decimal("50.00"),  # Adds $50 to base price
        weight_impact=Decimal("2.00"),  # Adds 2kg to base weight
        description="Durable aluminum frame",
        help_text="Best for coastal areas with high humidity",
    )
    
    print(f"✓ Created: {aluminum.name}")
    print(f"  LTREE Path: {aluminum.ltree_path}")
    print(f"  Depth: {aluminum.depth}")
    print(f"  Price Impact: +${aluminum.price_impact_value}")
    print(f"  Weight Impact: +{aluminum.weight_impact} kg")
    
    vinyl = await service.create_node(
        manufacturing_type_id=manufacturing_type_id,
        name="Vinyl",
        node_type="option",
        parent_node_id=material_type.id,
        data_type="string",
        price_impact_type="fixed",
        price_impact_value=Decimal("30.00"),  # Adds $30 to base price
        weight_impact=Decimal("1.50"),  # Adds 1.5kg to base weight
        description="Low-maintenance vinyl frame",
        help_text="Most cost-effective option",
    )
    
    print(f"✓ Created: {vinyl.name}")
    print(f"  LTREE Path: {vinyl.ltree_path}")
    print(f"  Depth: {vinyl.depth}")
    print(f"  Price Impact: +${vinyl.price_impact_value}")
    print(f"  Weight Impact: +{vinyl.weight_impact} kg")
    
    wood = await service.create_node(
        manufacturing_type_id=manufacturing_type_id,
        name="Wood",
        node_type="option",
        parent_node_id=material_type.id,
        data_type="string",
        price_impact_type="fixed",
        price_impact_value=Decimal("100.00"),  # Adds $100 to base price
        weight_impact=Decimal("3.00"),  # Adds 3kg to base weight
        description="Premium natural wood frame",
        help_text="Classic aesthetic with excellent insulation",
    )
    
    print(f"✓ Created: {wood.name}")
    print(f"  LTREE Path: {wood.ltree_path}")
    print(f"  Depth: {wood.depth}")
    print(f"  Price Impact: +${wood.price_impact_value}")
    print(f"  Weight Impact: +{wood.weight_impact} kg")
    
    return frame_material


async def example_create_hierarchy_from_dict(
    service: HierarchyBuilderService,
    manufacturing_type_id: int
):
    """Example 3: Create entire hierarchy from nested dictionary.
    
    This example shows how to create a complete hierarchy in one operation
    using a nested dictionary structure. This is much faster than creating
    nodes one at a time and ensures transactional consistency (all-or-nothing).
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Creating Hierarchy from Dictionary")
    print("="*80)
    
    # Define a complete hierarchy as a nested dictionary
    hierarchy_data = {
        "name": "Glass Type",
        "node_type": "category",
        "description": "Glass configuration options",
        "children": [
            {
                "name": "Pane Count",
                "node_type": "attribute",
                "data_type": "selection",
                "ui_component": "radio",
                "required": True,
                "description": "Number of glass panes",
                "children": [
                    {
                        "name": "Single Pane",
                        "node_type": "option",
                        "data_type": "string",
                        "price_impact_type": "fixed",
                        "price_impact_value": 0,  # No additional cost
                        "weight_impact": 3.0,
                        "description": "Basic single-pane glass",
                    },
                    {
                        "name": "Double Pane",
                        "node_type": "option",
                        "data_type": "string",
                        "price_impact_type": "fixed",
                        "price_impact_value": 80.00,  # Adds $80
                        "weight_impact": 5.0,
                        "description": "Energy-efficient double-pane glass",
                    },
                    {
                        "name": "Triple Pane",
                        "node_type": "option",
                        "data_type": "string",
                        "price_impact_type": "fixed",
                        "price_impact_value": 150.00,  # Adds $150
                        "weight_impact": 7.0,
                        "description": "Maximum insulation triple-pane glass",
                    },
                ],
            },
            {
                "name": "Glass Coating",
                "node_type": "attribute",
                "data_type": "selection",
                "ui_component": "checkbox",
                "required": False,
                "description": "Optional glass coatings",
                "children": [
                    {
                        "name": "Low-E Coating",
                        "node_type": "option",
                        "data_type": "boolean",
                        "price_impact_type": "fixed",
                        "price_impact_value": 40.00,
                        "description": "Reduces heat transfer",
                    },
                    {
                        "name": "Tinted Glass",
                        "node_type": "option",
                        "data_type": "boolean",
                        "price_impact_type": "fixed",
                        "price_impact_value": 30.00,
                        "description": "Reduces glare and UV",
                    },
                    {
                        "name": "UV Protection",
                        "node_type": "option",
                        "data_type": "boolean",
                        "price_impact_type": "fixed",
                        "price_impact_value": 50.00,
                        "description": "Blocks harmful UV rays",
                    },
                ],
            },
        ],
    }
    
    print("\n→ Creating hierarchy from dictionary...")
    print(f"  Root: {hierarchy_data['name']}")
    print(f"  Children: {len(hierarchy_data['children'])} attributes")
    
    # Create the entire hierarchy in one transaction
    root_node = await service.create_hierarchy_from_dict(
        manufacturing_type_id=manufacturing_type_id,
        hierarchy_data=hierarchy_data,
    )
    
    print(f"\n✓ Created hierarchy:")
    print(f"  Root Node: {root_node.name}")
    print(f"  LTREE Path: {root_node.ltree_path}")
    print(f"  Depth: {root_node.depth}")
    
    return root_node


async def example_get_tree_as_json(
    service: HierarchyBuilderService,
    manufacturing_type_id: int
):
    """Example 4: Get tree as JSON-serializable Pydantic models.
    
    This example shows how to retrieve the attribute tree as Pydantic models
    that can be easily serialized to JSON for API responses or visualization.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Getting Tree as JSON")
    print("="*80)
    
    # Get the complete tree as Pydantic models
    print("\n→ Retrieving tree as Pydantic models...")
    tree = await service.pydantify(manufacturing_type_id=manufacturing_type_id)
    
    print(f"✓ Retrieved {len(tree)} root nodes")
    
    # Serialize to JSON
    print("\n→ Serializing to JSON...")
    tree_json = json.dumps(
        [node.model_dump() for node in tree],
        indent=2,
        default=str,  # Handle Decimal and datetime objects
    )
    
    # Print first 1000 characters of JSON
    print("\n✓ JSON output (first 1000 characters):")
    print(tree_json[:1000])
    if len(tree_json) > 1000:
        print(f"... ({len(tree_json) - 1000} more characters)")
    
    # You can also save to a file
    with open("hierarchy_tree.json", "w") as f:
        f.write(tree_json)
    print("\n✓ Saved complete JSON to: hierarchy_tree.json")
    
    return tree


async def example_generate_ascii_tree(
    service: HierarchyBuilderService,
    manufacturing_type_id: int
):
    """Example 5: Generate ASCII tree visualization.
    
    This example shows how to generate a human-readable ASCII tree
    representation using box-drawing characters.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Generating ASCII Tree Visualization")
    print("="*80)
    
    # Generate ASCII tree
    print("\n→ Generating ASCII tree...")
    ascii_tree = await service.asciify(manufacturing_type_id=manufacturing_type_id)
    
    print("\n✓ ASCII Tree:")
    print(ascii_tree)
    
    # You can also save to a file
    with open("hierarchy_tree.txt", "w", encoding="utf-8") as f:
        f.write(ascii_tree)
    print("\n✓ Saved ASCII tree to: hierarchy_tree.txt")
    
    return ascii_tree


async def example_generate_tree_plot(
    service: HierarchyBuilderService,
    manufacturing_type_id: int
):
    """Example 6: Generate graphical tree plot (requires matplotlib).
    
    This example shows how to generate a visual tree plot using matplotlib.
    This is optional and requires matplotlib to be installed.
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Generating Graphical Tree Plot")
    print("="*80)
    
    try:
        import matplotlib.pyplot as plt
        
        # Generate tree plot
        print("\n→ Generating tree plot...")
        fig = await service.plot_tree(manufacturing_type_id=manufacturing_type_id)
        
        # Save to file
        output_file = "hierarchy_tree.png"
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Saved tree plot to: {output_file}")
        
        # Optionally display (comment out if running headless)
        # plt.show()
        
        plt.close(fig)
        
    except ImportError:
        print("\n⚠ Matplotlib not installed. Skipping tree plot example.")
        print("  Install with: pip install matplotlib")
    except Exception as e:
        print(f"\n⚠ Error generating tree plot: {e}")


async def example_complex_hierarchy(
    service: HierarchyBuilderService,
    manufacturing_type_id: int
):
    """Example 7: Create a complex real-world hierarchy.
    
    This example demonstrates creating a more complex hierarchy similar to
    the uPVC window example from the requirements.
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: Creating Complex Real-World Hierarchy")
    print("="*80)
    
    # Define a complex hierarchy structure
    upvc_hierarchy = {
        "name": "uPVC System",
        "node_type": "category",
        "description": "uPVC window system options",
        "children": [
            {
                "name": "System Manufacturer",
                "node_type": "attribute",
                "data_type": "selection",
                "ui_component": "dropdown",
                "required": True,
                "children": [
                    {
                        "name": "Aluplast",
                        "node_type": "option",
                        "children": [
                            {
                                "name": "Profile Series",
                                "node_type": "attribute",
                                "data_type": "selection",
                                "ui_component": "radio",
                                "required": True,
                                "children": [
                                    {
                                        "name": "IDEAL 4000",
                                        "node_type": "option",
                                        "price_impact_value": 50.00,
                                        "description": "Standard 5-chamber profile",
                                        "children": [
                                            {
                                                "name": "Color & Decor",
                                                "node_type": "attribute",
                                                "data_type": "selection",
                                                "ui_component": "dropdown",
                                                "required": True,
                                                "children": [
                                                    {
                                                        "name": "Standard White",
                                                        "node_type": "option",
                                                        "price_impact_value": 0,
                                                    },
                                                    {
                                                        "name": "Special Colors",
                                                        "node_type": "option",
                                                        "price_impact_value": 25.00,
                                                    },
                                                    {
                                                        "name": "Aludec Collection",
                                                        "node_type": "option",
                                                        "price_impact_value": 35.00,
                                                    },
                                                    {
                                                        "name": "Woodec Collection",
                                                        "node_type": "option",
                                                        "price_impact_value": 40.00,
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                    {
                                        "name": "IDEAL 5000",
                                        "node_type": "option",
                                        "price_impact_value": 75.00,
                                        "description": "Premium 6-chamber profile",
                                        "children": [
                                            {
                                                "name": "Color & Decor",
                                                "node_type": "attribute",
                                                "data_type": "selection",
                                                "ui_component": "dropdown",
                                                "required": True,
                                                "children": [
                                                    {
                                                        "name": "Standard White",
                                                        "node_type": "option",
                                                        "price_impact_value": 0,
                                                    },
                                                    {
                                                        "name": "Special Colors",
                                                        "node_type": "option",
                                                        "price_impact_value": 30.00,
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                "name": "Window Type",
                                "node_type": "attribute",
                                "data_type": "selection",
                                "ui_component": "dropdown",
                                "required": True,
                                "children": [
                                    {
                                        "name": "Single Sash",
                                        "node_type": "option",
                                        "price_impact_value": 100.00,
                                    },
                                    {
                                        "name": "Double Sash",
                                        "node_type": "option",
                                        "price_impact_value": 180.00,
                                    },
                                    {
                                        "name": "Triple Sash",
                                        "node_type": "option",
                                        "price_impact_value": 250.00,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "name": "Kommerling",
                        "node_type": "option",
                        "children": [
                            {
                                "name": "Profile Series",
                                "node_type": "attribute",
                                "data_type": "selection",
                                "ui_component": "radio",
                                "required": True,
                                "children": [
                                    {
                                        "name": "76MD",
                                        "node_type": "option",
                                        "price_impact_value": 60.00,
                                    },
                                    {
                                        "name": "88MD",
                                        "node_type": "option",
                                        "price_impact_value": 90.00,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Dimensions",
                "node_type": "category",
                "children": [
                    {
                        "name": "Width",
                        "node_type": "attribute",
                        "data_type": "number",
                        "ui_component": "input",
                        "required": True,
                        "validation_rules": {
                            "rule_type": "range",
                            "min": 385,
                            "max": 3010,
                            "message": "Width must be between 385mm and 3010mm",
                        },
                        "description": "Window width in millimeters",
                    },
                    {
                        "name": "Height",
                        "node_type": "attribute",
                        "data_type": "number",
                        "ui_component": "input",
                        "required": True,
                        "validation_rules": {
                            "rule_type": "range",
                            "min": 385,
                            "max": 3010,
                            "message": "Height must be between 385mm and 3010mm",
                        },
                        "description": "Window height in millimeters",
                    },
                ],
            },
        ],
    }
    
    print("\n→ Creating complex uPVC hierarchy...")
    print(f"  Root: {upvc_hierarchy['name']}")
    print(f"  Total depth: 6+ levels")
    
    # Create the hierarchy
    root_node = await service.create_hierarchy_from_dict(
        manufacturing_type_id=manufacturing_type_id,
        hierarchy_data=upvc_hierarchy,
    )
    
    print(f"\n✓ Created complex hierarchy:")
    print(f"  Root Node: {root_node.name}")
    print(f"  LTREE Path: {root_node.ltree_path}")
    
    # Generate ASCII visualization of the complex hierarchy
    print("\n→ Generating ASCII visualization...")
    ascii_tree = await service.asciify(manufacturing_type_id=manufacturing_type_id)
    print("\n✓ Complete Hierarchy:")
    print(ascii_tree)
    
    return root_node


async def main():
    """Main function to run all examples."""
    print("\n" + "="*80)
    print("HIERARCHY INSERTION EXAMPLES")
    print("="*80)
    print("\nThis script demonstrates the HierarchyBuilderService capabilities.")
    print("Each example builds on the previous one to show different features.")
    
    # Get database session
    async for session in get_async_session():
        try:
            # Initialize service
            service = HierarchyBuilderService(session)
            
            # Example 1: Create manufacturing type
            window_type = await example_create_manufacturing_type(service)
            
            # Example 2: Create nodes manually
            await example_create_nodes_manually(service, window_type.id)
            
            # Example 3: Create hierarchy from dictionary
            await example_create_hierarchy_from_dict(service, window_type.id)
            
            # Example 4: Get tree as JSON
            await example_get_tree_as_json(service, window_type.id)
            
            # Example 5: Generate ASCII tree
            await example_generate_ascii_tree(service, window_type.id)
            
            # Example 6: Generate tree plot (optional)
            await example_generate_tree_plot(service, window_type.id)
            
            # Example 7: Create complex hierarchy
            await example_complex_hierarchy(service, window_type.id)
            
            print("\n" + "="*80)
            print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
            print("="*80)
            print("\nGenerated files:")
            print("  - hierarchy_tree.json (JSON export)")
            print("  - hierarchy_tree.txt (ASCII visualization)")
            print("  - hierarchy_tree.png (graphical plot, if matplotlib installed)")
            print("\nNext steps:")
            print("  - View the admin dashboard at: /admin/hierarchy")
            print("  - Read the documentation: docs/HIERARCHY_ADMIN_DASHBOARD.md")
            print("  - Explore the API endpoints in the OpenAPI docs")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        break  # Only use first session


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
