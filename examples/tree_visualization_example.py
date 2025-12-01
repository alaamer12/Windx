"""Example script demonstrating tree visualization functionality.

This script shows how to use the HierarchyBuilderService to create
hierarchical attribute data and generate graphical tree visualizations
using matplotlib.
"""

import asyncio
from decimal import Decimal

from app.database.connection import get_async_session
from app.services.hierarchy_builder import HierarchyBuilderService


async def main():
    """Demonstrate tree visualization functionality."""

    # Get database session
    async for session in get_async_session():
        service = HierarchyBuilderService(session)

        # Create manufacturing type
        print("Creating manufacturing type...")
        mfg_type = await service.create_manufacturing_type(
            name="Example Window",
            description="Example window for tree visualization",
            base_price=Decimal("200.00"),
            base_weight=Decimal("15.00"),
        )
        print(f"✓ Created manufacturing type: {mfg_type.name} (ID: {mfg_type.id})")

        # Create hierarchy using dictionary
        print("\nCreating attribute hierarchy...")
        hierarchy = {
            "name": "Frame Options",
            "node_type": "category",
            "children": [
                {
                    "name": "Material Type",
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
        print(f"✓ Created hierarchy with root node: {root.name} (ID: {root.id})")

        # Generate ASCII tree
        print("\n" + "=" * 60)
        print("ASCII Tree Visualization:")
        print("=" * 60)
        ascii_tree = await service.asciify(manufacturing_type_id=mfg_type.id)
        print(ascii_tree)

        # Generate graphical tree plot
        print("\n" + "=" * 60)
        print("Generating graphical tree plot...")
        print("=" * 60)

        try:
            fig = await service.plot_tree(manufacturing_type_id=mfg_type.id)

            # Save to file
            output_file = "hierarchy_tree.png"
            fig.savefig(output_file, dpi=300, bbox_inches="tight")
            print(f"✓ Tree plot saved to: {output_file}")

            # Clean up
            import matplotlib.pyplot as plt

            plt.close(fig)

        except ImportError as e:
            print(f"✗ Could not generate plot: {e}")
            print("  Install matplotlib with: pip install matplotlib networkx")

        # Get tree as JSON (Pydantic serialization)
        print("\n" + "=" * 60)
        print("JSON Tree Structure (first 500 chars):")
        print("=" * 60)
        tree = await service.pydantify(manufacturing_type_id=mfg_type.id)
        import json

        tree_json = json.dumps([node.model_dump() for node in tree], indent=2)
        print(tree_json[:500] + "...")

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)

        break  # Exit after first session


if __name__ == "__main__":
    asyncio.run(main())
