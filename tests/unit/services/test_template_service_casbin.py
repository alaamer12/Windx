"""Unit tests for Template Service with Casbin decorators.

This module contains unit tests for the Template Service with RBAC decorators,
customer relationships, and template usage tracking.

Tests cover:
- Template application with customer relationships
- Casbin decorator authorization on template operations
- Template usage tracking with proper customer associations
- Privilege object functionality

Requirements: 2.1, 2.2, 9.1, 9.3
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from app.models.user import User
from app.models.customer import Customer
from app.models.configuration import Configuration
from app.models.configuration_template import ConfigurationTemplate
from app.models.template_selection import TemplateSelection
from app.models.manufacturing_type import ManufacturingType
from app.services.template import TemplateService, TemplateManagement, TemplateReader, AdminTemplateAccess
from app.services.rbac import RBACService
from app.schemas.configuration_template import ConfigurationTemplateCreate
from app.schemas.configuration_selection import ConfigurationSelectionValue
from app.core.rbac import Role
from app.core.exceptions import NotFoundException, ValidationException
from fastapi import HTTPException


class TestTemplateServiceCasbin:
    """Unit tests for Template Service with Casbin decorators."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=Role.CUSTOMER.value,
            is_active=True,
            is_superuser=False
        )

    @pytest.fixture
    def sample_data_entry(self):
        """Create sample data entry user for testing."""
        return User(
            id=2,
            email="data@company.com",
            username="dataentry",
            full_name="Data Entry User",
            role=Role.DATA_ENTRY.value,
            is_active=True,
            is_superuser=False
        )

    @pytest.fixture
    def sample_salesman(self):
        """Create sample salesman user for testing."""
        return User(
            id=3,
            email="salesman@company.com",
            username="salesman",
            full_name="Sales Person",
            role=Role.SALESMAN.value,
            is_active=True,
            is_superuser=False
        )

    @pytest.fixture
    def sample_admin(self):
        """Create sample admin user for testing."""
        return User(
            id=4,
            email="admin@company.com",
            username="admin",
            full_name="Admin User",
            role=Role.SUPERADMIN.value,
            is_active=True,
            is_superuser=True
        )

    @pytest.fixture
    def sample_customer(self):
        """Create sample customer for testing."""
        return Customer(
            id=100,
            email="test@example.com",
            contact_person="Test User",
            customer_type="residential",
            is_active=True
        )

    @pytest.fixture
    def sample_manufacturing_type(self):
        """Create sample manufacturing type for testing."""
        return ManufacturingType(
            id=1,
            name="Test Window",
            base_price=Decimal("200.00"),
            base_weight=Decimal("15.00"),
            is_active=True
        )

    @pytest.fixture
    def sample_template(self, sample_manufacturing_type):
        """Create sample configuration template for testing."""
        return ConfigurationTemplate(
            id=1,
            name="Standard Window Template",
            description="Standard window configuration",
            manufacturing_type_id=sample_manufacturing_type.id,
            template_type="standard",
            is_public=True,
            estimated_price=Decimal("300.00"),
            estimated_weight=Decimal("20.00"),
            usage_count=5,
            success_rate=Decimal("85.50"),
            created_by=2,  # Data entry user
            is_active=True
        )

    @pytest.fixture
    def sample_template_selections(self, sample_template):
        """Create sample template selections for testing."""
        return [
            TemplateSelection(
                id=1,
                template_id=sample_template.id,
                attribute_node_id=10,
                string_value="Aluminum",
                selection_path="frame.material.aluminum"
            ),
            TemplateSelection(
                id=2,
                template_id=sample_template.id,
                attribute_node_id=11,
                string_value="Double Pane",
                selection_path="glass.pane_count.double"
            )
        ]

    @pytest.fixture
    def sample_configuration(self, sample_customer, sample_manufacturing_type):
        """Create sample configuration for testing."""
        return Configuration(
            id=1,
            manufacturing_type_id=sample_manufacturing_type.id,
            customer_id=sample_customer.id,
            name="Test Configuration from Template",
            status="draft",
            base_price=Decimal("200.00"),
            total_price=Decimal("300.00"),
            calculated_weight=Decimal("20.00")
        )

    @pytest.mark.asyncio
    async def test_apply_template_uses_proper_customer_relationship(self, mock_db, sample_user, sample_customer, sample_template, sample_template_selections):
        """Test that apply_template_to_configuration uses proper customer relationship."""
        # Setup
        template_service = TemplateService(mock_db)
        
        # Mock RBAC service
        mock_rbac_service = AsyncMock()
        mock_rbac_service.get_or_create_customer_for_user.return_value = sample_customer
        template_service.rbac_service = mock_rbac_service
        
        # Mock template repository
        template_service.template_repo.get = AsyncMock(return_value=sample_template)
        
        # Mock template selections
        template_service.template_selection_repo.get_by_template = AsyncMock(return_value=sample_template_selections)
        
        # Mock configuration service
        mock_config_service = AsyncMock()
        mock_config_service.create_configuration = AsyncMock(return_value=sample_configuration)
        mock_config_service.add_selection = AsyncMock()
        mock_config_service.calculate_totals = AsyncMock()
        template_service.config_service = mock_config_service
        
        # Mock template usage tracking
        template_service.track_template_usage = AsyncMock()
        
        # Execute
        result = await template_service.apply_template_to_configuration(
            template_id=1,
            user=sample_user,
            config_name="Custom Configuration"
        )
        
        # Verify customer relationship used
        mock_rbac_service.get_or_create_customer_for_user.assert_called_once_with(sample_user)
        
        # Verify configuration created with proper customer ID
        mock_config_service.create_configuration.assert_called_once()
        config_data = mock_config_service.create_configuration.call_args[0][0]
        assert config_data.customer_id == sample_customer.id
        assert config_data.customer_id != sample_user.id

    @pytest.mark.asyncio
    async def test_apply_template_casbin_decorator_authorization(self, mock_db, sample_user, sample_template):
        """Test Casbin decorator authorization on apply_template_to_configuration."""
        # Setup
        template_service = TemplateService(mock_db)
        template_service.template_repo.get = AsyncMock(return_value=sample_template)
        
        # Mock Casbin decorator to allow access
        with patch('app.core.rbac.require') as mock_require:
            mock_decorator = MagicMock()
            mock_decorator.return_value = lambda func: func  # Pass through
            mock_require.return_value = mock_decorator
            
            # Mock other dependencies to prevent actual execution
            template_service.template_selection_repo.get_by_template = AsyncMock(return_value=[])
            template_service.rbac_service = AsyncMock()
            template_service.config_service = AsyncMock()
            template_service.track_template_usage = AsyncMock()
            
            # Execute
            await template_service.apply_template_to_configuration(
                template_id=1,
                user=sample_user
            )
            
            # Verify decorator was applied
            mock_require.assert_called()

    @pytest.mark.asyncio
    async def test_template_usage_tracking_with_proper_customer_associations(self, mock_db, sample_user, sample_customer, sample_template, sample_configuration):
        """Test template usage tracking with proper customer associations."""
        # Setup
        template_service = TemplateService(mock_db)
        template_service.template_repo.get = AsyncMock(return_value=sample_template)
        
        # Execute
        await template_service.track_template_usage(
            template_id=1,
            config_id=sample_configuration.id,
            customer_id=sample_customer.id
        )
        
        # Verify usage count incremented
        assert sample_template.usage_count == 6  # Was 5, now 6
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_template)

    @pytest.mark.asyncio
    async def test_get_template_multiple_decorators_or_logic(self, mock_db, sample_user, sample_data_entry, sample_admin, sample_template):
        """Test get_template with multiple @require decorators (OR logic)."""
        # Setup
        template_service = TemplateService(mock_db)
        template_service.template_repo.get = AsyncMock(return_value=sample_template)
        
        # Mock Casbin decorators to simulate OR logic
        with patch('app.core.rbac.require') as mock_require:
            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        user = args[2] if len(args) > 2 else kwargs.get('user')
                        
                        # Simulate different authorization rules
                        if requirement == TemplateReader:
                            # All authenticated users can read public templates
                            if sample_template.is_public:
                                return await func(*args, **kwargs)
                        elif requirement == AdminTemplateAccess:
                            # Admins can read any template
                            if user.role == Role.SUPERADMIN.value:
                                return await func(*args, **kwargs)
                        
                        raise HTTPException(status_code=403, detail="Access denied")
                    return wrapper
                return decorator
            
            mock_require.side_effect = mock_decorator_factory
            
            # Test 1: Regular user can read public template
            result = await template_service.get_template(1, sample_user)
            assert result == sample_template
            
            # Test 2: Data entry user can read public template
            result = await template_service.get_template(1, sample_data_entry)
            assert result == sample_template
            
            # Test 3: Admin can read any template
            result = await template_service.get_template(1, sample_admin)
            assert result == sample_template

    @pytest.mark.asyncio
    async def test_create_template_casbin_authorization(self, mock_db, sample_data_entry, sample_salesman, sample_manufacturing_type):
        """Test create_template with Casbin authorization for data entry and salesman roles."""
        # Setup
        template_service = TemplateService(mock_db)
        
        # Mock manufacturing type repository
        from app.repositories.manufacturing_type import ManufacturingTypeRepository
        with patch.object(ManufacturingTypeRepository, 'get') as mock_mfg_get:
            mock_mfg_get.return_value = sample_manufacturing_type
            
            # Mock template creation
            template_service.template_repo.db.add = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            # Mock Casbin decorator to allow access for data entry
            with patch('app.core.rbac.require') as mock_require:
                def mock_decorator_factory(requirement):
                    def decorator(func):
                        async def wrapper(*args, **kwargs):
                            user = args[2] if len(args) > 2 else kwargs.get('user')
                            
                            # Simulate authorization rules
                            if requirement == TemplateManagement:
                                # Data entry and salesman can create templates
                                if user.role in [Role.DATA_ENTRY.value, Role.SALESMAN.value]:
                                    return await func(*args, **kwargs)
                            elif requirement == AdminTemplateAccess:
                                # Admins can create templates
                                if user.role == Role.SUPERADMIN.value:
                                    return await func(*args, **kwargs)
                            
                            raise HTTPException(status_code=403, detail="Access denied")
                        return wrapper
                    return decorator
                
                mock_require.side_effect = mock_decorator_factory
                
                # Test data entry user can create template
                template_data = ConfigurationTemplateCreate(
                    name="New Template",
                    manufacturing_type_id=1,
                    template_type="standard"
                )
                
                result = await template_service.create_template(template_data, sample_data_entry)
                
                # Verify template creation
                template_service.template_repo.db.add.assert_called_once()
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_privilege_objects_functionality(self):
        """Test Privilege objects functionality for Template Service."""
        # Test TemplateManagement privilege
        assert Role.DATA_ENTRY in TemplateManagement.roles
        assert Role.SALESMAN in TemplateManagement.roles
        assert TemplateManagement.permission.resource == "template"
        assert TemplateManagement.permission.action == "create"
        
        # Test TemplateReader privilege
        assert Role.CUSTOMER in TemplateReader.roles
        assert Role.SALESMAN in TemplateReader.roles
        assert Role.PARTNER in TemplateReader.roles
        assert Role.DATA_ENTRY in TemplateReader.roles
        assert TemplateReader.permission.resource == "template"
        assert TemplateReader.permission.action == "read"
        
        # Test AdminTemplateAccess privilege
        assert Role.SUPERADMIN in AdminTemplateAccess.roles
        assert AdminTemplateAccess.permission.resource == "*"
        assert AdminTemplateAccess.permission.action == "*"

    @pytest.mark.asyncio
    async def test_template_application_with_selections_and_customer_tracking(self, mock_db, sample_user, sample_customer, sample_template, sample_template_selections, sample_configuration):
        """Test complete template application with selections and customer tracking."""
        # Setup
        template_service = TemplateService(mock_db)
        
        # Mock RBAC service
        mock_rbac_service = AsyncMock()
        mock_rbac_service.get_or_create_customer_for_user.return_value = sample_customer
        template_service.rbac_service = mock_rbac_service
        
        # Mock template repository
        template_service.template_repo.get = AsyncMock(return_value=sample_template)
        template_service.template_selection_repo.get_by_template = AsyncMock(return_value=sample_template_selections)
        
        # Mock configuration service
        mock_config_service = AsyncMock()
        mock_config_service.create_configuration = AsyncMock(return_value=sample_configuration)
        mock_config_service.add_selection = AsyncMock()
        mock_config_service.calculate_totals = AsyncMock()
        template_service.config_service = mock_config_service
        
        # Mock template usage tracking
        template_service.track_template_usage = AsyncMock()
        
        # Execute
        result = await template_service.apply_template_to_configuration(
            template_id=1,
            user=sample_user,
            config_name="Applied Template Configuration"
        )
        
        # Verify all selections were applied
        assert mock_config_service.add_selection.call_count == len(sample_template_selections)
        
        # Verify totals were recalculated
        mock_config_service.calculate_totals.assert_called_once_with(sample_configuration.id)
        
        # Verify usage tracking with proper customer ID
        template_service.track_template_usage.assert_called_once_with(
            1, sample_configuration.id, sample_customer.id
        )

    @pytest.mark.asyncio
    async def test_template_not_found_error_handling(self, mock_db, sample_user):
        """Test error handling when template is not found."""
        # Setup
        template_service = TemplateService(mock_db)
        template_service.template_repo.get = AsyncMock(return_value=None)
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await template_service.get_template(999, sample_user)
        
        assert "ConfigurationTemplate" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_template_not_active_validation(self, mock_db, sample_user, sample_template):
        """Test validation that template must be active to apply."""
        # Setup
        template_service = TemplateService(mock_db)
        
        # Mock inactive template
        sample_template.is_active = False
        template_service.template_repo.get = AsyncMock(return_value=sample_template)
        
        # Execute and verify exception
        with pytest.raises(ValidationException) as exc_info:
            await template_service.apply_template_to_configuration(
                template_id=1,
                user=sample_user
            )
        
        assert "Template is not active" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manufacturing_type_not_found_in_create_template(self, mock_db, sample_data_entry):
        """Test error handling when manufacturing type is not found during template creation."""
        # Setup
        template_service = TemplateService(mock_db)
        
        # Mock manufacturing type repository
        from app.repositories.manufacturing_type import ManufacturingTypeRepository
        with patch.object(ManufacturingTypeRepository, 'get') as mock_mfg_get:
            mock_mfg_get.return_value = None
            
            template_data = ConfigurationTemplateCreate(
                name="New Template",
                manufacturing_type_id=999,
                template_type="standard"
            )
            
            # Execute and verify exception
            with pytest.raises(NotFoundException) as exc_info:
                await template_service.create_template(template_data, sample_data_entry)
            
            assert "ManufacturingType" in str(exc_info.value)