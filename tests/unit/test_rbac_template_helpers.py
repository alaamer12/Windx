"""Unit tests for RBAC template helper classes.

Tests the Can, Has, and RBACHelper classes that provide RBAC functionality
in Jinja2 templates.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.rbac_template_helpers import Can, Has, RBACHelper
from app.models.user import User


class TestCanHelper:
    """Test suite for Can helper class."""
    
    def test_can_init(self):
        """Test Can helper initialization."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        can = Can(user)
        
        assert can.user == user
        assert can._rbac_service is None
    
    def test_can_call_valid_permission(self):
        """Test Can helper with valid permission string."""
        user = User(id=1, email="test@example.com", username="test", role="superadmin")
        can = Can(user)
        
        # Superadmin should have all permissions
        result = can('customer:read')
        assert result is True
        
        # Non-superadmin should not have permissions
        user_regular = User(id=2, email="user@example.com", username="user", role="customer")
        can_regular = Can(user_regular)
        result_regular = can_regular('customer:read')
        assert result_regular is False
    
    def test_can_call_invalid_format(self):
        """Test Can helper with invalid permission format."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        can = Can(user)
        
        # Invalid format (no colon)
        result = can('invalid_permission')
        
        assert result is False
    
    def test_can_call_permission_denied(self):
        """Test Can helper when permission is denied."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        can = Can(user)
        
        # Mock RBAC service to deny permission
        with patch('app.core.rbac_template_helpers.Can.rbac_service') as mock_service:
            async def mock_check():
                return False
            mock_service.check_permission.return_value = mock_check()
            
            result = can('customer:delete')
            
            assert result is False
    
    def test_can_create_shortcut(self):
        """Test Can.create() CRUD shortcut."""
        user = User(id=1, email="test@example.com", username="test", role="superadmin")
        can = Can(user)
        
        result = can.create('customer')
        assert result is True
    
    def test_can_read_shortcut(self):
        """Test Can.read() CRUD shortcut."""
        user = User(id=1, email="test@example.com", username="test", role="superadmin")
        can = Can(user)
        
        result = can.read('customer')
        assert result is True
    
    def test_can_update_shortcut(self):
        """Test Can.update() CRUD shortcut."""
        user = User(id=1, email="test@example.com", username="test", role="superadmin")
        can = Can(user)
        
        result = can.update('customer')
        assert result is True
    
    def test_can_delete_shortcut(self):
        """Test Can.delete() CRUD shortcut."""
        user = User(id=1, email="test@example.com", username="test", role="superadmin")
        can = Can(user)
        
        with patch('app.core.rbac_template_helpers.Can.rbac_service') as mock_service:
            async def mock_check():
                return True
            mock_service.check_permission.return_value = mock_check()
            
            result = can.delete('customer')
            
            assert result is True
    
    def test_can_access_resource(self):
        """Test Can.access() for resource ownership."""
        user = User(id=1, email="test@example.com", username="test", role="superadmin")
        can = Can(user)
        
        result = can.access('customer', 123)
        assert result is True
    
    def test_can_access_denied(self):
        """Test Can.access() when access is denied."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        can = Can(user)
        
        with patch('app.core.rbac_template_helpers.Can.rbac_service') as mock_service:
            async def mock_check():
                return False
            mock_service.check_resource_ownership.return_value = mock_check()
            
            result = can.access('customer', 999)
            
            assert result is False
    
    def test_can_error_handling(self):
        """Test Can helper error handling."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        can = Can(user)
        
        # Mock RBAC service to raise exception
        with patch('app.core.rbac_template_helpers.Can.rbac_service') as mock_service:
            async def mock_check():
                raise Exception("Test error")
            mock_service.check_permission.return_value = mock_check()
            
            result = can('customer:read')
            
            # Should fail safely and return False
            assert result is False


