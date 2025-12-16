"""RBAC service for Role-Based Access Control operations.

This module provides the RBAC service for managing authorization,
role assignments, and policy evaluation using Casbin.

Public Classes:
    RBACService: Service for RBAC operations

Features:
    - Casbin policy engine integration
    - User-Customer relationship management
    - Permission checking and caching
    - Resource ownership validation
    - Query filtering for data access control
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import casbin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.models.customer import Customer
from app.models.user import User
from app.services.base import BaseService

__all__ = ["RBACService"]

logger = logging.getLogger(__name__)


class RBACService(BaseService):
    """Service for RBAC operations using Casbin.
    
    Provides comprehensive authorization services including:
    - Policy-based access control with Casbin
    - User-Customer relationship management
    - Permission checking with caching
    - Resource ownership validation
    - Automatic query filtering
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize RBAC service.
        
        Args:
            db: Database session for operations
        """
        super().__init__(db)
        self.enforcer = casbin.Enforcer(
            "config/rbac_model.conf",
            "config/rbac_policy.csv"
        )
        self._permission_cache: Dict[str, bool] = {}
        self._customer_cache: Dict[int, List[int]] = {}
    
    async def check_permission(
        self, 
        user: User, 
        resource: str, 
        action: str, 
        context: Optional[Dict] = None
    ) -> bool:
        """Check if user has permission for action on resource.
        
        Args:
            user: User to check permissions for
            resource: Resource type (e.g., "configuration", "quote")
            action: Action type (e.g., "read", "create", "update", "delete")
            context: Optional context for advanced permissions
            
        Returns:
            True if user has permission, False otherwise
        """
        # Cache key for performance
        cache_key = f"{user.id}:{resource}:{action}"
        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]
        
        try:
            # Check Casbin policy using user email as subject
            result = self.enforcer.enforce(user.email, resource, action)
            
            # Cache result
            self._permission_cache[cache_key] = result
            
            logger.debug(
                f"Permission check: user={user.email}, resource={resource}, "
                f"action={action}, result={result}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    async def check_resource_ownership(
        self, 
        user: User, 
        resource_type: str, 
        resource_id: int
    ) -> bool:
        """Check if user owns or has access to the resource.
        
        Args:
            user: User to check ownership for
            resource_type: Type of resource (e.g., "configuration", "customer")
            resource_id: ID of the resource
            
        Returns:
            True if user owns or has access to resource, False otherwise
        """
        # Superadmin has access to everything
        if user.role == Role.SUPERADMIN.value:
            return True
        
        # Get accessible customers for user
        accessible_customers = await self.get_accessible_customers(user)
        
        # For customer resources, check direct access
        if resource_type == "customer":
            return resource_id in accessible_customers
        
        # For configuration resources, check through customer relationship
        if resource_type == "configuration":
            from app.models.configuration import Configuration
            stmt = select(Configuration.customer_id).where(Configuration.id == resource_id)
            result = await self.db.execute(stmt)
            customer_id = result.scalar_one_or_none()
            
            if customer_id is None:
                return False
            
            return customer_id in accessible_customers
        
        # For quote resources, check through customer relationship
        if resource_type == "quote":
            from app.models.quote import Quote
            stmt = select(Quote.customer_id).where(Quote.id == resource_id)
            result = await self.db.execute(stmt)
            customer_id = result.scalar_one_or_none()
            
            if customer_id is None:
                return False
            
            return customer_id in accessible_customers
        
        # For order resources, check through quote -> customer relationship
        if resource_type == "order":
            from app.models.order import Order
            from app.models.quote import Quote
            stmt = (
                select(Quote.customer_id)
                .select_from(Order)
                .join(Quote)
                .where(Order.id == resource_id)
            )
            result = await self.db.execute(stmt)
            customer_id = result.scalar_one_or_none()
            
            if customer_id is None:
                return False
            
            return customer_id in accessible_customers
        
        # Default: deny access for unknown resource types
        logger.warning(f"Unknown resource type for ownership check: {resource_type}")
        return False
    
    async def get_accessible_customers(self, user: User) -> List[int]:
        """Get list of customer IDs user can access.
        
        Args:
            user: User to get accessible customers for
            
        Returns:
            List of customer IDs user can access
        """
        # Cache for performance
        if user.id in self._customer_cache:
            return self._customer_cache[user.id]
        
        accessible = []
        
        # Superadmin has access to all customers
        if user.role == Role.SUPERADMIN.value:
            stmt = select(Customer.id)
            result = await self.db.execute(stmt)
            accessible = [row[0] for row in result.fetchall()]
        else:
            # Regular users have access to their associated customer(s)
            # Find customer by email match (auto-creation pattern)
            stmt = select(Customer.id).where(Customer.email == user.email)
            result = await self.db.execute(stmt)
            customer_id = result.scalar_one_or_none()
            
            if customer_id:
                accessible = [customer_id]
        
        # Cache result
        self._customer_cache[user.id] = accessible
        
        logger.debug(f"Accessible customers for {user.email}: {accessible}")
        return accessible
    
    async def get_or_create_customer_for_user(self, user: User) -> Customer:
        """Get existing customer or create one for the user.
        
        This implements the auto-creation pattern where users get associated
        customers automatically when they first create configurations.
        
        Args:
            user: User to get or create customer for
            
        Returns:
            Customer associated with the user
            
        Raises:
            DatabaseException: If customer creation fails
        """
        # First try to find existing customer by email
        customer = await self._find_customer_by_email(user.email)
        
        if customer:
            logger.debug(f"Found existing customer {customer.id} for user {user.email}")
            return customer
        
        # Create new customer from user data
        logger.info(f"Creating new customer for user {user.email}")
        customer = await self._create_customer_from_user(user)
        
        # Clear customer cache since we added a new customer
        self._customer_cache.clear()
        
        return customer
    
    async def _find_customer_by_email(self, email: str) -> Optional[Customer]:
        """Find existing customer by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Customer if found, None otherwise
        """
        stmt = select(Customer).where(Customer.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _create_customer_from_user(self, user: User) -> Customer:
        """Create new customer record from user data.
        
        Args:
            user: User to create customer from
            
        Returns:
            Newly created customer
            
        Raises:
            DatabaseException: If customer creation fails
        """
        try:
            # Create customer with user data
            customer_data = {
                "email": user.email,
                "contact_person": user.full_name or user.username,
                "customer_type": "residential",  # Default for entry page users
                "is_active": True,
                "notes": f"Auto-created from user: {user.username}",
            }
            
            customer = Customer(**customer_data)
            self.db.add(customer)
            await self.commit()
            await self.refresh(customer)
            
            logger.info(f"Created customer {customer.id} for user {user.email}")
            return customer
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to create customer for user {user.email}: {e}")
            
            # Check if it was a race condition - another process created the customer
            customer = await self._find_customer_by_email(user.email)
            if customer:
                logger.info(f"Customer {customer.id} was created by another process")
                return customer
            
            # Re-raise the original exception
            from app.core.exceptions import DatabaseException
            raise DatabaseException(
                message="Failed to create customer record",
                details={"user_email": user.email, "error": str(e)}
            )
    
    async def assign_role_to_user(self, user: User, role: Role) -> None:
        """Assign role to user and update Casbin policies.
        
        Args:
            user: User to assign role to
            role: Role to assign
        """
        # Update user role in database
        user.role = role.value
        await self.commit()
        
        # Update Casbin role assignment
        # Remove existing role assignments
        self.enforcer.remove_grouping_policy(user.email)
        
        # Add new role assignment
        self.enforcer.add_grouping_policy(user.email, role.value)
        
        # Clear caches
        self.clear_cache()
        
        logger.info(f"Assigned role {role.value} to user {user.email}")
    
    async def assign_customer_to_user(self, user: User, customer_id: int) -> None:
        """Assign customer access to user (for salesmen/partners).
        
        Args:
            user: User to assign customer access to
            customer_id: Customer ID to grant access to
        """
        # Add customer assignment in Casbin
        # This uses the g2 grouping for customer assignments
        self.enforcer.add_grouping_policy(user.email, "customer", str(customer_id))
        
        # Clear customer cache
        if user.id in self._customer_cache:
            del self._customer_cache[user.id]
        
        logger.info(f"Assigned customer {customer_id} access to user {user.email}")
    
    def clear_cache(self) -> None:
        """Clear permission and customer caches."""
        self._permission_cache.clear()
        self._customer_cache.clear()
        logger.debug("Cleared RBAC caches")
    
    async def initialize_user_policies(self, user: User) -> None:
        """Initialize Casbin policies for a user.
        
        This should be called when a user is created or their role changes.
        
        Args:
            user: User to initialize policies for
        """
        # Add role assignment
        self.enforcer.add_grouping_policy(user.email, user.role)
        
        # For customers, assign them to their own customer record
        if user.role == Role.CUSTOMER.value:
            customer = await self.get_or_create_customer_for_user(user)
            self.enforcer.add_grouping_policy(user.email, "customer", str(customer.id))
        
        logger.info(f"Initialized policies for user {user.email} with role {user.role}")