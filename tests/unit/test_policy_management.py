"""Unit tests for policy management functionality.

This module tests policy management operations including:
- Dynamic customer assignment to salesmen
- Policy addition and removal
- Policy backup and restore
- Privilege object creation and management

Requirements: 6.1, 6.2, 6.3, 9.3
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import PolicyEvaluationException
from app.core.rbac import Role, Permission, Privilege
from app.models.customer import Customer
from app.models.user import User
from app.services.policy_manager import PolicyManager


class TestPolicyManager:
    """Test PolicyManager functionality."""
    
    @pytest.fixture
    def policy_manager(self, mock_db):
        """Create PolicyManager with mocked database."""
        with patch('casbin.Enforcer'):
            manager = PolicyManager(mock_db)
            manager.enforcer = MagicMock()
            manager.enforcer.enable_auto_save = MagicMock()
            return manager
    
    @pytest.fixture
    def customer(self):
        """Create test customer."""
        customer = Customer()
        customer.id = 123
        customer.email = "customer@example.com"
        customer.company_name = "Test Company"
        customer.contact_person = "John Doe"
        return customer
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        user = User()
        user.id = 1
        user.email = "salesman@example.com"
        user.username = "salesman"
        user.role = Role.SALESMAN.value
        return user


class TestPolicyAdditionAndRemoval(TestPolicyManager):
    """Test policy addition and removal operations."""
    
    @pytest.mark.asyncio
    async def test_add_policy_success(self, policy_manager):
        """Test successful policy addition."""
        # Mock enforcer to return True (policy added)
        policy_manager.enforcer.add_policy.return_value = True
        policy_manager._log_policy_change = AsyncMock()
        
        result = await policy_manager.add_policy(
            subject="test_role",
            resource="configuration",
            action="read",
            effect="allow"
        )
        
        assert result is True
        
        # Verify enforcer was called correctly
        policy_manager.enforcer.add_policy.assert_called_once_with(
            "test_role", "configuration", "read", "allow"
        )
        
        # Verify audit logging
        policy_manager._log_policy_change.assert_called_once_with(
            action_type="add_policy",
            policy_data={
                "subject": "test_role",
                "resource": "configuration", 
                "action": "read",
                "effect": "allow"
        