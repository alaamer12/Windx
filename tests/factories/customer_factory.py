"""Customer factory for test data generation.

This module provides factory functions for creating customer test data
with realistic values and proper validation.

Public Functions:
    create_customer_data: Create customer data dictionary
    create_customer_create_schema: Create CustomerCreate schema
    create_multiple_customers_data: Create multiple customer data dictionaries

Features:
    - Realistic test data
    - Unique values per call
    - Customizable fields
    - Factory traits (residential, inactive, contractor)
    - Proper validation
"""

from __future__ import annotations

from typing import Any

from app.schemas.customer import CustomerCreate

__all__ = [
    "create_customer_data",
    "create_customer_create_schema",
    "create_multiple_customers_data",
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


def create_customer_data(
    company_name: str | None = None,
    contact_person: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: dict | None = None,
    customer_type: str = "commercial",
    tax_id: str | None = None,
    payment_terms: str | None = None,
    is_active: bool = True,
    notes: str | None = None,
    # Factory traits
    residential: bool = False,
    inactive: bool = False,
    contractor: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create customer data dictionary.

    Args:
        company_name (str | None): Company name (auto-generated if None)
        contact_person (str | None): Contact name (auto-generated if None)
        email (str | None): Email (auto-generated if None)
        phone (str | None): Phone number (auto-generated if None)
        address (dict | None): Address dictionary (auto-generated if None)
        customer_type (str): Customer type (commercial, residential, contractor)
        tax_id (str | None): Tax ID (auto-generated if None)
        payment_terms (str | None): Payment terms (default based on type)
        is_active (bool): Active status
        notes (str | None): Internal notes
        residential (bool): Apply residential trait
        inactive (bool): Apply inactive trait
        contractor (bool): Apply contractor trait
        **kwargs: Additional fields

    Returns:
        dict[str, Any]: Customer data dictionary

    Examples:
        >>> # Standard commercial customer
        >>> data = create_customer_data()
        
        >>> # Residential customer (trait)
        >>> data = create_customer_data(residential=True)
        
        >>> # Inactive contractor (multiple traits)
        >>> data = create_customer_data(contractor=True, inactive=True)
    """
    unique_id = _get_unique_id()

    # Apply traits
    if residential:
        customer_type = "residential"
        company_name = None  # Residential customers typically don't have company names
        payment_terms = payment_terms or "net_30"
    elif contractor:
        customer_type = "contractor"
        payment_terms = payment_terms or "net_15"
    else:
        # Default commercial
        payment_terms = payment_terms or "net_30"

    if inactive:
        is_active = False

    # Generate default values
    if company_name is None and customer_type != "residential":
        company_name = f"Test Company {unique_id}"
    
    if contact_person is None:
        contact_person = f"Contact Person {unique_id}"
    
    if email is None:
        email = f"customer{unique_id}@example.com"
    
    if phone is None:
        phone = f"555-{unique_id:04d}"
    
    if address is None:
        address = {
            "street": f"{unique_id} Test Street",
            "city": "Test City",
            "state": "TS",
            "zip": f"{unique_id:05d}",
            "country": "USA",
        }
    
    if tax_id is None and customer_type != "residential":
        tax_id = f"{unique_id:02d}-{unique_id:07d}"

    data = {
        "company_name": company_name,
        "contact_person": contact_person,
        "email": email,
        "phone": phone,
        "address": address,
        "customer_type": customer_type,
        "tax_id": tax_id,
        "payment_terms": payment_terms,
        "is_active": is_active,
        "notes": notes,
    }

    data.update(kwargs)
    return data


def create_customer_create_schema(
    company_name: str | None = None,
    contact_person: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: dict | None = None,
    customer_type: str = "commercial",
    tax_id: str | None = None,
    payment_terms: str | None = None,
    notes: str | None = None,
    # Factory traits
    residential: bool = False,
    contractor: bool = False,
    **kwargs: Any,
) -> CustomerCreate:
    """Create CustomerCreate schema.

    Args:
        company_name (str | None): Company name (auto-generated if None)
        contact_person (str | None): Contact name (auto-generated if None)
        email (str | None): Email (auto-generated if None)
        phone (str | None): Phone number (auto-generated if None)
        address (dict | None): Address dictionary (auto-generated if None)
        customer_type (str): Customer type (commercial, residential, contractor)
        tax_id (str | None): Tax ID (auto-generated if None)
        payment_terms (str | None): Payment terms (default based on type)
        notes (str | None): Internal notes
        residential (bool): Apply residential trait
        contractor (bool): Apply contractor trait
        **kwargs: Additional fields

    Returns:
        CustomerCreate: Customer creation schema

    Examples:
        >>> # Standard commercial customer
        >>> schema = create_customer_create_schema()
        
        >>> # Residential customer
        >>> schema = create_customer_create_schema(residential=True)
        
        >>> # Contractor with custom payment terms
        >>> schema = create_customer_create_schema(
        ...     contractor=True,
        ...     payment_terms="net_10"
        ... )
    """
    data = create_customer_data(
        company_name=company_name,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address,
        customer_type=customer_type,
        tax_id=tax_id,
        payment_terms=payment_terms,
        notes=notes,
        residential=residential,
        contractor=contractor,
        **kwargs,
    )
    # Remove fields not in CustomerCreate
    data.pop("is_active", None)

    return CustomerCreate(**data)


def create_multiple_customers_data(
    count: int = 3,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Create multiple customer data dictionaries.

    Args:
        count (int): Number of customers to create
        **kwargs: Common fields for all customers

    Returns:
        list[dict[str, Any]]: List of customer data dictionaries

    Examples:
        >>> # Create 5 commercial customers
        >>> customers = create_multiple_customers_data(count=5)
        
        >>> # Create 3 residential customers
        >>> customers = create_multiple_customers_data(
        ...     count=3,
        ...     residential=True
        ... )
    """
    return [create_customer_data(**kwargs) for _ in range(count)]
