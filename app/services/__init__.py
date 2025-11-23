"""Services layer for business logic.

This package contains service classes that implement business logic
and orchestrate operations between repositories.

Public Classes:
    UserService: User management business logic
    AuthService: Authentication and authorization logic
    SessionService: Session management logic
    DashboardService: Dashboard statistics and metrics

Features:
    - Business logic separation from data access
    - Transaction management
    - Complex operations orchestration
    - Validation and business rules
"""

from app.services.auth import AuthService
from app.services.dashboard import DashboardService
from app.services.session import SessionService
from app.services.user import UserService

__all__ = [
    "UserService",
    "AuthService",
    "SessionService",
    "DashboardService",
]
