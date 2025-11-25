"""Database models module.

This module contains all SQLAlchemy ORM models for database tables
using modern SQLAlchemy 2.0 with Mapped columns.

Public Classes:
    User: User model for authentication
    Session: Session model for tracking user sessions
    ManufacturingType: Product category model for Windx configurator
    AttributeNode: Hierarchical attribute tree node for product configuration
    Configuration: Customer product design model
    ConfigurationSelection: Individual attribute selection model

Features:
    - SQLAlchemy 2.0 Mapped columns
    - Relationship management
    - Automatic timestamps
    - Type-safe model definitions
"""

from app.models.attribute_node import AttributeNode
from app.models.configuration import Configuration
from app.models.configuration_selection import ConfigurationSelection
from app.models.manufacturing_type import ManufacturingType
from app.models.session import Session
from app.models.user import User

__all__ = [
    "User",
    "Session",
    "ManufacturingType",
    "AttributeNode",
    "Configuration",
    "ConfigurationSelection",
]
