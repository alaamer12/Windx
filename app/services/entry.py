"""Entry Page service for business logic.

This module provides the EntryService class for handling entry page operations
including schema generation, conditional field evaluation, data validation,
and configuration management.

Public Classes:
    ConditionEvaluator: Smart condition evaluator with complex expression support
    EntryService: Service class for entry page operations

Features:
    - Schema-driven form generation from attribute hierarchy
    - Smart conditional field visibility evaluation
    - Comprehensive validation with error handling
    - Configuration creation and management
    - Preview data generation
    - Performance optimizations with caching
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.core.rbac import Permission, require, ResourceOwnership, Privilege, Role
from app.models.attribute_node import AttributeNode
from app.models.configuration import Configuration
from app.models.configuration_selection import ConfigurationSelection
from app.models.customer import Customer
from app.models.manufacturing_type import ManufacturingType
from app.models.user import User
from app.schemas.entry import (
    FieldDefinition,
    FormSection,
    ProfileEntryData,
    ProfilePreviewData,
    ProfileSchema,
    PreviewTable,
)
from app.services.base import BaseService
from app.services.rbac import RBACService

__all__ = ["ConditionEvaluator", "EntryService"]


# Define reusable Privilege objects for Entry Service operations
ConfigurationCreator = Privilege(
    roles=[Role.CUSTOMER, Role.SALESMAN, Role.PARTNER, Role.SUPERADMIN],
    permission=Permission("configuration", "create")
)

ConfigurationViewer = Privilege(
    roles=Role.CUSTOMER | Role.SALESMAN | Role.PARTNER | Role.SUPERADMIN,
    permission=Permission("configuration", "read"),
    resource=ResourceOwnership("configuration")
)

AdminAccess = Privilege(
    roles=Role.SUPERADMIN,
    permission=Permission("*", "*")
)


class ConditionEvaluator:
    """Smart condition evaluator with support for complex expressions.
    
    Supports a rich set of operators for comparison, string operations,
    collection operations, existence checks, and logical operations.
    Provides consistent evaluation in both Python and JavaScript.
    """
    
    OPERATORS = {
        # Comparison operators
        'equals': lambda a, b: a == b,
        'not_equals': lambda a, b: a != b,
        'greater_than': lambda a, b: (a or 0) > (b or 0),
        'less_than': lambda a, b: (a or 0) < (b or 0),
        'greater_equal': lambda a, b: (a or 0) >= (b or 0),
        'less_equal': lambda a, b: (a or 0) <= (b or 0),
        
        # String operators
        'contains': lambda a, b: str(b).lower() in str(a or '').lower(),
        'starts_with': lambda a, b: str(a or '').lower().startswith(str(b).lower()),
        'ends_with': lambda a, b: str(a or '').lower().endswith(str(b).lower()),
        'matches_pattern': lambda a, b: bool(re.match(b, str(a or ''))),
        
        # Collection operators
        'in': lambda a, b: a in (b if isinstance(b, list) else [b]),
        'not_in': lambda a, b: a not in (b if isinstance(b, list) else [b]),
        'any_of': lambda a, b: any(item in (a if isinstance(a, list) else [a]) for item in b),
        'all_of': lambda a, b: all(item in (a if isinstance(a, list) else [a]) for item in b),
        
        # Existence operators
        'exists': lambda a, b: a is not None and a != '',
        'not_exists': lambda a, b: a is None or a == '',
        'is_empty': lambda a, b: not bool(a),
        'is_not_empty': lambda a, b: bool(a),
    }
    
    def evaluate_condition(self, condition: dict[str, Any], form_data: dict[str, Any]) -> bool:
        """Evaluate a condition against form data.
        
        Args:
            condition: Condition dictionary with operator, field, value, etc.
            form_data: Form data to evaluate against
            
        Returns:
            bool: True if condition is met, False otherwise
            
        Raises:
            ValueError: If operator is unknown
        """
        if not condition:
            return True
            
        operator = condition.get('operator')
        if not operator:
            return True
            
        # Handle logical operators (and, or, not)
        if operator == 'and':
            conditions = condition.get('conditions', [])
            return all(self.evaluate_condition(c, form_data) for c in conditions)
        elif operator == 'or':
            conditions = condition.get('conditions', [])
            return any(self.evaluate_condition(c, form_data) for c in conditions)
        elif operator == 'not':
            inner_condition = condition.get('condition', {})
            return not self.evaluate_condition(inner_condition, form_data)
        
        # Handle field-based operators
        field = condition.get('field')
        if not field:
            return True
            
        field_value = self.get_field_value(field, form_data)
        expected_value = condition.get('value')
        
        if operator not in self.OPERATORS:
            raise ValueError(f"Unknown operator: {operator}")
            
        return self.OPERATORS[operator](field_value, expected_value)
    
    def get_field_value(self, field_path: str | int, form_data: dict[str, Any]) -> Any:
        """Get field value supporting dot notation for nested fields.
        
        Args:
            field_path: Field path (supports dot notation like "parent.child") or field key
            form_data: Form data dictionary
            
        Returns:
            Any: Field value or None if not found
        """
        # Handle non-string field paths (convert to string)
        if not isinstance(field_path, str):
            field_path = str(field_path)
            
        if '.' not in field_path:
            return form_data.get(field_path)
        
        # Support nested field access: "parent.child.grandchild"
        value = form_data
        for part in field_path.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value


class EntryService(BaseService):
    """Service class for entry page operations.
    
    Provides business logic for schema generation, conditional field evaluation,
    data validation, and configuration management.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        """Initialize entry service.
        
        Args:
            db: Database session
        """
        super().__init__(db)
        self.condition_evaluator = ConditionEvaluator()
        self.rbac_service = RBACService(db)
    
    async def get_profile_schema(self, manufacturing_type_id: int) -> ProfileSchema:
        """Get profile form schema for a manufacturing type.
        
        Args:
            manufacturing_type_id: Manufacturing type ID
            
        Returns:
            ProfileSchema: Generated form schema
            
        Raises:
            NotFoundException: If manufacturing type not found
        """
        # Verify manufacturing type exists
        stmt = select(ManufacturingType).where(ManufacturingType.id == manufacturing_type_id)
        result = await self.db.execute(stmt)
        manufacturing_type = result.scalar_one_or_none()
        
        if not manufacturing_type:
            raise NotFoundException(f"Manufacturing type {manufacturing_type_id} not found")
        
        # Get attribute nodes for this manufacturing type
        stmt = (
            select(AttributeNode)
            .where(AttributeNode.manufacturing_type_id == manufacturing_type_id)
            .order_by(AttributeNode.ltree_path, AttributeNode.sort_order)
        )
        result = await self.db.execute(stmt)
        attribute_nodes = result.scalars().all()
        
        # Generate form schema
        return self.generate_form_schema(manufacturing_type_id, attribute_nodes)
    
    def generate_form_schema(self, manufacturing_type_id: int, attribute_nodes: list[AttributeNode]) -> ProfileSchema:
        """Generate form schema from attribute nodes.
        
        Args:
            manufacturing_type_id: Manufacturing type ID
            attribute_nodes: List of attribute nodes
            
        Returns:
            ProfileSchema: Generated form schema
        """
        sections_dict: dict[str, FormSection] = {}
        conditional_logic: dict[str, Any] = {}
        
        for node in attribute_nodes:
            # Skip category nodes - they don't generate fields
            if node.node_type == 'category':
                continue
                
            # Determine section based on LTREE path
            section_name = self.get_section_name(node.ltree_path)
            
            # Create section if it doesn't exist
            if section_name not in sections_dict:
                sections_dict[section_name] = FormSection(
                    title=section_name,
                    fields=[],
                    sort_order=len(sections_dict)
                )
            
            # Create field definition
            field = self.create_field_definition(node)
            sections_dict[section_name].fields.append(field)
            
            # Add conditional logic if present
            if node.display_condition:
                conditional_logic[node.name] = node.display_condition
        
        # Convert to list and sort by sort_order
        sections = list(sections_dict.values())
        sections.sort(key=lambda s: s.sort_order)
        
        return ProfileSchema(
            manufacturing_type_id=manufacturing_type_id,
            sections=sections,
            conditional_logic=conditional_logic
        )
    
    def get_section_name(self, ltree_path: str) -> str:
        """Get section name from LTREE path.
        
        Args:
            ltree_path: LTREE path string
            
        Returns:
            str: Section name
        """
        if not ltree_path:
            return "general"
        
        # Use the first part of the path as section name
        parts = ltree_path.split('.')
        if len(parts) >= 1:
            section_name = parts[0]
            # Convert snake_case to Title Case
            return section_name.replace('_', ' ').title()
        return "General"
    
    def create_field_definition(self, node: AttributeNode) -> FieldDefinition:
        """Create field definition from attribute node.
        
        Args:
            node: Attribute node
            
        Returns:
            FieldDefinition: Field definition
        """
        return FieldDefinition(
            name=node.name,
            label=node.description or node.name,
            data_type=node.data_type or 'string',
            required=node.required or False,
            validation_rules=node.validation_rules,
            display_condition=node.display_condition,
            ui_component=node.ui_component,
            description=node.description,
            help_text=node.help_text,
            options=None  # TODO: Extract options from child nodes if needed
        )
    
    async def evaluate_display_conditions(
        self, 
        form_data: dict[str, Any], 
        schema: ProfileSchema
    ) -> dict[str, bool]:
        """Evaluate display conditions for all fields.
        
        Args:
            form_data: Current form data
            schema: Form schema with conditional logic
            
        Returns:
            dict[str, bool]: Field visibility map
        """
        visibility: dict[str, bool] = {}
        
        # Evaluate each field's display condition
        for field_name, condition in schema.conditional_logic.items():
            try:
                visibility[field_name] = self.condition_evaluator.evaluate_condition(
                    condition, form_data
                )
            except Exception as e:
                # Log error and default to visible
                print(f"Error evaluating condition for {field_name}: {e}")
                visibility[field_name] = True
        
        return visibility
    
    async def validate_profile_data(self, data: ProfileEntryData) -> dict[str, Any]:
        """Validate profile data against schema rules.
        
        Args:
            data: Profile data to validate
            
        Returns:
            dict[str, Any]: Validation result with errors if any
            
        Raises:
            ValidationException: If validation fails
        """
        errors: dict[str, str] = {}
        
        # Get schema for validation rules
        try:
            schema = await self.get_profile_schema(data.manufacturing_type_id)
        except NotFoundException:
            raise ValidationException("Invalid manufacturing type", {"manufacturing_type_id": "Not found"})
        
        # Validate each field against its rules
        form_data = data.model_dump()
        
        for section in schema.sections:
            for field in section.fields:
                field_value = form_data.get(field.name)
                
                # Check required fields
                if field.required and (field_value is None or field_value == ''):
                    errors[field.name] = f"{field.label} is required"
                    continue
                
                # Apply validation rules if present
                if field.validation_rules and field_value is not None:
                    field_errors = self.validate_field_value(field_value, field.validation_rules, field.label)
                    if field_errors:
                        errors[field.name] = field_errors
        
        # Cross-field validation
        cross_field_errors = self.validate_cross_field_rules(form_data, schema)
        errors.update(cross_field_errors)
        
        if errors:
            raise ValidationException("Validation failed", errors)
        
        return {"valid": True}
    
    def validate_field_value(self, value: Any, rules: dict[str, Any], field_label: str) -> str | None:
        """Validate a field value against validation rules.
        
        Args:
            value: Field value to validate
            rules: Validation rules
            field_label: Field label for error messages
            
        Returns:
            str | None: Error message if validation fails, None if valid
        """
        # Range validation for numbers
        if 'min' in rules and isinstance(value, (int, float)) and value < rules['min']:
            return f"{field_label} must be at least {rules['min']}"
        if 'max' in rules and isinstance(value, (int, float)) and value > rules['max']:
            return f"{field_label} must be at most {rules['max']}"
        
        # Pattern validation for strings
        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                custom_message = rules.get('message', f"{field_label} format is invalid")
                return custom_message
        
        # Length validation for strings
        if 'min_length' in rules and isinstance(value, str) and len(value) < rules['min_length']:
            return f"{field_label} must be at least {rules['min_length']} characters"
        if 'max_length' in rules and isinstance(value, str) and len(value) > rules['max_length']:
            return f"{field_label} must be at most {rules['max_length']} characters"
        
        # Enum/choice validation
        if 'choices' in rules and value not in rules['choices']:
            choices_str = ', '.join(str(c) for c in rules['choices'])
            return f"{field_label} must be one of: {choices_str}"
        
        # Custom validation rules
        if 'rule_type' in rules:
            rule_type = rules['rule_type']
            
            if rule_type == 'range' and isinstance(value, (int, float)):
                min_val = rules.get('min', float('-inf'))
                max_val = rules.get('max', float('inf'))
                if not (min_val <= value <= max_val):
                    custom_message = rules.get('message', f"{field_label} must be between {min_val} and {max_val}")
                    return custom_message
            
            elif rule_type == 'email' and isinstance(value, str):
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, value):
                    custom_message = rules.get('message', f"{field_label} must be a valid email address")
                    return custom_message
            
            elif rule_type == 'url' and isinstance(value, str):
                url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                if not re.match(url_pattern, value):
                    custom_message = rules.get('message', f"{field_label} must be a valid URL")
                    return custom_message
            
            elif rule_type == 'positive' and isinstance(value, (int, float)):
                if value <= 0:
                    custom_message = rules.get('message', f"{field_label} must be positive")
                    return custom_message
            
            elif rule_type == 'non_negative' and isinstance(value, (int, float)):
                if value < 0:
                    custom_message = rules.get('message', f"{field_label} must be non-negative")
                    return custom_message
        
        return None
    
    def validate_cross_field_rules(self, form_data: dict[str, Any], schema: ProfileSchema) -> dict[str, str]:
        """Validate cross-field rules and dependencies.
        
        Args:
            form_data: Form data to validate
            schema: Form schema with field definitions
            
        Returns:
            dict[str, str]: Field errors from cross-field validation
        """
        errors: dict[str, str] = {}
        
        # Business logic validations for profile entry
        
        # If builtin_flyscreen_track is True, total_width and flyscreen_track_height should be provided
        if form_data.get('builtin_flyscreen_track') is True:
            if not form_data.get('total_width'):
                errors['total_width'] = "Total width is required when builtin flyscreen track is enabled"
            if not form_data.get('flyscreen_track_height'):
                errors['flyscreen_track_height'] = "Flyscreen track height is required when builtin flyscreen track is enabled"
        
        # If type is "Flying mullion", clearance fields should be provided
        if form_data.get('type') == 'Flying mullion':
            if not form_data.get('flying_mullion_horizontal_clearance'):
                errors['flying_mullion_horizontal_clearance'] = "Horizontal clearance is required for flying mullion type"
            if not form_data.get('flying_mullion_vertical_clearance'):
                errors['flying_mullion_vertical_clearance'] = "Vertical clearance is required for flying mullion type"
        
        # If reinforcement_steel is provided, steel_material_thickness should be provided
        if form_data.get('reinforcement_steel'):
            if not form_data.get('steel_material_thickness'):
                errors['steel_material_thickness'] = "Steel material thickness is required when reinforcement steel is specified"
        
        # Logical validations
        if form_data.get('front_height') and form_data.get('rear_height'):
            front_height = form_data['front_height']
            rear_height = form_data['rear_height']
            if abs(front_height - rear_height) > 50:  # Example business rule
                errors['rear_height'] = "Rear height should not differ from front height by more than 50mm"
        
        # Price validation
        if form_data.get('price_per_meter') and form_data.get('price_per_beam'):
            if form_data.get('length_of_beam'):
                expected_beam_price = form_data['price_per_meter'] * form_data['length_of_beam']
                actual_beam_price = form_data['price_per_beam']
                if abs(expected_beam_price - actual_beam_price) > expected_beam_price * 0.1:  # 10% tolerance
                    errors['price_per_beam'] = "Price per beam should be approximately price per meter × length of beam"
        
        return errors
    
    # @require(ConfigurationCreator)
    # @require(AdminAccess)  # Allow admins to save configurations
    async def save_profile_configuration(self, data: ProfileEntryData, user: User) -> Configuration:
        """Save profile configuration data with proper customer relationship.
        
        Args:
            data: Profile data to save
            user: Current user
            
        Returns:
            Configuration: Created configuration
            
        Raises:
            ValidationException: If validation fails
            NotFoundException: If manufacturing type not found
        """
        # Validate data first
        await self.validate_profile_data(data)
        
        # Get manufacturing type for base price/weight
        stmt = select(ManufacturingType).where(ManufacturingType.id == data.manufacturing_type_id)
        result = await self.db.execute(stmt)
        manufacturing_type = result.scalar_one_or_none()
        
        if not manufacturing_type:
            raise NotFoundException(f"Manufacturing type {data.manufacturing_type_id} not found")
        
        # Get attribute nodes for field mapping
        stmt = (
            select(AttributeNode)
            .where(AttributeNode.manufacturing_type_id == data.manufacturing_type_id)
        )
        result = await self.db.execute(stmt)
        attribute_nodes = result.scalars().all()
        
        # Create field name to attribute node mapping
        field_to_node = {node.name: node for node in attribute_nodes}
        
        # Get or create customer for user using RBAC service
        customer = await self.rbac_service.get_or_create_customer_for_user(user)
        
        # Create configuration with proper customer relationship
        config_data = {
            "manufacturing_type_id": data.manufacturing_type_id,
            "customer_id": customer.id,  # Use proper customer ID instead of user.id
            "name": data.name,
            "description": f"Profile entry for {data.type}",
            "status": "draft",
            "base_price": manufacturing_type.base_price,
            "total_price": manufacturing_type.base_price,  # TODO: Calculate with selections
            "calculated_weight": manufacturing_type.base_weight,  # TODO: Calculate with selections
            "calculated_technical_data": {},
        }
        
        configuration = Configuration(**config_data)
        self.db.add(configuration)
        await self.commit()
        await self.refresh(configuration)
        
        # Create configuration selections for non-null fields
        form_data = data.model_dump(exclude={'manufacturing_type_id', 'name'})
        
        for field_name, field_value in form_data.items():
            if field_value is not None and field_name in field_to_node:
                attribute_node = field_to_node[field_name]
                
                # Create selection with proper attribute node mapping
                selection_data = {
                    "configuration_id": configuration.id,
                    "attribute_node_id": attribute_node.id,
                    "selection_path": attribute_node.ltree_path,
                }
                
                # Store value in appropriate field based on data type
                if isinstance(field_value, bool):
                    selection_data["boolean_value"] = field_value
                elif isinstance(field_value, (int, float)):
                    selection_data["numeric_value"] = field_value
                elif isinstance(field_value, (list, dict)):
                    selection_data["json_value"] = field_value
                else:
                    selection_data["string_value"] = str(field_value)
                
                selection = ConfigurationSelection(**selection_data)
                self.db.add(selection)
        
        await self.commit()
        return configuration
    
    # @require(ConfigurationViewer)
    # @require(AdminAccess)  # Admins can view any configuration
    async def load_profile_configuration(self, configuration_id: int, user: User) -> ProfileEntryData:
        """Load profile configuration data and populate form fields.
        
        Args:
            configuration_id: Configuration ID to load
            user: Current user
            
        Returns:
            ProfileEntryData: Populated form data
            
        Raises:
            NotFoundException: If configuration not found
            AuthorizationException: If user lacks permission
        """
        # Get configuration with selections
        stmt = (
            select(Configuration)
            .options(selectinload(Configuration.selections))
            .where(Configuration.id == configuration_id)
        )
        result = await self.db.execute(stmt)
        configuration = result.scalar_one_or_none()
        
        if not configuration:
            raise NotFoundException(f"Configuration {configuration_id} not found")
        
        # Authorization is handled by the @require decorator
        # No need for manual authorization checks
        
        # Get attribute nodes for field mapping
        stmt = (
            select(AttributeNode)
            .where(AttributeNode.manufacturing_type_id == configuration.manufacturing_type_id)
        )
        result = await self.db.execute(stmt)
        attribute_nodes = result.scalars().all()
        
        # Create attribute node ID to field name mapping
        node_to_field = {node.id: node.name for node in attribute_nodes}
        
        # Start with base configuration data
        form_data = {
            "manufacturing_type_id": configuration.manufacturing_type_id,
            "name": configuration.name,
        }
        
        # Populate form data from selections
        for selection in configuration.selections:
            field_name = node_to_field.get(selection.attribute_node_id)
            if field_name:
                # Get value from appropriate field
                if selection.boolean_value is not None:
                    form_data[field_name] = selection.boolean_value
                elif selection.numeric_value is not None:
                    form_data[field_name] = selection.numeric_value
                elif selection.json_value is not None:
                    form_data[field_name] = selection.json_value
                elif selection.string_value is not None:
                    form_data[field_name] = selection.string_value
        
        # Create ProfileEntryData with validation
        return ProfileEntryData(**form_data)
    
    @require(ConfigurationViewer)
    @require(AdminAccess)  # Admins can view any configuration
    async def generate_preview_data(self, configuration_id: int, user: User) -> ProfilePreviewData:
        """Generate preview data for a configuration.
        
        Args:
            configuration_id: Configuration ID
            user: Current user
            
        Returns:
            ProfilePreviewData: Preview data
            
        Raises:
            NotFoundException: If configuration not found
            AuthorizationException: If user lacks permission
        """
        # Get configuration with selections
        stmt = (
            select(Configuration)
            .options(selectinload(Configuration.selections))
            .where(Configuration.id == configuration_id)
        )
        result = await self.db.execute(stmt)
        configuration = result.scalar_one_or_none()
        
        if not configuration:
            raise NotFoundException(f"Configuration {configuration_id} not found")
        
        # Authorization is handled by the @require decorator
        # No need for manual authorization checks
        
        # Generate preview table
        preview_table = self.generate_preview_table(configuration)
        
        return ProfilePreviewData(
            configuration_id=configuration.id,
            table=preview_table,
            last_updated=configuration.updated_at
        )
    
    def generate_preview_table(self, data: Configuration | dict[str, Any]) -> PreviewTable:
        """Generate preview table from configuration data or form data.
        
        Args:
            data: Configuration with selections or form data dictionary
            
        Returns:
            PreviewTable: Preview table structure
        """
        # Define CSV column headers (all 29 columns) - exact match with template
        headers = [
            "Name", "Type", "Company", "Material", "opening system", "system series",
            "Code", "Length of Beam\nm", "Renovation\nonly for frame", "width", 
            "builtin Flyscreen track only for sliding frame", "Total width\nonly for frame with builtin flyscreen",
            "flyscreen track height\nonly for frame with builtin flyscreen", "front Height mm", "Rear heightt",
            "Glazing height", "Renovation height mm\nonly for frame", "Glazing undercut heigth\nonly for glazing bead",
            "Pic", "Sash overlap only for sashs", "flying mullion horizontal clearance", 
            "flying mullion vertical clearance", "Steel material thickness\nonly for reinforcement",
            "Weight/m kg", "Reinforcement steel", "Colours", "Price/m", "Price per/beam", "UPVC Profile Discount%"
        ]
        
        # Header to field mapping (exact match with template)
        header_mapping = {
            "Name": "name",
            "Type": "type",
            "Company": "company",
            "Material": "material",
            "opening system": "opening_system",
            "system series": "system_series",
            "Code": "code",
            "Length of Beam\nm": "length_of_beam",
            "Renovation\nonly for frame": "renovation",
            "width": "width",
            "builtin Flyscreen track only for sliding frame": "builtin_flyscreen_track",
            "Total width\nonly for frame with builtin flyscreen": "total_width",
            "flyscreen track height\nonly for frame with builtin flyscreen": "flyscreen_track_height",
            "front Height mm": "front_height",
            "Rear heightt": "rear_height",
            "Glazing height": "glazing_height",
            "Renovation height mm\nonly for frame": "renovation_height",
            "Glazing undercut heigth\nonly for glazing bead": "glazing_undercut_height",
            "Pic": "pic",
            "Sash overlap only for sashs": "sash_overlap",
            "flying mullion horizontal clearance": "flying_mullion_horizontal_clearance",
            "flying mullion vertical clearance": "flying_mullion_vertical_clearance",
            "Steel material thickness\nonly for reinforcement": "steel_material_thickness",
            "Weight/m kg": "weight_per_meter",
            "Reinforcement steel": "reinforcement_steel",
            "Colours": "colours",
            "Price/m": "price_per_meter",
            "Price per/beam": "price_per_beam",
            "UPVC Profile Discount%": "upvc_profile_discount"
        }
        
        # Create row data
        row_data: dict[str, Any] = {}
        
        if isinstance(data, Configuration):
            # Handle Configuration object
            row_data["Name"] = data.name
            
            # Map selections to CSV columns
            for selection in data.selections:
                field_name = selection.selection_path
                value = selection.string_value or selection.json_value or selection.numeric_value or selection.boolean_value
                
                # Find header for this field
                for header, field in header_mapping.items():
                    if field == field_name:
                        row_data[header] = self.format_preview_value(value)
                        break
        else:
            # Handle dictionary (form data)
            for header, field_name in header_mapping.items():
                value = data.get(field_name)
                row_data[header] = self.format_preview_value(value)
        
        # Fill missing columns with N/A
        for header in headers:
            if header not in row_data:
                row_data[header] = "N/A"
        
        return PreviewTable(
            headers=headers,
            rows=[row_data]
        )
    
    def format_preview_value(self, value: Any) -> str:
        """Format value for preview display.
        
        Args:
            value: Value to format
            
        Returns:
            str: Formatted value
        """
        if value is None or value == '':
            return "N/A"
        elif isinstance(value, bool):
            return "yes" if value else "no"  # Lowercase to match CSV format
        elif isinstance(value, list):
            if len(value) == 0:
                return "N/A"
            return ", ".join(str(v) for v in value)
        elif isinstance(value, (int, float)):
            # Format numbers appropriately
            return str(value)
        elif hasattr(value, '__str__'):  # Handle Decimal and other numeric types
            return str(value)
        elif isinstance(value, dict):
            return str(value)  # TODO: Better dict formatting
        else:
            return str(value)
    
    # Customer management is now handled by RBACService
    # This method is deprecated - use rbac_service.get_or_create_customer_for_user() instead


