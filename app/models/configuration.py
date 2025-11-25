"""Configuration model for customer product designs.

This module defines the Configuration ORM model for individual customer
product configurations using SQLAlchemy 2.0 with Mapped columns.

Public Classes:
    Configuration: Customer product design model

Features:
    - Status tracking (draft, saved, quoted, ordered)
    - Calculated fields (total_price, calculated_weight, calculated_technical_data)
    - Reference code for easy identification
    - JSONB for flexible technical specifications
    - Relationships with manufacturing types, customers, and selections
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.attribute_node import AttributeNode
    from app.models.configuration_selection import ConfigurationSelection
    from app.models.manufacturing_type import ManufacturingType

__all__ = ["Configuration"]


class Configuration(Base):
    """Configuration model for customer product designs.

    Represents individual product designs created by customers.
    Each configuration is a unique product instance with specific
    attribute selections and calculated totals.

    Attributes:
        id: Primary key
        manufacturing_type_id: Foreign key to ManufacturingType
        customer_id: Optional foreign key to Customer (future)
        name: Configuration name
        description: Customer notes
        status: Current state (draft, saved, quoted, ordered)
        reference_code: Unique identifier for easy reference
        base_price: Base price from manufacturing type
        total_price: Final calculated price including options
        calculated_weight: Total weight in kg
        calculated_technical_data: Product-specific technical specs (JSONB)
        created_at: Record creation timestamp
        updated_at: Last update timestamp
        manufacturing_type: Related manufacturing type
        selections: Related configuration selections
    """

    __tablename__ = "configurations"

    # Primary key
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True,
        sort_order=-100,
        doc="Primary key identifier",
    )

    # Foreign keys
    manufacturing_type_id: Mapped[int] = mapped_column(
        ForeignKey("manufacturing_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Manufacturing type ID",
    )
    customer_id: Mapped[int | None] = mapped_column(
        # ForeignKey("customers.id", ondelete="SET NULL"),  # Future: when Customer model exists
        nullable=True,
        index=True,
        doc="Customer ID (optional)",
    )

    # Basic information
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Configuration name",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Customer notes and description",
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        index=True,
        doc="Current state: draft, saved, quoted, ordered",
    )

    # Reference code for easy identification
    reference_code: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        doc="Unique identifier for easy reference",
    )

    # Calculated properties (updated by triggers or application)
    base_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Base price from manufacturing type",
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
        index=True,
        doc="Final calculated price including all options",
    )
    calculated_weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Total weight in kg",
    )
    calculated_technical_data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        server_default="{}",
        doc="Product-specific technical specifications (JSONB)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Record creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
        doc="Last update timestamp (UTC)",
    )

    # Relationships
    manufacturing_type: Mapped["ManufacturingType"] = relationship(
        "ManufacturingType",
        back_populates="configurations",
    )
    selections: Mapped[list["ConfigurationSelection"]] = relationship(
        "ConfigurationSelection",
        back_populates="configuration",
        cascade="all, delete-orphan",
        doc="Related configuration selections",
    )

    # Indexes
    __table_args__ = (
        # Composite index for filtering by manufacturing type and status
        Index(
            "idx_configurations_mfg_type_status",
            "manufacturing_type_id",
            "status",
        ),
        # Composite index for filtering by customer and status
        Index(
            "idx_configurations_customer_status",
            "customer_id",
            "status",
        ),
        # GIN index on calculated_technical_data for JSONB queries
        Index(
            "idx_configurations_technical_data",
            "calculated_technical_data",
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        """String representation of Configuration.

        Returns:
            str: Configuration representation with ID and name
        """
        return (
            f"<Configuration(id={self.id}, name='{self.name}', "
            f"status='{self.status}', total_price={self.total_price})>"
        )
