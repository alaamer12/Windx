"""Example: ASCII Tree Visualization

This example demonstrates how to use the asciify() method to generate
human-readable ASCII tree representations of hierarchical attribute data.
"""

import asyncio
from decimal import Decimal

from app.database.connection import get_async_session
from app.services.hierarchy_builder import HierarchyBuilderService


async def main():
    """Demonstrate ASCII tree visualization."""

    # Get database session
    async for db_session in get_async_session():
        service = HierarchyBuilderService(db_session)

        # Create a manufacturing type
        print("Creating manufacturing type...")
        mfg_type = await service.create_manufacturing_type(
            name="Example Window",
            description="Example window for ASCII tree demo",
            base_category="window",
            base_price=Decimal("200.00"),
            base_weight=Decimal("15.00"),
        )
        print(f"✓ Created manufacturing type: {mfg_type.name} (ID: {mfg_type.id})")

        # Create a complex hierarchy
        print("\nCreating hierarchy...")
        hierarchy = {
            "name": "Frame Options",
            "node_type": "category",
            "children": [
                {
                    "name": "Material",
                    "node_type": "attribute",
                    "data_type": "selection",
                    "children": [
                        {
                            "name": "Aluminum",
                            "node_type": "option",
                            "price_impact_value": Decimal("50.00"),
                            "weight_impact": Decimal("2.00"),
                        },
                        {
                            "name": "Vinyl",
                            "node_type": "option",
                            "price_impact_value": Decimal("30.00"),
                            "weight_impact": Decimal("1.50"),
                        },
                        {
                            "name": "Wood",
                            "node_type": "option",
                            "price_impact_value": Decimal("100.00"),
                            "weight_impact": Decimal("3.00"),
                        },
                    ],
                },
                {
                    "name": "Color",
                    "node_type": "attribute",
                    "data_type": "selection",
                    "children": [
                        {
                            "name": "White",
                            "node_type": "option",
                            "price_impact_value": Decimal("0.00"),
                        },
                        {
                            "name": "Black",
                            "node_type": "option",
                            "price_impact_value": Decimal("25.00"),
                        },
                        {
                            "name": "Custom Color",
                            "node_type": "option",
                            "price_impact_value": Decimal("50.00"),
                        },
                    ],
                },
            ],
        }

        root = await service.create_hierarchy_from_dict(
            manufacturing_type_id=mfg_type.id,
            hierarchy_data=hierarchy,
        )
        print(f"✓ Created hierarchy with root: {root.name}")

        # Generate ASCII tree
        print("\n" + "=" * 60)
        print("ASCII TREE VISUALIZATION")
        print("=" * 60)
        tree_str = await service.asciify(manufacturing_type_id=mfg_type.id)
        print(tree_str)
        print("=" * 60)

        # Generate subtree (just the Material branch)
        print("\n" + "=" * 60)
        print("SUBTREE VISUALIZATION (Material branch only)")
        print("=" * 60)

        # Find the Material node
        nodes = await service.attr_node_repo.get_by_manufacturing_type(mfg_type.id)
        material_node = next((n for n in nodes if n.name == "Material"), None)

        if material_node:
            subtree_str = await service.asciify(
                manufacturing_type_id=mfg_type.id,
                root_node_id=material_node.id,
            )
            print(subtree_str)
            print("=" * 60)

        # Demonstrate with more complex hierarchy
        print("\n" + "=" * 60)
        print("COMPLEX HIERARCHY EXAMPLE")
        print("=" * 60)

        complex_hierarchy = {
            "name": "Glass Options",
            "node_type": "category",
            "children": [
                {
                    "name": "Pane Count",
                    "node_type": "attribute",
                    "children": [
                        {
                            "name": "Single Pane",
                            "node_type": "option",
                            "price_impact_value": Decimal("0.00"),
                        },
                        {
                            "name": "Double Pane",
                            "node_type": "option",
                            "price_impact_value": Decimal("80.00"),
                            "children": [
                                {
                                    "name": "Coating",
                                    "node_type": "attribute",
                                    "children": [
                                        {
                                            "name": "Low-E",
                                            "node_type": "option",
                                            "price_impact_value": Decimal("40.00"),
                                        },
                                        {
                                            "name": "Tinted",
                                            "node_type": "option",
                                            "price_impact_value": Decimal("30.00"),
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "name": "Triple Pane",
                            "node_type": "option",
                            "price_impact_value": Decimal("150.00"),
                            "children": [
                                {
                                    "name": "Coating",
                                    "node_type": "attribute",
                                    "children": [
                                        {
                                            "name": "Low-E",
                                            "node_type": "option",
                                            "price_impact_value": Decimal("40.00"),
                                        },
                                        {
                                            "name": "UV Protection",
                                            "node_type": "option",
                                            "price_impact_value": Decimal("50.00"),
                                        },
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        await service.create_hierarchy_from_dict(
            manufacturing_type_id=mfg_type.id,
            hierarchy_data=complex_hierarchy,
        )

        # Show complete tree
        complete_tree = await service.asciify(manufacturing_type_id=mfg_type.id)
        print(complete_tree)
        print("=" * 60)

        print("\n✓ ASCII tree visualization demo complete!")
        print("\nKey Features Demonstrated:")
        print("  • Box-drawing characters (├──, └──, │)")
        print("  • Node type indicators [category], [attribute], [option]")
        print("  • Price formatting [+$50.00]")
        print("  • Nested hierarchy visualization")
        print("  • Subtree visualization")
        print("  • Multiple branches at same level")

        break  # Exit after first session


if __name__ == "__main__":
    asyncio.run(main())