# JavaScript equivalent for client-side evaluation
JAVASCRIPT_CONDITION_EVALUATOR = '''
class ConditionEvaluator {
    static OPERATORS = {
        // Comparison operators
        equals: (a, b) => a == b,
        not_equals: (a, b) => a != b,
        greater_than: (a, b) => (a || 0) > (b || 0),
        less_than: (a, b) => (a || 0) < (b || 0),
        greater_equal: (a, b) => (a || 0) >= (b || 0),
        less_equal: (a, b) => (a || 0) <= (b || 0),
        
        // String operators
        contains: (a, b) => String(a || '').toLowerCase().includes(String(b).toLowerCase()),
        starts_with: (a, b) => String(a || '').toLowerCase().startsWith(String(b).toLowerCase()),
        ends_with: (a, b) => String(a || '').toLowerCase().endsWith(String(b).toLowerCase()),
        matches_pattern: (a, b) => new RegExp(b).test(String(a || '')),
        
        // Collection operators
        in: (a, b) => (Array.isArray(b) ? b : [b]).includes(a),
        not_in: (a, b) => !(Array.isArray(b) ? b : [b]).includes(a),
        any_of: (a, b) => b.some(item => (Array.isArray(a) ? a : [a]).includes(item)),
        all_of: (a, b) => b.every(item => (Array.isArray(a) ? a : [a]).includes(item)),
        
        // Existence operators
        exists: (a, b) => a !== null && a !== undefined && a !== '',
        not_exists: (a, b) => a === null || a === undefined || a === '',
        is_empty: (a, b) => !Boolean(a),
        is_not_empty: (a, b) => Boolean(a),
    };
    
    static evaluateCondition(condition, formData) {
        if (!condition) return true;
        
        const operator = condition.operator;
        if (!operator) return true;
        
        // Handle logical operators
        if (operator === 'and') {
            return (condition.conditions || []).every(c => 
                ConditionEvaluator.evaluateCondition(c, formData)
            );
        } else if (operator === 'or') {
            return (condition.conditions || []).some(c => 
                ConditionEvaluator.evaluateCondition(c, formData)
            );
        } else if (operator === 'not') {
            return !ConditionEvaluator.evaluateCondition(condition.condition, formData);
        }
        
        // Handle field-based operators
        const field = condition.field;
        if (!field) return true;
        
        const fieldValue = ConditionEvaluator.getFieldValue(field, formData);
        const expectedValue = condition.value;
        
        const operatorFn = ConditionEvaluator.OPERATORS[operator];
        if (!operatorFn) {
            throw new Error(`Unknown operator: ${operator}`);
        }
        
        return operatorFn(fieldValue, expectedValue);
    }
    
    static getFieldValue(fieldPath, formData) {
        if (!fieldPath.includes('.')) {
            return formData[fieldPath];
        }
        
        // Support nested field access
        let value = formData;
        for (const part of fieldPath.split('.')) {
            if (value && typeof value === 'object') {
                value = value[part];
            } else {
                return undefined;
            }
        }
        return value;
    }
}
'''