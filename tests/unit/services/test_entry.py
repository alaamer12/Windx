"""Unit tests for entry service and condition evaluators.

Tests service creation with database session and authentication integration,
operator parity between Python and JavaScript versions, and complex nested
conditions with performance considerations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.entry import ConditionEvaluator, EntryService
from app.models.manufacturing_type import ManufacturingType
from app.models.attribute_node import AttributeNode
from app.models.user import User
from app.schemas.entry import ProfileEntryData
from app.core.exceptions import NotFoundException, ValidationException


class TestConditionEvaluator:
    """Test the ConditionEvaluator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ConditionEvaluator()
        self.sample_form_data = {
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "sliding",
            "width": 48.5,
            "builtin_flyscreen_track": True,
            "nested": {
                "child": {
                    "value": "test"
                }
            }
        }
    
    def test_comparison_operators(self):
        """Test comparison operators work correctly."""
        # Equals
        condition = {"operator": "equals", "field": "type", "value": "Frame"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        condition = {"operator": "equals", "field": "type", "value": "Door"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
        
        # Not equals
        condition = {"operator": "not_equals", "field": "type", "value": "Door"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        # Greater than
        condition = {"operator": "greater_than", "field": "width", "value": 40}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        condition = {"operator": "greater_than", "field": "width", "value": 50}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
    
    def test_string_operators(self):
        """Test string operators work correctly."""
        # Contains
        condition = {"operator": "contains", "field": "opening_system", "value": "slid"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        condition = {"operator": "contains", "field": "opening_system", "value": "casement"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
        
        # Starts with
        condition = {"operator": "starts_with", "field": "material", "value": "Alum"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        # Ends with
        condition = {"operator": "ends_with", "field": "material", "value": "inum"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        # Pattern matching
        condition = {"operator": "matches_pattern", "field": "type", "value": "^Frame$"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
    
    def test_collection_operators(self):
        """Test collection operators work correctly."""
        # In
        condition = {"operator": "in", "field": "type", "value": ["Frame", "Door"]}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        condition = {"operator": "in", "field": "type", "value": ["Door", "Window"]}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
        
        # Not in
        condition = {"operator": "not_in", "field": "type", "value": ["Door", "Window"]}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
    
    def test_existence_operators(self):
        """Test existence operators work correctly."""
        # Exists
        condition = {"operator": "exists", "field": "type", "value": None}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        condition = {"operator": "exists", "field": "nonexistent", "value": None}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
        
        # Not exists
        condition = {"operator": "not_exists", "field": "nonexistent", "value": None}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        # Is empty
        empty_data = {"empty_field": ""}
        condition = {"operator": "is_empty", "field": "empty_field", "value": None}
        assert self.evaluator.evaluate_condition(condition, empty_data) is True
        
        # Is not empty
        condition = {"operator": "is_not_empty", "field": "type", "value": None}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
    
    def test_logical_operators(self):
        """Test logical operators work correctly."""
        # AND
        condition = {
            "operator": "and",
            "conditions": [
                {"operator": "equals", "field": "type", "value": "Frame"},
                {"operator": "equals", "field": "material", "value": "Aluminum"}
            ]
        }
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        condition = {
            "operator": "and",
            "conditions": [
                {"operator": "equals", "field": "type", "value": "Frame"},
                {"operator": "equals", "field": "material", "value": "Wood"}
            ]
        }
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
        
        # OR
        condition = {
            "operator": "or",
            "conditions": [
                {"operator": "equals", "field": "type", "value": "Door"},
                {"operator": "equals", "field": "material", "value": "Aluminum"}
            ]
        }
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        # NOT
        condition = {
            "operator": "not",
            "condition": {"operator": "equals", "field": "type", "value": "Door"}
        }
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
    
    def test_nested_field_access(self):
        """Test nested field access with dot notation."""
        # Simple nested access
        condition = {"operator": "equals", "field": "nested.child.value", "value": "test"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
        
        # Non-existent nested field
        condition = {"operator": "equals", "field": "nested.nonexistent.value", "value": "test"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is False
    
    def test_complex_nested_conditions(self):
        """Test complex nested conditions with multiple levels."""
        condition = {
            "operator": "and",
            "conditions": [
                {
                    "operator": "or",
                    "conditions": [
                        {"operator": "equals", "field": "type", "value": "Frame"},
                        {"operator": "equals", "field": "type", "value": "Door"}
                    ]
                },
                {
                    "operator": "and",
                    "conditions": [
                        {"operator": "contains", "field": "opening_system", "value": "sliding"},
                        {"operator": "greater_than", "field": "width", "value": 40}
                    ]
                }
            ]
        }
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True
    
    def test_invalid_operator_handling(self):
        """Test handling of invalid operators."""
        condition = {"operator": "invalid_operator", "field": "type", "value": "Frame"}
        
        with pytest.raises(ValueError, match="Unknown operator"):
            self.evaluator.evaluate_condition(condition, self.sample_form_data)
    
    def test_empty_conditions(self):
        """Test handling of empty or None conditions."""
        # Empty condition should return True
        assert self.evaluator.evaluate_condition({}, self.sample_form_data) is True
        assert self.evaluator.evaluate_condition(None, self.sample_form_data) is True
        
        # Condition without operator should return True
        condition = {"field": "type", "value": "Frame"}
        assert self.evaluator.evaluate_condition(condition, self.sample_form_data) is True


class TestEntryService:
    """Test the EntryService class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def entry_service(self, mock_db):
        """Create EntryService instance with mock database."""
        return EntryService(mock_db)
    
    @pytest.fixture
    def sample_manufacturing_type(self):
        """Create sample manufacturing type."""
        return ManufacturingType(
            id=1,
            name="Test Window",
            description="Test window type",
            base_price=200.00,
            base_weight=15.00,
            is_active=True
        )
    
    @pytest.fixture
    def sample_attribute_nodes(self):
        """Create sample attribute nodes."""
        return [
            AttributeNode(
                id=1,
                manufacturing_type_id=1,
                name="type",
                node_type="attribute",
                data_type="string",
                required=True,
                ltree_path="basic.type",
                description="Product type",
                ui_component="dropdown"
            ),
            AttributeNode(
                id=2,
                manufacturing_type_id=1,
                name="material",
                node_type="attribute", 
                data_type="string",
                required=True,
                ltree_path="basic.material",
                description="Material type",
                ui_component="dropdown"
            ),
            AttributeNode(
                id=3,
                manufacturing_type_id=1,
                name="width",
                node_type="attribute",
                data_type="number",
                required=False,
                ltree_path="dimensions.width",
                description="Width in inches",
                ui_component="input",
                validation_rules={"min": 10, "max": 100}
            )
        ]
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_superuser=False
        )
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_db):
        """Test service creation with database session."""
        service = EntryService(mock_db)
        
        assert service.db == mock_db
        assert isinstance(service.condition_evaluator, ConditionEvaluator)
    
    @pytest.mark.asyncio
    async def test_get_profile_schema_success(self, entry_service, sample_manufacturing_type, sample_attribute_nodes):
        """Test successful profile schema generation."""
        # Mock database queries
        entry_service.db.execute = AsyncMock()
        
        # Mock manufacturing type query
        mfg_result = MagicMock()
        mfg_result.scalar_one_or_none.return_value = sample_manufacturing_type
        
        # Mock attribute nodes query
        attr_result = MagicMock()
        attr_result.scalars.return_value.all.return_value = sample_attribute_nodes
        
        entry_service.db.execute.side_effect = [mfg_result, attr_result]
        
        # Test schema generation
        schema = await entry_service.get_profile_schema(1)
        
        assert schema.manufacturing_type_id == 1
        assert len(schema.sections) > 0
        
        # Check that fields were created
        all_fields = []
        for section in schema.sections:
            all_fields.extend(section.fields)
        
        field_names = [field.name for field in all_fields]
        assert "type" in field_names
        assert "material" in field_names
        assert "width" in field_names
    
    @pytest.mark.asyncio
    async def test_get_profile_schema_not_found(self, entry_service):
        """Test profile schema generation with non-existent manufacturing type."""
        # Mock database query to return None
        entry_service.db.execute = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        entry_service.db.execute.return_value = result
        
        with pytest.raises(NotFoundException, match="Manufacturing type 999 not found"):
            await entry_service.get_profile_schema(999)
    
    def test_generate_form_schema(self, entry_service, sample_attribute_nodes):
        """Test form schema generation from attribute nodes."""
        schema = entry_service.generate_form_schema(1, sample_attribute_nodes)
        
        assert schema.manufacturing_type_id == 1
        assert len(schema.sections) > 0
        
        # Check sections were created based on LTREE paths
        section_titles = [section.title for section in schema.sections]
        assert "Basic" in section_titles
        assert "Dimensions" in section_titles
    
    def test_create_field_definition(self, entry_service, sample_attribute_nodes):
        """Test field definition creation from attribute node."""
        node = sample_attribute_nodes[2]  # width field with validation
        field = entry_service.create_field_definition(node)
        
        assert field.name == "width"
        assert field.label == "Width in inches"
        assert field.data_type == "number"
        assert field.required is False
        assert field.validation_rules == {"min": 10, "max": 100}
        assert field.ui_component == "input"
    
    def test_get_section_name(self, entry_service):
        """Test section name extraction from LTREE path."""
        assert entry_service.get_section_name("basic.type") == "basic"
        assert entry_service.get_section_name("dimensions.width.value") == "dimensions"
        assert entry_service.get_section_name("") == "general"
        assert entry_service.get_section_name("single") == "single"
    
    @pytest.mark.asyncio
    async def test_evaluate_display_conditions(self, entry_service):
        """Test display condition evaluation."""
        from app.schemas.entry import ProfileSchema, FormSection, FieldDefinition
        
        # Create schema with conditional logic
        schema = ProfileSchema(
            manufacturing_type_id=1,
            sections=[],
            conditional_logic={
                "renovation": {
                    "operator": "equals",
                    "field": "type",
                    "value": "Frame"
                },
                "flyscreen_width": {
                    "operator": "and",
                    "conditions": [
                        {"operator": "equals", "field": "type", "value": "Frame"},
                        {"operator": "equals", "field": "builtin_flyscreen_track", "value": True}
                    ]
                }
            }
        )
        
        form_data = {
            "type": "Frame",
            "builtin_flyscreen_track": True
        }
        
        visibility = await entry_service.evaluate_display_conditions(form_data, schema)
        
        assert visibility["renovation"] is True
        assert visibility["flyscreen_width"] is True
        
        # Test with different form data
        form_data["type"] = "Door"
        visibility = await entry_service.evaluate_display_conditions(form_data, schema)
        
        assert visibility["renovation"] is False
        assert visibility["flyscreen_width"] is False
    
    def test_validate_field_value(self, entry_service):
        """Test field value validation against rules."""
        # Range validation
        error = entry_service.validate_field_value(5, {"min": 10, "max": 100}, "Width")
        assert "must be at least 10" in error
        
        error = entry_service.validate_field_value(150, {"min": 10, "max": 100}, "Width")
        assert "must be at most 100" in error
        
        error = entry_service.validate_field_value(50, {"min": 10, "max": 100}, "Width")
        assert error is None
        
        # Pattern validation
        error = entry_service.validate_field_value("invalid", {"pattern": "^[A-Z]{2}\\d{5}$"}, "Code")
        assert "format is invalid" in error
        
        error = entry_service.validate_field_value("AB12345", {"pattern": "^[A-Z]{2}\\d{5}$"}, "Code")
        assert error is None
        
        # Length validation
        error = entry_service.validate_field_value("ab", {"min_length": 5}, "Name")
        assert "must be at least 5 characters" in error
        
        error = entry_service.validate_field_value("a" * 200, {"max_length": 100}, "Name")
        assert "must be at most 100 characters" in error
    
    @pytest.mark.asyncio
    async def test_validate_profile_data_success(self, entry_service, sample_manufacturing_type, sample_attribute_nodes):
        """Test successful profile data validation."""
        # Mock get_profile_schema
        entry_service.get_profile_schema = AsyncMock()
        from app.schemas.entry import ProfileSchema, FormSection, FieldDefinition
        
        schema = ProfileSchema(
            manufacturing_type_id=1,
            sections=[
                FormSection(
                    title="Basic",
                    fields=[
                        FieldDefinition(
                            name="type",
                            label="Type",
                            data_type="string",
                            required=True
                        ),
                        FieldDefinition(
                            name="width",
                            label="Width",
                            data_type="number",
                            validation_rules={"min": 10, "max": 100}
                        )
                    ]
                )
            ]
        )
        entry_service.get_profile_schema.return_value = schema
        
        # Valid profile data
        profile_data = ProfileEntryData(
            manufacturing_type_id=1,
            name="Test Window",
            type="Frame",
            material="Aluminum",
            opening_system="Casement",
            system_series="Series100",
            width=50.0
        )
        
        result = await entry_service.validate_profile_data(profile_data)
        assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_validate_profile_data_validation_errors(self, entry_service):
        """Test profile data validation with errors."""
        # Mock get_profile_schema
        entry_service.get_profile_schema = AsyncMock()
        from app.schemas.entry import ProfileSchema, FormSection, FieldDefinition
        
        schema = ProfileSchema(
            manufacturing_type_id=1,
            sections=[
                FormSection(
                    title="Basic",
                    fields=[
                        FieldDefinition(
                            name="type",
                            label="Type",
                            data_type="string",
                            required=True
                        ),
                        FieldDefinition(
                            name="width",
                            label="Width",
                            data_type="number",
                            validation_rules={"min": 10, "max": 100}
                        )
                    ]
                )
            ]
        )
        entry_service.get_profile_schema.return_value = schema
        
        # Invalid profile data (missing required field, invalid width)
        profile_data = ProfileEntryData(
            manufacturing_type_id=1,
            name="Test Window",
            type="",  # Empty required field
            material="Aluminum",
            opening_system="Casement",
            system_series="Series100",
            width=150.0  # Exceeds max
        )
        
        with pytest.raises(ValidationException) as exc_info:
            await entry_service.validate_profile_data(profile_data)
        
        assert "Validation failed" in str(exc_info.value)
        assert "Type is required" in str(exc_info.value.field_errors)
        assert "must be at most 100" in str(exc_info.value.field_errors)
    
    def test_format_preview_value(self, entry_service):
        """Test preview value formatting."""
        assert entry_service.format_preview_value(None) == "N/A"
        assert entry_service.format_preview_value(True) == "Yes"
        assert entry_service.format_preview_value(False) == "No"
        assert entry_service.format_preview_value(["A", "B", "C"]) == "A, B, C"
        assert entry_service.format_preview_value({"key": "value"}) == "{'key': 'value'}"
        assert entry_service.format_preview_value("test") == "test"
        assert entry_service.format_preview_value(42) == "42"


class TestOperatorParity:
    """Test parity between Python and JavaScript operators."""
    
    def test_comparison_operator_parity(self):
        """Test that comparison operators work identically."""
        evaluator = ConditionEvaluator()
        test_cases = [
            (5, 5, True),   # equals
            (5, 3, False),  # equals
            (5, 3, True),   # not_equals
            (5, 5, False),  # not_equals
            (5, 3, True),   # greater_than
            (3, 5, False),  # greater_than
            (5, 3, False),  # less_than
            (3, 5, True),   # less_than
        ]
        
        operators = ["equals", "not_equals", "greater_than", "less_than"]
        
        for i, (a, b, expected) in enumerate(test_cases):
            operator = operators[i // 2]
            result = evaluator.OPERATORS[operator](a, b)
            assert result == expected, f"Operator {operator} failed for {a}, {b}"
    
    def test_string_operator_parity(self):
        """Test that string operators work identically."""
        evaluator = ConditionEvaluator()
        
        # Contains (case insensitive)
        assert evaluator.OPERATORS["contains"]("Hello World", "hello") is True
        assert evaluator.OPERATORS["contains"]("Hello World", "xyz") is False
        
        # Starts with (case insensitive)
        assert evaluator.OPERATORS["starts_with"]("Hello World", "hello") is True
        assert evaluator.OPERATORS["starts_with"]("Hello World", "world") is False
        
        # Ends with (case insensitive)
        assert evaluator.OPERATORS["ends_with"]("Hello World", "world") is True
        assert evaluator.OPERATORS["ends_with"]("Hello World", "hello") is False
    
    def test_collection_operator_parity(self):
        """Test that collection operators work identically."""
        evaluator = ConditionEvaluator()
        
        # In operator
        assert evaluator.OPERATORS["in"]("apple", ["apple", "banana"]) is True
        assert evaluator.OPERATORS["in"]("orange", ["apple", "banana"]) is False
        assert evaluator.OPERATORS["in"]("apple", "apple") is True  # Single value
        
        # Not in operator
        assert evaluator.OPERATORS["not_in"]("orange", ["apple", "banana"]) is True
        assert evaluator.OPERATORS["not_in"]("apple", ["apple", "banana"]) is False
    
    def test_existence_operator_parity(self):
        """Test that existence operators work identically."""
        evaluator = ConditionEvaluator()
        
        # Exists
        assert evaluator.OPERATORS["exists"]("value", None) is True
        assert evaluator.OPERATORS["exists"]("", None) is False
        assert evaluator.OPERATORS["exists"](None, None) is False
        
        # Not exists
        assert evaluator.OPERATORS["not_exists"](None, None) is True
        assert evaluator.OPERATORS["not_exists"]("", None) is True
        assert evaluator.OPERATORS["not_exists"]("value", None) is False
        
        # Is empty
        assert evaluator.OPERATORS["is_empty"]("", None) is True
        assert evaluator.OPERATORS["is_empty"](0, None) is True
        assert evaluator.OPERATORS["is_empty"](False, None) is True
        assert evaluator.OPERATORS["is_empty"]("value", None) is False
        
        # Is not empty
        assert evaluator.OPERATORS["is_not_empty"]("value", None) is True
        assert evaluator.OPERATORS["is_not_empty"](1, None) is True
        assert evaluator.OPERATORS["is_not_empty"](True, None) is True
        assert evaluator.OPERATORS["is_not_empty"]("", None) is False


class TestPerformanceAndComplexity:
    """Test performance with large condition sets and complex scenarios."""
    
    def test_large_condition_set_performance(self):
        """Test performance with large number of conditions."""
        evaluator = ConditionEvaluator()
        
        # Create large form data
        large_form_data = {f"field_{i}": f"value_{i}" for i in range(1000)}
        
        # Create complex nested condition
        conditions = []
        for i in range(100):
            conditions.append({
                "operator": "equals",
                "field": f"field_{i}",
                "value": f"value_{i}"
            })
        
        complex_condition = {
            "operator": "and",
            "conditions": conditions
        }
        
        # This should complete without timeout
        import time
        start_time = time.time()
        result = evaluator.evaluate_condition(complex_condition, large_form_data)
        end_time = time.time()
        
        assert result is True
        assert end_time - start_time < 1.0  # Should complete in under 1 second
    
    def test_deeply_nested_conditions(self):
        """Test deeply nested condition structures."""
        evaluator = ConditionEvaluator()
        form_data = {"a": 1, "b": 2, "c": 3}
        
        # Create deeply nested condition (10 levels)
        condition = {"operator": "equals", "field": "a", "value": 1}
        for i in range(10):
            condition = {
                "operator": "and",
                "conditions": [
                    condition,
                    {"operator": "equals", "field": "b", "value": 2}
                ]
            }
        
        result = evaluator.evaluate_condition(condition, form_data)
        assert result is True
    
    def test_complex_real_world_scenario(self):
        """Test complex real-world conditional logic scenario."""
        evaluator = ConditionEvaluator()
        
        # Simulate complex product configuration conditions
        form_data = {
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "sliding",
            "width": 48.5,
            "height": 60.0,
            "builtin_flyscreen_track": True,
            "system_series": "Kom800",
            "renovation": True
        }
        
        # Complex condition: Show flyscreen fields if Frame + sliding + builtin track
        condition = {
            "operator": "and",
            "conditions": [
                {"operator": "equals", "field": "type", "value": "Frame"},
                {
                    "operator": "or",
                    "conditions": [
                        {"operator": "contains", "field": "opening_system", "value": "sliding"},
                        {"operator": "equals", "field": "system_series", "value": "Kom800"}
                    ]
                },
                {"operator": "equals", "field": "builtin_flyscreen_track", "value": True},
                {
                    "operator": "and",
                    "conditions": [
                        {"operator": "greater_than", "field": "width", "value": 40},
                        {"operator": "greater_than", "field": "height", "value": 50}
                    ]
                }
            ]
        }
        
        result = evaluator.evaluate_condition(condition, form_data)
        assert result is True
        
        # Change one condition to make it false
        form_data["builtin_flyscreen_track"] = False
        result = evaluator.evaluate_condition(condition, form_data)
        assert result is False