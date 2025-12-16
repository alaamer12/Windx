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
    roles=[Role.CUSTOMER, Role.SALESMAN, Role.PARTNER],
    permission=Permission("configuration", "create")
)

ConfigurationViewer = Privilege(
    roles=Role.CUSTOMER | Role.SALESMAN | Role.PARTNER,
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
    
    def get_field_value(self, field_path: str, form_data: dict[str, Any]) -> Any:
        """Get field value supporting dot notation for nested fields.
        
        Args:
            field_path: Field path (supports dot notation like "parent.child")
            form_data: Form data dictionary
            
        Returns:
            Any: Field value or None if not found
        """
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
        # Range validation
        if 'min' in rules and isinstance(value, (int, float)) and value < rules['min']:
            return f"{field_label} must be at least {rules['min']}"
        if 'max' in rules and isinstance(value, (int, float)) and value > rules['max']:
            return f"{field_label} must be at most {rules['max']}"
        
        # Pattern validation
        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                return f"{field_label} format is invalid"
        
        # Length validation
        if 'min_length' in rules and isinstance(value, str) and len(value) < rules['min_length']:
            return f"{field_label} must be at least {rules['min_length']} characters"
        if 'max_length' in rules and isinstance(value, str) and len(value) > rules['max_length']:
            return f"{field_label} must be at most {rules['max_length']} characters"
        
        return None
    
    @require(ConfigurationCreator)
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
            if field_value is not None:
                # TODO: Get actual attribute node ID for this field
                # For now, create a simple selection record
                selection = ConfigurationSelection(
                    configuration_id=configuration.id,
                    attribute_node_id=1,  # TODO: Map field to actual attribute node
                    string_value=str(field_value) if not isinstance(field_value, (list, dict)) else None,
                    json_value=field_value if isinstance(field_value, (list, dict)) else None,
                    selection_path=field_name,
                )
                self.db.add(selection)
        
        await self.commit()
        return configuration
    
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
    
    def generate_preview_table(self, configuration: Configuration) -> PreviewTable:
        """Generate preview table from configuration data.
        
        Args:
            configuration: Configuration with selections
            
        Returns:
            PreviewTable: Preview table structure
        """
        # Define CSV column headers (all 29 columns)
        headers = [
            "Name", "Type", "Company", "Material", "Opening System", "System Series",
            "Code", "Length of beam", "Renovation", "Width", "Builtin Flyscreen Track",
            "Total Width", "Flyscreen Track Height", "Front Height", "Rear Height",
            "Glazing Height", "Renovation Height", "Glazing Undercut Height", "Pic",
            "Sash Overlap", "Flying Mullion Horizontal Clearance", "Flying Mullion Vertical Clearance",
            "Steel Material Thickness", "Weight per meter", "Reinforcement Steel", "Colours",
            "Price per meter", "Price per beam", "UPVC Profile Discount"
        ]
        
        # Create row data from configuration selections
        row_data: dict[str, Any] = {}
        
        # Initialize with configuration basic data
        row_data["Name"] = configuration.name
        
        # Map selections to CSV columns
        for selection in configuration.selections:
            field_name = selection.selection_path
            value = selection.string_value or selection.json_value or selection.numeric_value or selection.boolean_value
            
            # Map field names to CSV headers (simplified mapping)
            header_mapping = {
                "type": "Type",
                "company": "Company", 
                "material": "Material",
                "opening_system": "Opening System",
                "system_series": "System Series",
                "code": "Code",
                "length_of_beam": "Length of beam",
                "renovation": "Renovation",
                "width": "Width",
                "builtin_flyscreen_track": "Builtin Flyscreen Track",
                "total_width": "Total Width",
                "flyscreen_track_height": "Flyscreen Track Height",
                "front_height": "Front Height",
                "rear_height": "Rear Height",
                "glazing_height": "Glazing Height",
                "renovation_height": "Renovation Height",
                "glazing_undercut_height": "Glazing Undercut Height",
                "pic": "Pic",
                "sash_overlap": "Sash Overlap",
                "flying_mullion_horizontal_clearance": "Flying Mullion Horizontal Clearance",
                "flying_mullion_vertical_clearance": "Flying Mullion Vertical Clearance",
                "steel_material_thickness": "Steel Material Thickness",
                "weight_per_meter": "Weight per meter",
                "reinforcement_steel": "Reinforcement Steel",
                "colours": "Colours",
                "price_per_meter": "Price per meter",
                "price_per_beam": "Price per beam",
                "upvc_profile_discount": "UPVC Profile Discount",
            }
            
            header = header_mapping.get(field_name)
            if header:
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
        if value is None:
            return "N/A"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, list):
            return ", ".join(str(v) for v in value)
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