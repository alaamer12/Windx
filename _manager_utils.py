"""Manager utility functions for sample data management.

This module provides functions to create and delete sample manufacturing data
with hierarchical attribute nodes for testing and demonstration purposes.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_node import AttributeNode
from app.models.manufacturing_type import ManufacturingType


async def create_sample_manufacturing_data(db: AsyncSession) -> dict[str, Any]:
    """Create sample manufacturing type with hierarchical attribute nodes.
    
    Creates a complete example of a window product with:
    - Manufacturing type (Casement Window)
    - Hierarchical attribute tree with categories, attributes, and options
    - Multiple levels of depth
    - Different node types and pricing impacts
    
    Args:
        db: Database session
        
    Returns:
        dict: Created data summary with IDs and counts
    """
    # Create manufacturing type
    mfg_type = ManufacturingType(
        name="Sample Casement Window",
        description="Energy-efficient casement window with customizable options",
        base_category="window",
        image_url="/images/sample-casement.jpg",
        base_price=Decimal("250.00"),
        base_weight=Decimal("18.00"),
        is_active=True,
    )
    db.add(mfg_type)
    await db.flush()  # Get the ID
    
    created_nodes = []
    
    # Level 0: Root categories
    frame_category = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=None,
        name="Frame Options",
        node_type="category",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="frame_options",
        depth=0,
        sort_order=1,
        ui_component="section",
        description="Customize your window frame",
    )
    db.add(frame_category)
    await db.flush()
    created_nodes.append(frame_category)
    
    glass_category = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=None,
        name="Glass Options",
        node_type="category",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="glass_options",
        depth=0,
        sort_order=2,
        ui_component="section",
        description="Choose your glass configuration",
    )
    db.add(glass_category)
    await db.flush()
    created_nodes.append(glass_category)
    
    # Level 1: Frame attributes
    material_attr = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=frame_category.id,
        name="Frame Material",
        node_type="attribute",
        data_type="selection",
        required=True,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="frame_options.material",
        depth=1,
        sort_order=1,
        ui_component="radio",
        description="Select frame material",
        help_text="Different materials offer different benefits",
    )
    db.add(material_attr)
    await db.flush()
    created_nodes.append(material_attr)
    
    color_attr = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=frame_category.id,
        name="Frame Color",
        node_type="attribute",
        data_type="selection",
        required=True,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="frame_options.color",
        depth=1,
        sort_order=2,
        ui_component="dropdown",
        description="Select frame color",
    )
    db.add(color_attr)
    await db.flush()
    created_nodes.append(color_attr)
    
    # Level 2: Material options
    aluminum_option = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=material_attr.id,
        name="Aluminum",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("50.00"),
        weight_impact=Decimal("2.50"),
        ltree_path="frame_options.material.aluminum",
        depth=2,
        sort_order=1,
        ui_component="radio",
        description="Durable aluminum frame",
        help_text="Best for coastal areas, corrosion resistant",
    )
    db.add(aluminum_option)
    created_nodes.append(aluminum_option)
    
    vinyl_option = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=material_attr.id,
        name="Vinyl",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("30.00"),
        weight_impact=Decimal("1.80"),
        ltree_path="frame_options.material.vinyl",
        depth=2,
        sort_order=2,
        ui_component="radio",
        description="Low-maintenance vinyl frame",
        help_text="Energy efficient and affordable",
    )
    db.add(vinyl_option)
    created_nodes.append(vinyl_option)
    
    wood_option = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=material_attr.id,
        name="Wood",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("120.00"),
        weight_impact=Decimal("3.50"),
        ltree_path="frame_options.material.wood",
        depth=2,
        sort_order=3,
        ui_component="radio",
        description="Premium wood frame",
        help_text="Classic look with natural insulation",
    )
    db.add(wood_option)
    created_nodes.append(wood_option)
    
    # Level 2: Color options
    white_color = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=color_attr.id,
        name="White",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="frame_options.color.white",
        depth=2,
        sort_order=1,
        ui_component="color",
        description="Classic white finish",
    )
    db.add(white_color)
    created_nodes.append(white_color)
    
    bronze_color = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=color_attr.id,
        name="Bronze",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("25.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="frame_options.color.bronze",
        depth=2,
        sort_order=2,
        ui_component="color",
        description="Bronze finish",
    )
    db.add(bronze_color)
    created_nodes.append(bronze_color)
    
    # Level 1: Glass attributes
    pane_attr = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=glass_category.id,
        name="Pane Configuration",
        node_type="attribute",
        data_type="selection",
        required=True,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="glass_options.pane_config",
        depth=1,
        sort_order=1,
        ui_component="radio",
        description="Number of glass panes",
        help_text="More panes provide better insulation",
    )
    db.add(pane_attr)
    await db.flush()
    created_nodes.append(pane_attr)
    
    coating_attr = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=glass_category.id,
        name="Glass Coating",
        node_type="attribute",
        data_type="selection",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="glass_options.coating",
        depth=1,
        sort_order=2,
        ui_component="checkbox",
        description="Optional glass coatings",
    )
    db.add(coating_attr)
    await db.flush()
    created_nodes.append(coating_attr)
    
    # Level 2: Pane options
    single_pane = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=pane_attr.id,
        name="Single Pane",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("0.00"),
        weight_impact=Decimal("3.00"),
        ltree_path="glass_options.pane_config.single",
        depth=2,
        sort_order=1,
        ui_component="radio",
        description="Single pane glass",
        help_text="Basic option, less insulation",
    )
    db.add(single_pane)
    created_nodes.append(single_pane)
    
    double_pane = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=pane_attr.id,
        name="Double Pane",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("80.00"),
        weight_impact=Decimal("5.50"),
        ltree_path="glass_options.pane_config.double",
        depth=2,
        sort_order=2,
        ui_component="radio",
        description="Double pane insulated glass",
        help_text="Good energy efficiency",
    )
    db.add(double_pane)
    created_nodes.append(double_pane)
    
    triple_pane = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=pane_attr.id,
        name="Triple Pane",
        node_type="option",
        data_type="string",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("180.00"),
        weight_impact=Decimal("8.00"),
        ltree_path="glass_options.pane_config.triple",
        depth=2,
        sort_order=3,
        ui_component="radio",
        description="Triple pane maximum insulation",
        help_text="Best energy efficiency, quieter",
    )
    db.add(triple_pane)
    created_nodes.append(triple_pane)
    
    # Level 2: Coating options
    low_e_coating = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=coating_attr.id,
        name="Low-E Coating",
        node_type="option",
        data_type="boolean",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("45.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="glass_options.coating.low_e",
        depth=2,
        sort_order=1,
        ui_component="checkbox",
        description="Low-emissivity coating",
        help_text="Reflects heat, improves energy efficiency",
    )
    db.add(low_e_coating)
    created_nodes.append(low_e_coating)
    
    uv_protection = AttributeNode(
        manufacturing_type_id=mfg_type.id,
        parent_node_id=coating_attr.id,
        name="UV Protection",
        node_type="option",
        data_type="boolean",
        required=False,
        price_impact_type="fixed",
        price_impact_value=Decimal("35.00"),
        weight_impact=Decimal("0.00"),
        ltree_path="glass_options.coating.uv_protection",
        depth=2,
        sort_order=2,
        ui_component="checkbox",
        description="UV protection coating",
        help_text="Protects furniture from fading",
    )
    db.add(uv_protection)
    created_nodes.append(uv_protection)
    
    await db.commit()
    
    return {
        "manufacturing_type_id": mfg_type.id,
        "manufacturing_type_name": mfg_type.name,
        "total_nodes": len(created_nodes),
        "nodes_by_depth": {
            0: len([n for n in created_nodes if n.depth == 0]),
            1: len([n for n in created_nodes if n.depth == 1]),
            2: len([n for n in created_nodes if n.depth == 2]),
        },
        "nodes_by_type": {
            "category": len([n for n in created_nodes if n.node_type == "category"]),
            "attribute": len([n for n in created_nodes if n.node_type == "attribute"]),
            "option": len([n for n in created_nodes if n.node_type == "option"]),
        },
    }


async def delete_sample_manufacturing_data(db: AsyncSession) -> dict[str, Any]:
    """Delete sample manufacturing data created by create_sample_manufacturing_data.
    
    Deletes the "Sample Casement Window" manufacturing type and all its
    associated attribute nodes (cascade delete).
    
    Args:
        db: Database session
        
    Returns:
        dict: Deletion summary with counts
    """
    # Find the sample manufacturing type
    result = await db.execute(
        select(ManufacturingType).where(
            ManufacturingType.name == "Sample Casement Window"
        )
    )
    mfg_type = result.scalar_one_or_none()
    
    if not mfg_type:
        return {
            "deleted": False,
            "message": "Sample manufacturing type not found",
            "manufacturing_type_id": None,
            "deleted_nodes": 0,
        }
    
    # Count nodes before deletion
    node_result = await db.execute(
        select(AttributeNode).where(
            AttributeNode.manufacturing_type_id == mfg_type.id
        )
    )
    nodes = node_result.scalars().all()
    node_count = len(nodes)
    
    # Delete the manufacturing type (cascade will delete nodes)
    await db.delete(mfg_type)
    await db.commit()
    
    return {
        "deleted": True,
        "message": "Sample manufacturing data deleted successfully",
        "manufacturing_type_id": mfg_type.id,
        "manufacturing_type_name": "Sample Casement Window",
        "deleted_nodes": node_count,
    }
