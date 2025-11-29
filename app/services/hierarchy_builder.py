"""HierarchyBuilderService for programmatic hierarchy management.

This module provides the service for creating and managing hierarchical
attribute data with automatic LTREE path calculation.

Public Classes:
    NodeParams: Base dataclass for node parameters
    HierarchyBuilderService: Service for hierarchy management

Features:
    - Automatic LTREE path calculation
    - Automatic depth calculation
    - Manufacturing type creation
    - Node creation with validation
    - Batch hierarchy creation from dictionaries
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_node import AttributeNode
from app.models.manufacturing_type import ManufacturingType
from app.repositories.attribute_node import AttributeNodeRepository
from app.repositories.manufacturing_type import ManufacturingTypeRepository
from app.schemas.attribute_node import AttributeNodeCreate, AttributeNodeTree
from app.schemas.manufacturing_type import ManufacturingTypeCreate
from app.services.base import BaseService

__all__ = ["NodeParams", "HierarchyBuilderService"]


@dataclass
class NodeParams:
    """Base dataclass for common node parameters.
    
    This dataclass consolidates common parameters used across node creation
    functions to reduce duplication and ensure consistency.
    
    Attributes:
        manufacturing_type_id: Manufacturing type ID
        name: Node display name
        node_type: Type of node (category, attribute, option, etc.)
        parent_node_id: Optional parent node ID
        data_type: Optional data type for the node
        display_condition: Optional conditional display logic
        validation_rules: Optional validation rules
        required: Whether the node is required
        price_impact_type: How the node affects price
        price_impact_value: Fixed price adjustment amount
        price_formula: Dynamic price calculation formula
        weight_impact: Fixed weight addition
        weight_formula: Dynamic weight calculation formula
        technical_property_type: Type of technical property
        technical_impact_formula: Technical calculation formula
        sort_order: Display order among siblings
        ui_component: UI control type
        description: Help text for users
        help_text: Additional guidance
    """

    manufacturing_type_id: int
    name: str
    node_type: str
    parent_node_id: int | None = None
    data_type: str | None = None
    display_condition: dict | None = None
    validation_rules: dict | None = None
    required: bool = False
    price_impact_type: str = "fixed"
    price_impact_value: Decimal | None = None
    price_formula: str | None = None
    weight_impact: Decimal = Decimal("0")
    weight_formula: str | None = None
    technical_property_type: str | None = None
    technical_impact_formula: str | None = None
    sort_order: int = 0
    ui_component: str | None = None
    description: str | None = None
    help_text: str | None = None


class HierarchyBuilderService(BaseService):
    """Service for building and managing attribute hierarchies.
    
    This service provides high-level methods for creating manufacturing types
    and attribute nodes with automatic LTREE path and depth calculation.
    
    Attributes:
        db: Database session
        mfg_type_repo: ManufacturingTypeRepository instance
        attr_node_repo: AttributeNodeRepository instance
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize HierarchyBuilderService.
        
        Args:
            db (AsyncSession): Database session
        """
        super().__init__(db)
        self.mfg_type_repo = ManufacturingTypeRepository(db)
        self.attr_node_repo = AttributeNodeRepository(db)

    def _sanitize_for_ltree(self, name: str) -> str:
        """Sanitize input string for LTREE path compatibility.
        
        Performs comprehensive sanitization to ensure the name is valid for
        PostgreSQL LTREE paths. Handles all common edge cases including:
        - Unicode characters (accents, diacritics)
        - Special characters and symbols
        - Multiple consecutive spaces/underscores
        - Leading/trailing whitespace
        - Empty or whitespace-only strings
        - Names starting with numbers
        - Very long names (LTREE label limit: 256 chars)
        
        Args:
            name: Raw input string to sanitize
            
        Returns:
            str: Sanitized string safe for LTREE paths
            
        Raises:
            ValueError: If name is empty or becomes empty after sanitization
            
        Example:
            >>> service._sanitize_for_ltree("Frame Material")
            'frame_material'
            
            >>> service._sanitize_for_ltree("Aluminum & Steel (Premium)")
            'aluminum_and_steel_premium'
            
            >>> service._sanitize_for_ltree("  Multiple   Spaces  ")
            'multiple_spaces'
            
            >>> service._sanitize_for_ltree("Café-Style Door™")
            'cafe_style_door'
            
            >>> service._sanitize_for_ltree("100% Pure")
            'n_100_percent_pure'
            
            >>> service._sanitize_for_ltree("Price: $50-$100")
            'price_dollar_50_dollar_100'
        """
        import re
        import unicodedata
        
        # Validate input
        if not name or not name.strip():
            raise ValueError("Node name cannot be empty or whitespace-only")
        
        # Step 1: Normalize unicode characters (remove accents, etc.)
        # NFD = Canonical Decomposition, then filter out combining characters
        normalized = unicodedata.normalize('NFD', name)
        ascii_name = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'  # Mn = Mark, Nonspacing
        )
        
        # Step 2: Convert to lowercase
        sanitized = ascii_name.lower()
        
        # Step 3: Replace common symbols with words
        replacements = {
            '&': 'and',
            '+': 'plus',
            '%': 'percent',
            '@': 'at',
            '#': 'number',
            '$': 'dollar',
            '€': 'euro',
            '£': 'pound',
            '¥': 'yen',
            '°': 'degree',
            '™': '',
            '®': '',
            '©': '',
            '×': 'x',
            '÷': 'div',
            '=': 'equals',
            '<': 'lt',
            '>': 'gt',
        }
        
        for symbol, replacement in replacements.items():
            if replacement:
                sanitized = sanitized.replace(symbol, f'_{replacement}_')
            else:
                sanitized = sanitized.replace(symbol, '_')
        
        # Step 4: Replace common separators with underscores
        separators = [' ', '-', '/', '\\', '|', '.', ',', ';', ':', '~', '`']
        for sep in separators:
            sanitized = sanitized.replace(sep, '_')
        
        # Step 5: Remove parentheses, brackets, quotes (but keep content)
        sanitized = re.sub(r'[(){}\[\]"\']', '_', sanitized)
        
        # Step 6: Remove any remaining non-alphanumeric characters except underscore
        sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
        
        # Step 7: Replace multiple consecutive underscores with single underscore
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Step 8: Strip leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Step 9: Validate result is not empty
        if not sanitized:
            raise ValueError(
                f"Node name '{name}' becomes empty after sanitization. "
                "Please provide a name with at least one alphanumeric character."
            )
        
        # Step 10: Enforce LTREE label length limit (256 characters)
        if len(sanitized) > 256:
            # Truncate to 256 characters
            sanitized = sanitized[:256]
            # Remove trailing underscore if truncation created one
            sanitized = sanitized.rstrip('_')
        
        # Step 11: Ensure it doesn't start with a number (LTREE requirement)
        # This must be done AFTER truncation to ensure the final result is valid
        if sanitized and sanitized[0].isdigit():
            sanitized = f'n_{sanitized}'
            # If adding prefix makes it too long, truncate again
            if len(sanitized) > 256:
                sanitized = sanitized[:256].rstrip('_')
        
        return sanitized

    def _calculate_ltree_path(
        self, parent: AttributeNode | None, node_name: str
    ) -> str:
        """Calculate LTREE path for a new node.
        
        Sanitizes the node name using comprehensive sanitization and constructs
        the LTREE path based on whether the node is a root node or a child node.
        
        Args:
            parent: Parent node (None for root nodes)
            node_name: Display name of the node
            
        Returns:
            str: Sanitized LTREE path
            
        Raises:
            ValueError: If node_name is invalid or becomes empty after sanitization
            
        Example:
            >>> # Root node
            >>> service._calculate_ltree_path(None, "Frame Material")
            'frame_material'
            
            >>> # Child node with parent path "frame_material"
            >>> service._calculate_ltree_path(parent, "Aluminum & Steel")
            'frame_material.aluminum_and_steel'
            
            >>> # Complex name with special characters
            >>> service._calculate_ltree_path(None, "100% Café-Style™")
            'n_100_percent_cafe_style'
        """
        # Use robust sanitization function
        sanitized_name = self._sanitize_for_ltree(node_name)
        
        if parent is None:
            # Root node - return just the sanitized name
            return sanitized_name
        else:
            # Child node - append to parent's path
            return f"{parent.ltree_path}.{sanitized_name}"


    def _calculate_depth(self, parent: AttributeNode | None) -> int:
        """Calculate depth level for a new node.
        
        Determines the nesting level of a node in the hierarchy based on
        its parent's depth.
        
        Args:
            parent: Parent node (None for root nodes)
            
        Returns:
            int: Depth level (0 for root nodes, parent.depth + 1 for children)
            
        Example:
            >>> # Root node
            >>> service._calculate_depth(None)
            0
            
            >>> # Child of root node (depth=0)
            >>> service._calculate_depth(root_node)
            1
            
            >>> # Grandchild (parent depth=1)
            >>> service._calculate_depth(child_node)
            2
        """
        if parent is None:
            # Root node - depth is 0
            return 0
        else:
            # Child node - depth is parent's depth + 1
            return parent.depth + 1


    async def create_manufacturing_type(
        self,
        name: str,
        description: str | None = None,
        base_category: str | None = None,
        base_price: Decimal = Decimal("0"),
        base_weight: Decimal = Decimal("0"),
    ) -> ManufacturingType:
        """Create a new manufacturing type.
        
        Creates a manufacturing type that serves as the root for an
        attribute hierarchy.
        
        Args:
            name: Unique manufacturing type name
            description: Optional detailed description
            base_category: Optional high-level category (e.g., "window", "door")
            base_price: Starting price (default: 0)
            base_weight: Base weight in kg (default: 0)
            
        Returns:
            ManufacturingType: Created manufacturing type instance
            
        Raises:
            ConflictException: If name already exists
            DatabaseException: If creation fails
            
        Example:
            >>> mfg_type = await service.create_manufacturing_type(
            ...     name="Casement Window",
            ...     description="Energy-efficient casement windows",
            ...     base_category="window",
            ...     base_price=Decimal("200.00"),
            ...     base_weight=Decimal("15.00")
            ... )
        """
        # Create schema for validation
        mfg_type_data = ManufacturingTypeCreate(
            name=name,
            description=description,
            base_category=base_category,
            base_price=base_price,
            base_weight=base_weight,
        )
        
        # Use repository to create
        mfg_type = await self.mfg_type_repo.create(mfg_type_data)
        await self.commit()
        await self.refresh(mfg_type)
        
        return mfg_type


    async def create_node(
        self,
        manufacturing_type_id: int,
        name: str,
        node_type: str,
        parent_node_id: int | None = None,
        data_type: str | None = None,
        display_condition: dict | None = None,
        validation_rules: dict | None = None,
        required: bool = False,
        price_impact_type: str = "fixed",
        price_impact_value: Decimal | None = None,
        price_formula: str | None = None,
        weight_impact: Decimal = Decimal("0"),
        weight_formula: str | None = None,
        technical_property_type: str | None = None,
        technical_impact_formula: str | None = None,
        sort_order: int = 0,
        ui_component: str | None = None,
        description: str | None = None,
        help_text: str | None = None,
    ) -> AttributeNode:
        """Create a single attribute node with automatic path/depth calculation.
        
        Creates an attribute node and automatically calculates its LTREE path
        and depth based on its parent node. Performs comprehensive input validation
        and sanitization.
        
        Args:
            manufacturing_type_id: Manufacturing type ID (must be > 0)
            name: Node display name (cannot be empty)
            node_type: Type of node (category, attribute, option, component, technical_spec)
            parent_node_id: Optional parent node ID (None for root nodes)
            data_type: Optional data type (string, number, boolean, formula, dimension, selection)
            display_condition: Optional conditional display logic (JSONB)
            validation_rules: Optional validation rules (JSONB)
            required: Whether this attribute must be selected
            price_impact_type: How it affects price (fixed, percentage, formula)
            price_impact_value: Fixed price adjustment amount (must be >= 0 if provided)
            price_formula: Dynamic price calculation formula
            weight_impact: Fixed weight addition in kg (must be >= 0)
            weight_formula: Dynamic weight calculation formula
            technical_property_type: Type of technical property
            technical_impact_formula: Technical calculation formula
            sort_order: Display order among siblings
            ui_component: UI control type
            description: Help text for users
            help_text: Additional guidance
            
        Returns:
            AttributeNode: Created attribute node with calculated path and depth
            
        Raises:
            ValueError: If input validation fails
            NotFoundException: If parent node or manufacturing type not found
            DatabaseException: If creation fails
            
        Example:
            >>> # Create root node
            >>> root = await service.create_node(
            ...     manufacturing_type_id=1,
            ...     name="Frame Material",
            ...     node_type="category"
            ... )
            >>> # root.ltree_path == "frame_material"
            >>> # root.depth == 0
            
            >>> # Create child node
            >>> child = await service.create_node(
            ...     manufacturing_type_id=1,
            ...     name="Aluminum",
            ...     node_type="option",
            ...     parent_node_id=root.id,
            ...     price_impact_value=Decimal("50.00")
            ... )
            >>> # child.ltree_path == "frame_material.aluminum"
            >>> # child.depth == 1
        """
        from app.core.exceptions import NotFoundException
        
        # Input validation
        if manufacturing_type_id <= 0:
            raise ValueError("manufacturing_type_id must be greater than 0")
        
        if not name or not name.strip():
            raise ValueError("Node name cannot be empty or whitespace-only")
        
        if len(name) > 200:
            raise ValueError("Node name cannot exceed 200 characters")
        
        # Validate node_type
        from app.core.exceptions import ValidationException
        
        valid_node_types = {"category", "attribute", "option", "component", "technical_spec"}
        if node_type not in valid_node_types:
            raise ValidationException(
                f"Invalid node_type '{node_type}'. Must be one of: {', '.join(valid_node_types)}"
            )
        
        # Validate data_type if provided
        if data_type is not None:
            valid_data_types = {"string", "number", "boolean", "formula", "dimension", "selection"}
            if data_type not in valid_data_types:
                raise ValueError(
                    f"Invalid data_type '{data_type}'. Must be one of: {', '.join(valid_data_types)}"
                )
        
        # Validate price_impact_type
        valid_price_types = {"fixed", "percentage", "formula"}
        if price_impact_type not in valid_price_types:
            raise ValueError(
                f"Invalid price_impact_type '{price_impact_type}'. Must be one of: {', '.join(valid_price_types)}"
            )
        
        # Validate price_impact_value if provided
        if price_impact_value is not None and price_impact_value < 0:
            raise ValueError("price_impact_value cannot be negative")
        
        # Validate weight_impact
        if weight_impact < 0:
            raise ValueError("weight_impact cannot be negative")
        
        # Validate sort_order
        if sort_order < 0:
            raise ValueError("sort_order cannot be negative")
        
        # Validate manufacturing type exists
        mfg_type = await self.mfg_type_repo.get(manufacturing_type_id)
        if mfg_type is None:
            raise NotFoundException(
                f"Manufacturing type with id {manufacturing_type_id} not found"
            )
        
        # Fetch parent node if parent_node_id is provided
        parent: AttributeNode | None = None
        if parent_node_id is not None:
            if parent_node_id <= 0:
                raise ValueError("parent_node_id must be greater than 0")
            
            parent = await self.attr_node_repo.get(parent_node_id)
            if parent is None:
                raise NotFoundException(f"Parent node with id {parent_node_id} not found")
            
            # Validate parent belongs to same manufacturing type
            if parent.manufacturing_type_id != manufacturing_type_id:
                raise ValueError(
                    f"Parent node belongs to manufacturing type {parent.manufacturing_type_id}, "
                    f"but node is being created for manufacturing type {manufacturing_type_id}"
                )
            
            # Note: Circular reference detection is not needed for new node creation
            # since a new node cannot be its own ancestor. This validation is only
            # needed when moving existing nodes (see move_node method).
        
        # Calculate ltree_path using helper method
        ltree_path = self._calculate_ltree_path(parent, name)
        
        # Calculate depth using helper method
        depth = self._calculate_depth(parent)
        
        # Check for duplicate names at the same level (same parent)
        from app.core.exceptions import ConflictException
        from sqlalchemy import select
        
        # Query for siblings with the same name
        siblings_query = select(AttributeNode).where(
            AttributeNode.manufacturing_type_id == manufacturing_type_id,
            AttributeNode.parent_node_id == parent_node_id,
            AttributeNode.name == name,
        )
        result = await self.attr_node_repo.db.execute(siblings_query)
        existing_sibling = result.scalar_one_or_none()
        
        if existing_sibling is not None:
            parent_desc = f"parent node {parent_node_id}" if parent_node_id else "root level"
            raise ConflictException(
                f"A node with name '{name}' already exists at {parent_desc} "
                f"in manufacturing type {manufacturing_type_id}"
            )
        
        # Create AttributeNodeCreate schema with calculated fields
        # We need to create the model directly because we're adding computed fields
        from app.models.attribute_node import AttributeNode as AttributeNodeModel
        
        node = AttributeNodeModel(
            manufacturing_type_id=manufacturing_type_id,
            parent_node_id=parent_node_id,
            name=name,
            node_type=node_type,
            data_type=data_type,
            display_condition=display_condition,
            validation_rules=validation_rules,
            required=required,
            price_impact_type=price_impact_type,
            price_impact_value=price_impact_value,
            price_formula=price_formula,
            weight_impact=weight_impact,
            weight_formula=weight_formula,
            technical_property_type=technical_property_type,
            technical_impact_formula=technical_impact_formula,
            ltree_path=ltree_path,  # Calculated field
            depth=depth,  # Calculated field
            sort_order=sort_order,
            ui_component=ui_component,
            description=description,
            help_text=help_text,
        )
        
        # Add to session and commit
        self.attr_node_repo.db.add(node)
        await self.commit()
        await self.refresh(node)
        
        return node

    async def move_node(
        self,
        node_id: int,
        new_parent_id: int | None,
    ) -> AttributeNode:
        """Move a node to a new parent in the hierarchy.
        
        Moves an existing attribute node to a new parent, recalculating
        its LTREE path and depth. Validates that the move would not create
        a circular reference.
        
        Args:
            node_id: ID of the node to move
            new_parent_id: ID of the new parent (None for root level)
            
        Returns:
            AttributeNode: Updated node with new path and depth
            
        Raises:
            NotFoundException: If node or new parent not found
            ValidationException: If move would create circular reference
            ValueError: If new parent is in different manufacturing type
            
        Example:
            >>> # Move node 5 to be a child of node 10
            >>> moved_node = await service.move_node(5, 10)
            
            >>> # Move node 5 to root level
            >>> moved_node = await service.move_node(5, None)
        """
        from app.core.exceptions import NotFoundException, ValidationException
        
        # Validate node exists
        node = await self.attr_node_repo.get(node_id)
        if node is None:
            raise NotFoundException(f"Node with id {node_id} not found")
        
        # If new_parent_id is provided, validate it
        new_parent: AttributeNode | None = None
        if new_parent_id is not None:
            if new_parent_id <= 0:
                raise ValueError("new_parent_id must be greater than 0")
            
            new_parent = await self.attr_node_repo.get(new_parent_id)
            if new_parent is None:
                raise NotFoundException(f"New parent node with id {new_parent_id} not found")
            
            # Validate new parent belongs to same manufacturing type
            if new_parent.manufacturing_type_id != node.manufacturing_type_id:
                raise ValueError(
                    f"Cannot move node to parent in different manufacturing type. "
                    f"Node is in type {node.manufacturing_type_id}, "
                    f"parent is in type {new_parent.manufacturing_type_id}"
                )
            
            # Check for circular reference
            would_cycle = await self.attr_node_repo.would_create_cycle(node_id, new_parent_id)
            if would_cycle:
                raise ValidationException(
                    f"Cannot move node {node_id} under node {new_parent_id}: "
                    "this would create a circular reference in the hierarchy"
                )
        
        # Calculate new ltree_path and depth
        new_ltree_path = self._calculate_ltree_path(new_parent, node.name)
        new_depth = self._calculate_depth(new_parent)
        
        # Update node
        node.parent_node_id = new_parent_id
        node.ltree_path = new_ltree_path
        node.depth = new_depth
        
        # Update all descendants' paths and depths
        descendants = await self.attr_node_repo.get_descendants(node_id)
        for descendant in descendants:
            # Calculate relative path from node to descendant
            old_node_path = node.ltree_path
            descendant_relative_path = descendant.ltree_path[len(old_node_path) + 1:]
            
            # Update descendant's path
            descendant.ltree_path = f"{new_ltree_path}.{descendant_relative_path}"
            
            # Update descendant's depth (add the depth change)
            depth_change = new_depth - node.depth
            descendant.depth = descendant.depth + depth_change
        
        await self.commit()
        await self.refresh(node)
        
        return node

    async def create_hierarchy_from_dict(
        self,
        manufacturing_type_id: int,
        hierarchy_data: dict,
        parent: AttributeNode | None = None,
        _is_root_call: bool = True,
    ) -> AttributeNode:
        """Create a hierarchy from nested dictionary structure.
        
        Creates an entire attribute hierarchy from a nested dictionary,
        recursively processing children. This enables batch creation of
        complex hierarchies with a single method call.
        
        The operation is transactional - either all nodes are created
        successfully, or none are created (all-or-nothing).
        
        Args:
            manufacturing_type_id: Manufacturing type ID
            hierarchy_data: Dictionary containing node data and optional children
            parent: Optional parent node (None for root level)
            _is_root_call: Internal flag to track root call (do not set manually)
            
        Returns:
            AttributeNode: The root node of the created hierarchy
            
        Raises:
            ValueError: If hierarchy_data is invalid or missing required fields
            NotFoundException: If manufacturing type or parent not found
            ConflictException: If duplicate names exist at same level
            DatabaseException: If creation fails (triggers rollback)
            
        Dictionary Structure:
            {
                "name": "Node Name",  # Required
                "node_type": "category",  # Required
                "data_type": "string",  # Optional
                "price_impact_value": 50.00,  # Optional
                "weight_impact": 2.0,  # Optional
                "description": "Description",  # Optional
                # ... any other node fields ...
                "children": [  # Optional - list of child dictionaries
                    {
                        "name": "Child Node",
                        "node_type": "option",
                        # ... child fields ...
                        "children": [...]  # Nested children
                    }
                ]
            }
            
        Example:
            >>> hierarchy = {
            ...     "name": "Frame Material",
            ...     "node_type": "category",
            ...     "children": [
            ...         {
            ...             "name": "Material Type",
            ...             "node_type": "attribute",
            ...             "data_type": "selection",
            ...             "children": [
            ...                 {
            ...                     "name": "Aluminum",
            ...                     "node_type": "option",
            ...                     "price_impact_value": 50.00,
            ...                     "weight_impact": 2.0
            ...                 },
            ...                 {
            ...                     "name": "Vinyl",
            ...                     "node_type": "option",
            ...                     "price_impact_value": 30.00,
            ...                     "weight_impact": 1.5
            ...                 }
            ...             ]
            ...         }
            ...     ]
            ... }
            >>> 
            >>> root = await service.create_hierarchy_from_dict(
            ...     manufacturing_type_id=1,
            ...     hierarchy_data=hierarchy
            ... )
            >>> # Creates: Frame Material → Material Type → [Aluminum, Vinyl]
        """
        from app.core.exceptions import DatabaseException, NotFoundException, ValidationException, ConflictException
        
        # Validate hierarchy_data is a dictionary
        if not isinstance(hierarchy_data, dict):
            raise ValueError(
                f"hierarchy_data must be a dictionary, got {type(hierarchy_data).__name__}"
            )
        
        # Validate required fields
        if "name" not in hierarchy_data:
            raise ValueError("hierarchy_data must contain 'name' field")
        
        if "node_type" not in hierarchy_data:
            raise ValueError("hierarchy_data must contain 'node_type' field")
        
        # Make a copy to avoid modifying the original dict
        hierarchy_data = hierarchy_data.copy()
        
        # Extract children before creating node (we'll process them after)
        children_data = hierarchy_data.pop("children", [])
        
        # Validate children is a list if provided
        if children_data is not None and not isinstance(children_data, list):
            raise ValueError(
                f"'children' must be a list, got {type(children_data).__name__}"
            )
        
        try:
            # Extract node data from dictionary
            node_data = {
                "manufacturing_type_id": manufacturing_type_id,
                "parent_node_id": parent.id if parent else None,
                **hierarchy_data  # Spread all other fields from dict
            }
            
            # Convert Decimal fields if they're provided as strings or floats
            if "price_impact_value" in node_data and node_data["price_impact_value"] is not None:
                node_data["price_impact_value"] = Decimal(str(node_data["price_impact_value"]))
            
            if "weight_impact" in node_data and node_data["weight_impact"] is not None:
                node_data["weight_impact"] = Decimal(str(node_data["weight_impact"]))
            
            # Create the node - but don't commit yet if we're in a batch operation
            # We'll commit at the end of the root call
            from app.models.attribute_node import AttributeNode as AttributeNodeModel
            from sqlalchemy import select
            
            # Perform all the same validations as create_node
            name = node_data["name"]
            node_type = node_data["node_type"]
            
            # Validate manufacturing type exists
            mfg_type = await self.mfg_type_repo.get(manufacturing_type_id)
            if mfg_type is None:
                raise NotFoundException(
                    f"Manufacturing type with id {manufacturing_type_id} not found"
                )
            
            # Validate node_type
            valid_node_types = {"category", "attribute", "option", "component", "technical_spec"}
            if node_type not in valid_node_types:
                raise ValidationException(
                    f"Invalid node_type '{node_type}'. Must be one of: {', '.join(valid_node_types)}"
                )
            
            # Check for duplicate names at the same level
            siblings_query = select(AttributeNodeModel).where(
                AttributeNodeModel.manufacturing_type_id == manufacturing_type_id,
                AttributeNodeModel.parent_node_id == (parent.id if parent else None),
                AttributeNodeModel.name == name,
            )
            result = await self.attr_node_repo.db.execute(siblings_query)
            existing_sibling = result.scalar_one_or_none()
            
            if existing_sibling is not None:
                parent_desc = f"parent node {parent.id if parent else None}" if parent else "root level"
                raise ConflictException(
                    f"A node with name '{name}' already exists at {parent_desc} "
                    f"in manufacturing type {manufacturing_type_id}"
                )
            
            # Calculate ltree_path and depth
            ltree_path = self._calculate_ltree_path(parent, name)
            depth = self._calculate_depth(parent)
            
            # Create the node model
            node = AttributeNodeModel(
                ltree_path=ltree_path,
                depth=depth,
                **node_data
            )
            
            # Add to session but don't commit yet
            self.attr_node_repo.db.add(node)
            await self.attr_node_repo.db.flush()  # Flush to get the ID
            
            # Recursively process children
            if children_data:
                for child_data in children_data:
                    # Validate each child is a dictionary
                    if not isinstance(child_data, dict):
                        raise ValueError(
                            f"Each child must be a dictionary, got {type(child_data).__name__} "
                            f"for child of node '{node.name}'"
                        )
                    
                    # Recursively create child hierarchy (not a root call)
                    await self.create_hierarchy_from_dict(
                        manufacturing_type_id=manufacturing_type_id,
                        hierarchy_data=child_data,
                        parent=node,
                        _is_root_call=False,
                    )
            
            # Only commit if this is the root call
            if _is_root_call:
                await self.commit()
                await self.refresh(node)
            
            return node
            
        except Exception as e:
            # Only rollback if this is the root call
            if _is_root_call:
                await self.rollback()
            
            # Re-raise with additional context about which node failed
            node_name = hierarchy_data.get("name", "<unknown>")
            parent_name = parent.name if parent else "<root>"
            
            # For validation errors, preserve the original exception type
            if isinstance(e, (NotFoundException, ValidationException, ConflictException, ValueError)):
                raise
            
            raise DatabaseException(
                f"Failed to create node '{node_name}' under parent '{parent_name}': {str(e)}"
            ) from e

    async def pydantify(
        self,
        manufacturing_type_id: int,
        root_node_id: int | None = None,
    ) -> list[AttributeNodeTree]:
        """Get hierarchy as Pydantic models (serializable to JSON).
        
        Retrieves the attribute tree for a manufacturing type and converts
        it to a nested Pydantic structure suitable for JSON serialization
        and tree visualization.
        
        Args:
            manufacturing_type_id: Manufacturing type ID
            root_node_id: Optional root node ID to get subtree only
            
        Returns:
            list[AttributeNodeTree]: List of root nodes with nested children
            
        Raises:
            NotFoundException: If manufacturing type or root node not found
            
        Example:
            >>> # Get full tree for manufacturing type
            >>> tree = await service.pydantify(manufacturing_type_id=1)
            >>> 
            >>> # Get subtree starting from specific node
            >>> subtree = await service.pydantify(
            ...     manufacturing_type_id=1,
            ...     root_node_id=42
            ... )
            >>> 
            >>> # Serialize to JSON
            >>> import json
            >>> tree_json = json.dumps([node.model_dump() for node in tree], indent=2)
        """
        from app.core.exceptions import NotFoundException
        from app.schemas.attribute_node import AttributeNodeTree
        
        # Validate manufacturing type exists
        mfg_type = await self.mfg_type_repo.get(manufacturing_type_id)
        if mfg_type is None:
            raise NotFoundException(
                f"Manufacturing type with id {manufacturing_type_id} not found"
            )
        
        # If root_node_id is provided, validate it exists and build subtree
        if root_node_id is not None:
            root_node = await self.attr_node_repo.get(root_node_id)
            if root_node is None:
                raise NotFoundException(f"Root node with id {root_node_id} not found")
            
            # Validate root node belongs to the manufacturing type
            if root_node.manufacturing_type_id != manufacturing_type_id:
                raise ValueError(
                    f"Root node {root_node_id} belongs to manufacturing type "
                    f"{root_node.manufacturing_type_id}, not {manufacturing_type_id}"
                )
            
            # Get all descendants of the root node
            descendants = await self.attr_node_repo.get_descendants(root_node_id)
            # Include the root node itself at the beginning
            nodes = [root_node] + descendants
            
            # For subtree, we need to build the tree treating the specified node as root
            # Create a mapping of node_id to node with children list
            node_map: dict[int, AttributeNodeTree] = {}
            
            for node in nodes:
                node_tree = AttributeNodeTree(
                    id=node.id,
                    manufacturing_type_id=node.manufacturing_type_id,
                    parent_node_id=node.parent_node_id,
                    name=node.name,
                    node_type=node.node_type,
                    data_type=node.data_type,
                    display_condition=node.display_condition,
                    validation_rules=node.validation_rules,
                    required=node.required,
                    price_impact_type=node.price_impact_type,
                    price_impact_value=node.price_impact_value,
                    price_formula=node.price_formula,
                    weight_impact=node.weight_impact,
                    weight_formula=node.weight_formula,
                    technical_property_type=node.technical_property_type,
                    technical_impact_formula=node.technical_impact_formula,
                    ltree_path=node.ltree_path,
                    depth=node.depth,
                    sort_order=node.sort_order,
                    ui_component=node.ui_component,
                    description=node.description,
                    help_text=node.help_text,
                    created_at=node.created_at,
                    updated_at=node.updated_at,
                    children=[],
                )
                node_map[node.id] = node_tree
            
            # Build tree by linking children to parents
            # The root of the subtree is the specified root_node_id
            for node in nodes:
                if node.id == root_node_id:
                    # This is the root of our subtree
                    continue
                    
                node_tree = node_map[node.id]
                
                # Add to parent's children if parent is in our subtree
                if node.parent_node_id in node_map:
                    parent = node_map[node.parent_node_id]
                    parent.children.append(node_tree)
            
            # Return the root node as a single-item list
            return [node_map[root_node_id]]
        else:
            # Get all nodes for the manufacturing type
            nodes = await self.attr_node_repo.get_by_manufacturing_type(
                manufacturing_type_id
            )
            
            # Build tree structure using repository method
            tree = self.attr_node_repo.build_tree(nodes)
            
            return tree
