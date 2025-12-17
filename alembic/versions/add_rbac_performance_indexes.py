"""Add RBAC performance indexes

Revision ID: add_rbac_performance_indexes
Revises: d7882101cf73
Create Date: 2024-12-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_rbac_performance_indexes'
down_revision = 'd7882101cf73'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for RBAC operations."""
    
    # Index for customers.email lookup (used in customer auto-creation)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_customers_email 
        ON customers (email)
    """)
    
    # Index for users.role filtering (used in RBAC queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_role 
        ON users (role)
    """)
    
    # Composite index for configurations by customer_id and status
    # (used in filtered configuration queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_configurations_customer_status 
        ON configurations (customer_id, status)
    """)
    
    # Index for quotes by customer_id (used in filtered quote queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_quotes_customer_id 
        ON quotes (customer_id)
    """)
    
    # Index for orders by quote_id (used in order-quote relationships)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_quote_id 
        ON orders (quote_id)
    """)
    
    # Index for configuration_selections by configuration_id
    # (used in configuration detail queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_configuration_selections_config_id 
        ON configuration_selections (configuration_id)
    """)
    
    # Index for sessions by user_id (used in user session queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
        ON sessions (user_id)
    """)
    
    # Index for sessions by is_active (used in active session queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_is_active 
        ON sessions (is_active)
    """)


def downgrade():
    """Remove performance indexes for RBAC operations."""
    
    # Remove all indexes in reverse order
    op.drop_index('idx_sessions_is_active', table_name='sessions')
    op.drop_index('idx_sessions_user_id', table_name='sessions')
    op.drop_index('idx_configuration_selections_config_id', table_name='configuration_selections')
    op.drop_index('idx_orders_quote_id', table_name='orders')
    op.drop_index('idx_quotes_customer_id', table_name='quotes')
    op.drop_index('idx_configurations_customer_status', table_name='configurations')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_customers_email', table_name='customers')