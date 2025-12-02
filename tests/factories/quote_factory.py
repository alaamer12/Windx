"""Quote factory for test data generation.

This module provides factory functions for creating quote test data
with realistic values and proper validation.

Public Functions:
    create_quote_data: Create quote data dictionary
    create_multiple_quotes_data: Create multiple quote data dictionaries

Features:
    - Realistic test data
    - Unique values per call
    - Customizable fields
    - Proper validation
    - Automatic quote number generation
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

__all__ = [
    "create_quote_data",
    "create_multiple_quotes_data",
]

_counter = 0


def _get_unique_id() -> int:
    """Get unique ID for test data.

    Returns:
        int: Unique counter value
    """
    global _counter
    _counter += 1
    return _counter


def create_quote_data(
    configuration_id: int | None = None,
    customer_id: int | None = None,
    quote_number: str | None = None,
    subtotal: Decimal | None = None,
    tax_rate: Decimal | None = None,
    tax_amount: Decimal | None = None,
    discount_amount: Decimal | None = None,
    total_amount: Decimal | None = None,
    technical_requirements: dict | None = None,
    valid_until: date | None = None,
    status: str = "draft",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create quote data dictionary.

    Args:
        configuration_id (int | None): Configuration ID (required for actual creation)
        customer_id (int | None): Customer ID (optional)
        quote_number (str | None): Quote number (auto-generated if None)
        subtotal (Decimal | None): Subtotal (default: 500.00)
        tax_rate (Decimal | None): Tax rate percentage (default: 8.50)
        tax_amount (Decimal | None): Tax amount (auto-calculated if None)
        discount_amount (Decimal | None): Discount amount (default: 0.00)
        total_amount (Decimal | None): Total amount (auto-calculated if None)
        technical_requirements (dict | None): Technical requirements
        valid_until (date | None): Expiration date (default: 30 days from now)
        status (str): Quote status (draft, sent, accepted, expired)
        **kwargs: Additional fields

    Returns:
        dict[str, Any]: Quote data dictionary

    Examples:
        >>> # Standard quote
        >>> data = create_quote_data(configuration_id=1)
        
        >>> # Quote with custom pricing
        >>> data = create_quote_data(
        ...     configuration_id=1,
        ...     subtotal=Decimal("1000.00"),
        ...     tax_rate=Decimal("10.00")
        ... )
    """
    unique_id = _get_unique_id()

    # Generate default values
    if quote_number is None:
        today = date.today()
        quote_number = f"Q-{today.strftime('%Y%m%d')}-{unique_id:03d}"
    
    if subtotal is None:
        subtotal = Decimal("500.00")
    
    if tax_rate is None:
        tax_rate = Decimal("8.50")
    
    if tax_amount is None:
        tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    
    if discount_amount is None:
        discount_amount = Decimal("0.00")
    
    if total_amount is None:
        total_amount = (subtotal + tax_amount - discount_amount).quantize(Decimal("0.01"))
    
    if valid_until is None:
        valid_until = date.today() + timedelta(days=30)

    data = {
        "configuration_id": configuration_id,
        "customer_id": customer_id,
        "quote_number": quote_number,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
        "technical_requirements": technical_requirements,
        "valid_until": valid_until,
        "status": status,
    }

    data.update(kwargs)
    return data


def create_multiple_quotes_data(
    count: int = 3,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Create multiple quote data dictionaries.

    Args:
        count (int): Number of quotes to create
        **kwargs: Common fields for all quotes

    Returns:
        list[dict[str, Any]]: List of quote data dictionaries

    Examples:
        >>> # Create 5 quotes
        >>> quotes = create_multiple_quotes_data(count=5, configuration_id=1)
    """
    return [create_quote_data(**kwargs) for _ in range(count)]