class TestHasHelper:
    """Test suite for Has helper class."""
    
    def test_has_init(self):
        """Test Has helper initialization."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        has = Has(user)
        
        assert has.user == user
    
    def test_has_role_exact_match(self):
        """Test Has.role() with exact role match."""
        user = User(id=1, email="test@example.com", username="test", role="salesman")
        has = Has(user)
        
        assert has.role('salesman') is True
        assert has.role('SALESMAN') is True  # Case insensitive
    
    def test_has_role_superadmin_bypass(self):
        """Test Has.role() with SUPERADMIN bypass."""
        user = User(id=1, email="admin@example.com", username="admin", role="superadmin")
        has = Has(user)
        
        # SUPERADMIN should pass all role checks
        assert has.role('customer') is True
        assert has.role('salesman') is True
        assert has.role('data_entry') is True
        assert has.role('partner') is True
    
    def test_has_role_no_match(self):
        """Test Has.role() with no role match."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        has = Has(user)
        
        assert has.role('salesman') is False
        assert has.role('superadmin') is False
    
    def test_has_any_role_single_match(self):
        """Test Has.any_role() with single role match."""
        user = User(id=1, email="test@example.com", username="test", role="salesman")
        has = Has(user)
        
        assert has.any_role('salesman', 'partner') is True
    
    def test_has_any_role_no_match(self):
        """Test Has.any_role() with no role match."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        has = Has(user)
        
        assert has.any_role('salesman', 'partner', 'data_entry') is False
    
    def test_has_any_role_superadmin(self):
        """Test Has.any_role() with SUPERADMIN."""
        user = User(id=1, email="admin@example.com", username="admin", role="superadmin")
        has = Has(user)
        
        assert has.any_role('customer', 'salesman') is True
    
    def test_has_admin_access_superadmin(self):
        """Test Has.admin_access() for SUPERADMIN."""
        user = User(id=1, email="admin@example.com", username="admin", role="superadmin")
        has = Has(user)
        
        assert has.admin_access() is True
    
    def test_has_admin_access_salesman(self):
        """Test Has.admin_access() for SALESMAN."""
        user = User(id=1, email="sales@example.com", username="sales", role="salesman")
        has = Has(user)
        
        assert has.admin_access() is True
    
    def test_has_admin_access_data_entry(self):
        """Test Has.admin_access() for DATA_ENTRY."""
        user = User(id=1, email="data@example.com", username="data", role="data_entry")
        has = Has(user)
        
        assert has.admin_access() is True
    
    def test_has_admin_access_customer(self):
        """Test Has.admin_access() for CUSTOMER."""
        user = User(id=1, email="customer@example.com", username="customer", role="customer")
        has = Has(user)
        
        assert has.admin_access() is False
    
    def test_has_customer_access_customer(self):
        """Test Has.customer_access() for CUSTOMER."""
        user = User(id=1, email="customer@example.com", username="customer", role="customer")
        has = Has(user)
        
        assert has.customer_access() is True
    
    def test_has_customer_access_salesman(self):
        """Test Has.customer_access() for SALESMAN."""
        user = User(id=1, email="sales@example.com", username="sales", role="salesman")
        has = Has(user)
        
        assert has.customer_access() is False
    
    def test_has_error_handling(self):
        """Test Has helper error handling."""
        # Create user with None role
        user = User(id=1, email="test@example.com", username="test", role=None)
        has = Has(user)
        
        # Should fail safely and return False
        result = has.role('salesman')
        assert result is False


class TestRBACHelper:
    """Test suite for RBACHelper class."""
    
    def test_rbac_helper_init(self):
        """Test RBACHelper initialization."""
        user = User(id=1, email="test@example.com", username="test", role="customer")
        rbac = RBACHelper(user)
        
        assert rbac.user == user
        assert isinstance(rbac.can, Can)
        assert isinstance(rbac.has, Has)
        assert rbac.can.user == user
        assert rbac.has.user == user
    
    def test_rbac_helper_can_access(self):
        """Test RBACHelper provides Can helper."""
        user = User(id=1, email="test@example.com", username="test", role="salesman")
        rbac = RBACHelper(user)
        
        # Can helper should be accessible
        assert rbac.can is not None
        assert isinstance(rbac.can, Can)
    
    def test_rbac_helper_has_access(self):
        """Test RBACHelper provides Has helper."""
        user = User(id=1, email="test@example.com", username="test", role="salesman")
        rbac = RBACHelper(user)
        
        # Has helper should be accessible
        assert rbac.has is not None
        assert isinstance(rbac.has, Has)
    
    def test_rbac_helper_integration(self):
        """Test RBACHelper integration with both helpers."""
        user = User(id=1, email="admin@example.com", username="admin", role="superadmin")
        rbac = RBACHelper(user)
        
        # Both helpers should work together
        assert rbac.has.role('superadmin') is True
        assert rbac.has.admin_access() is True
